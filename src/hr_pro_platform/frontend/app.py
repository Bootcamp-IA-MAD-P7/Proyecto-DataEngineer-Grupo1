from __future__ import annotations

import streamlit as st

from .api_client import (
    ApiRequestError,
    ApiUnavailableError,
    get_health,
    get_statistics,
    search_all,
    search_by_location_profession,
    search_people,
)
from .masking import (
    domain_completeness,
    mask_email,
    mask_ip,
    mask_passport,
    mask_phone,
)

st.set_page_config(page_title="HR Pro Explorer", layout="wide")

BASE_CSS = """
<style>
.stApp { background-color: #0b1026; color: #e6f1ff; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3 { color: #e6f1ff; }
[data-testid="stTabs"] [data-baseweb="tab"] { color: #8fa3c2; }
[data-testid="stTabs"] [aria-selected="true"] [data-baseweb="tab"] {
    color: #e6f1ff !important;
    border-bottom: 2px solid #57e39a;
}
[data-testid="stMetricLabel"] { color: #8fa3c2; }
[data-testid="stMetricValue"] { color: #57e39a; }
.stButton > button {
    background: #16213f; color: #e6f1ff;
    border: 1px solid #37c8c3; border-radius: 6px;
}
.stButton > button:hover { border-color: #57e39a; }
[data-testid="stDataFrame"] { background: #111a33; }
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label { color: #8fa3c2; }
[data-testid="stExpander"] { background: #16213f; border-radius: 10px; }
.hr-card {
    background: #16213f; border-radius: 12px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem; color: #e6f1ff;
}
.hr-card .muted { color: #8fa3c2; font-size: 0.85rem; }
.hr-card .field-row { color: #e6f1ff; font-size: 0.9rem; line-height: 1.7; }
.hr-card .field-row strong { color: #e6f1ff; }
.aurora-line {
    background: linear-gradient(90deg, #57e39a, #37c8c3, #9b8cff, #c96bff);
    height: 3px; border-radius: 2px; margin: 0.4rem 0 1.2rem 0;
}
.pipeline-step {
    display: inline-block; padding: 0.4rem 0.8rem; border-radius: 6px;
    background: #16213f; border: 1px solid #8fa3c2; font-size: 0.9rem;
    color: #e6f1ff;
}
.pipeline-step.highlight {
    border: 2px solid #57e39a; font-weight: 700;
}
.pipeline-arrow {
    display: inline-block; margin: 0 0.4rem; color: #8fa3c2;
}
</style>
"""


