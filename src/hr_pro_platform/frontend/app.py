"""Streamlit demo UI. All data comes from the FastAPI query boundary."""

from __future__ import annotations

from typing import Any

import streamlit as st

from hr_pro_platform.frontend.api_client import (
    ApiRequestError,
    ApiUnavailableError,
    get_health,
    get_statistics,
    search_people,
)
from hr_pro_platform.frontend.masking import (
    domain_completeness,
    mask_email,
    mask_ip,
    mask_passport,
    mask_phone,
)

st.set_page_config(page_title="HR Pro Explorer", layout="wide")
BASE_CSS = (
    "<style>.stApp{background-color:#0b1026;color:#e6f1ff}"
    '[data-testid="stMetricValue"]{color:#57e39a}'
    ".stButton>button{background:#16213f;color:#e6f1ff;border:1px solid #37c8c3}</style>"
)


def _safe_person(person: dict[str, Any]) -> dict[str, Any]:
    """Return only UI fields, masking sensitive values."""
    return {
        "Name": f"{person.get('first_name') or '—'} {person.get('last_name') or '—'}".strip(),
        "Sex": ", ".join(person["sex"]) if isinstance(person.get("sex"), list) else "—",
        "Passport": mask_passport(str(person["passport"])) if person.get("passport") else "—",
        "Email": mask_email(str(person["email"])) if person.get("email") else "—",
        "Phone": mask_phone(str(person["telephone_number"]))
        if person.get("telephone_number")
        else "—",
        "Locations": [
            {
                "Name": x.get("full_name") or "—",
                "City": x.get("city") or "—",
                "Address": x.get("address") or "—",
                "IP": mask_ip(str(x["ip_v4"])) if x.get("ip_v4") else "—",
            }
            for x in person.get("locations") or []
        ],
        "Professional profiles": [
            {
                "Name": x.get("full_name") or "—",
                "Company": x.get("company") or "—",
                "Job": x.get("job") or "—",
                "Company email": mask_email(str(x["company_email"]))
                if x.get("company_email")
                else "—",
                "Company phone": mask_phone(str(x["company_telephone_number"]))
                if x.get("company_telephone_number")
                else "—",
            }
            for x in person.get("professional_profiles") or []
        ],
    }


def _render_results(results: list[dict[str, Any]]) -> None:
    rows = []
    for person in results:
        location = next((x for x in person.get("locations") or [] if x.get("city")), {})
        profile = next((x for x in person.get("professional_profiles") or [] if x.get("job")), {})
        rows.append(
            {
                "ID": person.get("id"),
                "Name": f"{person.get('first_name') or '—'} {person.get('last_name') or '—'}",
                "City": location.get("city") or "—",
                "Job": profile.get("job") or "—",
                "Domains": f"{domain_completeness(person)}/4",
                "Passport": mask_passport(str(person["passport"]))
                if person.get("passport")
                else "—",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(results)} result(s)")


def _show_home() -> None:
    st.title("HR Pro Data Platform")
    st.caption("Read-only explorer over curated PostgreSQL data through FastAPI.")
    st.subheader("Records per table")
    try:
        stats = get_statistics()
    except (ApiUnavailableError, ApiRequestError):
        st.error("The API could not provide statistics.")
        return
    rows = stats.get("rows_per_table", {})
    for column, label, key in zip(
        st.columns(3),
        ("Employees", "Locations", "Professional profiles"),
        ("employees", "locations", "professional_profiles"),
        strict=True,
    ):
        column.metric(label, rows.get(key, "—"))
    st.subheader("Employees missing a domain")
    st.write(stats.get("employees_missing_domain", {}))


def _search_form() -> dict[str, Any] | None:
    with st.form("search_form", clear_on_submit=False):
        fields = {
            key: st.text_input(label, key=f"s_{key}")
            for key, label in (
                ("first_name", "First name"),
                ("last_name", "Last name"),
                ("passport", "Passport"),
                ("city", "City"),
                ("address", "Address"),
                ("job", "Job"),
                ("company", "Company"),
            )
        }
        st.slider("Results per page", 10, 100, 20, key="s_limit")
        if st.form_submit_button("Search"):
            filters = {key: value.strip() for key, value in fields.items()}
            st.session_state.pop("search_results", None)
            st.session_state.pop("selected_person", None)
            if not any(filters.values()):
                st.warning("Fill in at least one search field.")
                return None
            st.session_state["search_filters"] = filters
            st.session_state["search_page"] = 0
            return filters
    return st.session_state.get("search_filters")


def _show_people() -> None:
    filters = _search_form()
    if not filters:
        return
    page = int(st.session_state.get("search_page", 0))
    limit = int(st.session_state.get("s_limit", 20))
    try:
        results = search_people(
            **{key: value or None for key, value in filters.items()},
            limit=limit,
            offset=page * limit,
        )
    except (ApiUnavailableError, ApiRequestError):
        st.session_state.pop("search_results", None)
        st.session_state.pop("selected_person", None)
        st.error("The API could not process this search.")
        return
    st.session_state["search_results"] = results
    if not results:
        st.info("No people found matching the selected criteria.")
        return
    _render_results(results)
    options = [
        f"{p.get('id')} — {p.get('first_name') or ''} {p.get('last_name') or ''}" for p in results
    ]
    selected = st.selectbox("View details of...", options)
    if selected:
        st.session_state["selected_person"] = results[options.index(selected)]
        st.subheader(f"Person {st.session_state['selected_person'].get('id', '—')}")
        completeness = domain_completeness(st.session_state["selected_person"])
        st.write(f"Profile completeness: {completeness}/4 domains")
        st.json(_safe_person(st.session_state["selected_person"]), expanded=True)
    previous, page_label, next_page = st.columns(3)
    if previous.button("Anterior", disabled=page == 0):
        st.session_state["search_page"] = page - 1
        st.rerun()
    page_label.write(f"Página {page + 1}")
    if next_page.button("Siguiente", disabled=len(results) < limit):
        st.session_state["search_page"] = page + 1
        st.rerun()


def main() -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    try:
        api_ok = get_health().get("status") == "ok"
    except (ApiUnavailableError, ApiRequestError):
        api_ok = False
    if api_ok:
        st.success("API available")
    else:
        st.warning("API unavailable")
    home, people = st.tabs(["Home", "People"])
    with home:
        _show_home()
    with people:
        _show_people()


main()