def _render_search_results(results: list[dict]) -> None:
    rows = []
    for p in results:
        fn = p.get("first_name") or "—"
        ln = p.get("last_name") or "—"
        locs = p.get("locations") or []
        profs = p.get("professional_profiles") or []
        city_val = "—"
        for loc in locs:
            if loc.get("city"):
                city_val = str(loc["city"])
                break
        job_val = "—"
        for prof in profs:
            if prof.get("job"):
                job_val = str(prof["job"])
                break
        rows.append(
            {
                "ID": p.get("id"),
                "Name": f"{fn} {ln}" if fn != "—" or ln != "—" else "—",
                "City": city_val,
                "Job": job_val,
                "Domains": f"{domain_completeness(p)}/4",
                "Passport": mask_passport(str(p["passport"])) if p.get("passport") else "—",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(results)} result(s)")


def _render_person_detail(person: dict) -> None:
    pid = person.get("id")
    fn = person.get("first_name") or "—"
    ln = person.get("last_name") or "—"
    sex_raw = person.get("sex")
    sex = ", ".join(sex_raw) if isinstance(sex_raw, list) and sex_raw else "—"
    completeness = domain_completeness(person)

    st.markdown(
        f'<div class="hr-card">'
        f"<h3>{fn} {ln}</h3>"
        f'<div class="muted">Record id: {pid} — source: API / PostgreSQL</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    domains = [
        ("Identity", bool(person.get("first_name") and person.get("last_name"))),
        ("Contact", bool(person.get("email") or person.get("telephone_number"))),
        ("Location", bool(person.get("locations"))),
        ("Professional", bool(person.get("professional_profiles"))),
    ]
    domain_html = " ".join(
        f'<span style="color:{"#57e39a" if present else "#8fa3c2"}">'
        f"{'✓' if present else '✗'} {name}</span>"
        for name, present in domains
    )
    st.markdown(
        f'<div class="hr-card">'
        f"<strong>Profile completeness: {completeness}/4 domains</strong><br/>"
        f'<span style="font-size:0.9rem">{domain_html}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Personal data")
    st.markdown(
        f'<div class="hr-card">'
        f'<div class="field-row"><strong>Name:</strong> {fn}</div>'
        f'<div class="field-row"><strong>Last name:</strong> {ln}</div>'
        f'<div class="field-row"><strong>Sex:</strong> {sex}</div>'
        f'<div class="field-row"><strong>Passport:</strong> '
        f"{mask_passport(str(person['passport'])) if person.get('passport') else '—'}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Contact")
    email_val = mask_email(str(person["email"])) if person.get("email") else "—"
    tel_val = mask_phone(str(person["telephone_number"])) if person.get("telephone_number") else "—"
    st.markdown(
        f'<div class="hr-card">'
        f'<div class="field-row"><strong>Email:</strong> {email_val}</div>'
        f'<div class="field-row"><strong>Phone:</strong> {tel_val}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Location")
    locs = person.get("locations") or []
    if not locs:
        st.markdown(
            '<div class="hr-card"><div class="muted">—</div></div>',
            unsafe_allow_html=True,
        )
    for idx, loc in enumerate(locs, 1):
        loc_fn = loc.get("full_name") or "—"
        city = loc.get("city") or "—"
        addr = loc.get("address") or "—"
        ip = mask_ip(str(loc["ip_v4"])) if loc.get("ip_v4") else "—"
        st.markdown(
            f'<div class="hr-card">'
            f'<div class="field-row"><strong>Location {idx}</strong></div>'
            f'<div class="field-row"><strong>Name:</strong> {loc_fn}</div>'
            f'<div class="field-row"><strong>City:</strong> {city}</div>'
            f'<div class="field-row"><strong>Address:</strong> {addr}</div>'
            f'<div class="field-row"><strong>IP:</strong> {ip}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.subheader("Professional information")
    profs = person.get("professional_profiles") or []
    if not profs:
        st.markdown(
            '<div class="hr-card"><div class="muted">—</div></div>',
            unsafe_allow_html=True,
        )
    for idx, prof in enumerate(profs, 1):
        prof_fn = prof.get("full_name") or "—"
        company = prof.get("company") or "—"
        comp_addr = prof.get("company_address") or "—"
        job = prof.get("job") or "—"
        comp_email = mask_email(str(prof["company_email"])) if prof.get("company_email") else "—"
        comp_tel = (
            mask_phone(str(prof["company_telephone_number"]))
            if prof.get("company_telephone_number")
            else "—"
        )
        st.markdown(
            f'<div class="hr-card">'
            f'<div class="field-row"><strong>Profile {idx}</strong></div>'
            f'<div class="field-row"><strong>Name:</strong> {prof_fn}</div>'
            f'<div class="field-row"><strong>Company:</strong> {company}</div>'
            f'<div class="field-row"><strong>Company address:</strong> {comp_addr}</div>'
            f'<div class="field-row"><strong>Job:</strong> {job}</div>'
            f'<div class="field-row"><strong>Company email:</strong> {comp_email}</div>'
            f'<div class="field-row"><strong>Company phone:</strong> {comp_tel}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


def _tab_inicio() -> None:
    st.markdown(
        '<h2 style="color:#e6f1ff">HR Pro Data Platform</h2><div class="aurora-line"></div>',
        unsafe_allow_html=True,
    )

    steps = ["Kafka", "MongoDB", "ETL", "PostgreSQL", "API", "Frontend"]
    steps_html = ""
    for i, step in enumerate(steps):
        cls = "pipeline-step highlight" if step in ("API", "Frontend") else "pipeline-step"
        steps_html += f'<span class="{cls}">{step}</span>'
        if i < len(steps) - 1:
            steps_html += '<span class="pipeline-arrow">→</span>'
    st.markdown(
        f'<div class="hr-card" style="text-align:center">{steps_html}</div>'
        '<p style="color:#8fa3c2;font-size:0.85rem;text-align:center">'
        "From fragmented events to consolidated information: this frontend queries only "
        "the final layer through the API.</p>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("Records per table")
    try:
        stats = get_statistics()
    except ApiUnavailableError:
        st.error("Could not connect to the API. Check that the backend is running.")
        return
    except ApiRequestError as e:
        st.error(f"Query error: {e}")
        return

    rows_tbl = stats.get("rows_per_table", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Employees", rows_tbl.get("employees", "—"))
    c2.metric("Locations", rows_tbl.get("locations", "—"))
    c3.metric("Professional profiles", rows_tbl.get("professional_profiles", "—"))
    c4, c5, c6 = st.columns(3)
    c4.metric("Bank accounts", rows_tbl.get("bank_accounts", "—"))
    c5.metric("Network data", rows_tbl.get("network_data", "—"))
    c6.metric("Processing audit", rows_tbl.get("processing_audit", "—"))

    st.divider()
    st.subheader("Employees missing a domain")
    missing = stats.get("employees_missing_domain", {})
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Locations", missing.get("locations", "—"))
    g2.metric("Professional profiles", missing.get("professional_profiles", "—"))
    g3.metric("Bank accounts", missing.get("bank_accounts", "—"))
    g4.metric("Network data", missing.get("network_data", "—"))

    with st.expander("About this application"):
        st.markdown(
            "A read-only interface over consolidated data in PostgreSQL. "
            "It does not expose raw Kafka or MongoDB events, Redis, or "
            "financial fields (IBAN and salary are excluded by design). "
            "It consumes only the API."
        )
        st.markdown(
            "**Endpoints in use:**\n"
            "- `GET /health` — liveness check\n"
            "- `GET /people/search` — search by identity fields\n"
            "- `GET /people/search/by-location-profession` — search by location or profession\n"
            "- `GET /statistics` — aggregate counts per table"
        )


def _tab_personas() -> None:
    with st.form("search_form", clear_on_submit=False):
        col_id, col_loc = st.columns(2)
        with col_id:
            st.markdown("**Identity**")
            first_name = st.text_input("First name", key="s_first_name")
            last_name = st.text_input("Last name", key="s_last_name")
            passport = st.text_input("Passport", key="s_passport")
            person_id = st.number_input(
                "ID",
                min_value=0,
                step=1,
                value=0,
                key="s_id",
                format="%d",
            )
        with col_loc:
            st.markdown("**Location & role**")
            city = st.text_input("City", key="s_city")
            address = st.text_input("Address", key="s_address")
            job = st.text_input("Job", key="s_job")
            company = st.text_input("Company", key="s_company")

        limit = st.slider(
            "Results per page",
            min_value=10,
            max_value=100,
            value=20,
            key="s_limit",
        )
        submitted = st.form_submit_button("Search")

    if submitted:
        id_val = int(person_id) if person_id and int(person_id) != 0 else None
        has_identity = any(
            [
                id_val,
                first_name.strip(),
                last_name.strip(),
                passport.strip(),
            ]
        )
        has_location = any([city.strip(), address.strip(), job.strip(), company.strip()])

        if not has_identity and not has_location:
            st.warning("Fill in at least one search field.")
            return

        with st.spinner("Querying the API..."):
            try:
                if has_identity and not has_location:
                    results = search_people(
                        id=id_val,
                        passport=passport.strip() or None,
                        first_name=first_name.strip() or None,
                        last_name=last_name.strip() or None,
                        limit=limit,
                    )
                elif has_location and not has_identity:
                    results = search_by_location_profession(
                        city=city.strip() or None,
                        address=address.strip() or None,
                        job=job.strip() or None,
                        company=company.strip() or None,
                        limit=limit,
                    )
                else:
                    results = search_all(
                        id=id_val,
                        passport=passport.strip() or None,
                        first_name=first_name.strip() or None,
                        last_name=last_name.strip() or None,
                        city=city.strip() or None,
                        address=address.strip() or None,
                        job=job.strip() or None,
                        company=company.strip() or None,
                        limit=limit,
                    )
            except ApiUnavailableError:
                st.error("Could not connect to the API. Check that the backend is running.")
                return
            except ApiRequestError as e:
                st.error(f"Query error: {e}")
                return

        if not results:
            criteria_parts = []
            if id_val:
                criteria_parts.append(f"id={id_val}")
            if first_name.strip():
                criteria_parts.append(f"first_name={first_name.strip()}")
            if last_name.strip():
                criteria_parts.append(f"last_name={last_name.strip()}")
            if passport.strip():
                criteria_parts.append(f"passport={passport.strip()}")
            if city.strip():
                criteria_parts.append(f"city={city.strip()}")
            if address.strip():
                criteria_parts.append(f"address={address.strip()}")
            if job.strip():
                criteria_parts.append(f"job={job.strip()}")
            if company.strip():
                criteria_parts.append(f"company={company.strip()}")
            criteria = ", ".join(criteria_parts)
            st.info(f"No people found matching the selected criteria: {criteria}")
            return

        st.session_state["search_results"] = results
        _render_search_results(results)

    results = st.session_state.get("search_results")
    if results:
        options = [
            f"{p.get('id')} — {(p.get('first_name') or '').strip()} "
            f"{(p.get('last_name') or '').strip()}"
            for p in results
        ]
        id_map = {opt: p for opt, p in zip(options, results, strict=True)}
        selected_label = st.selectbox("View details of...", options=options)
        if selected_label:
            _render_person_detail(id_map[selected_label])


def main() -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)

    try:
        health = get_health()
        api_ok = health.get("status") == "ok"
    except Exception:
        api_ok = False

    if api_ok:
        st.markdown("🟢 API available")
    else:
        st.warning("🔴 API unavailable")

    tab_inicio, tab_personas = st.tabs(["🏠 Home", "🔍 People"])

    with tab_inicio:
        _tab_inicio()

    with tab_personas:
        _tab_personas()


main()
