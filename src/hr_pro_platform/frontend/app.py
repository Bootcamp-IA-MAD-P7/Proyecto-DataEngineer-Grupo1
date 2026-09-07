from __future__ import annotations

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("HRP_API_BASE_URL", "http://127.0.0.1:8123").rstrip("/")

CUSTOM_CSS = """
<style>
.stApp, .main .block-container {
    background: #fdf6f0 !important;
}
section[data-testid="stSidebar"] {
    background: #f5e6e0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #f5e6e0;
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #7a4a45;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    border-bottom: 3px solid #c9837a !important;
    color: #7a4a45 !important;
}
.stButton > button {
    background: #c9837a !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.8rem !important;
    font-weight: 600 !important;
    transition: opacity 0.2s;
}
.stButton > button:hover {
    opacity: 0.85;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stMultiSelect label {
    color: #7a4a45 !important;
    font-weight: 600;
}
.stTextInput:focus-within, .stNumberInput:focus-within {
    border-color: #c9837a !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #c9837a !important;
    box-shadow: 0 0 0 1px #c9837a !important;
}
.person-card {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(6px);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(180,120,110,0.10);
}
.person-card h4 {
    margin: 0 0 0.4rem 0;
    color: #7a4a45;
    font-size: 1.05rem;
    font-weight: 600;
}
.person-card .meta {
    color: #9e7b78;
    font-size: 0.88rem;
    line-height: 1.6;
}
.person-card .meta strong {
    color: #7a4a45;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(4px);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(180,120,110,0.08);
}
[data-testid="stMetricLabel"] {
    color: #9e7b78 !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #7a4a45 !important;
    font-weight: 700 !important;
}
.section-label {
    color: #7a4a45;
    font-size: 1rem;
    font-weight: 700;
    margin: 0.2rem 0 0.6rem 0;
    letter-spacing: 0.02em;
}
.empty-state {
    text-align: center;
    color: #9e7b78;
    padding: 3rem 1rem;
    font-size: 0.95rem;
}
</style>
"""


def _api_get(path: str, params: dict | None = None) -> dict | list | None:
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API.  Is the backend running?")
    except requests.exceptions.HTTPError:
        st.error(f"API returned an error ({resp.status_code}).")
    except Exception:
        st.error("Unexpected error while contacting the API.")
    return None


def _health_check() -> bool:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        return resp.ok and resp.json().get("status") == "ok"
    except Exception:
        return False


def _render_person_card(person: dict) -> None:
    name = " ".join(
        filter(None, [person.get("first_name"), person.get("last_name")])
    ) or "Unknown"
    passport = person.get("passport") or "\u2014"
    email = person.get("email") or "\u2014"
    phone = person.get("telephone_number") or "\u2014"
    sex_raw = person.get("sex")
    sex = ", ".join(sex_raw) if isinstance(sex_raw, list) else (sex_raw or "\u2014")

    locations_html = ""
    for loc in person.get("locations", []):
        city = loc.get("city") or ""
        addr = loc.get("address") or ""
        ip = loc.get("ip_v4") or ""
        full = loc.get("full_name") or ""
        parts = [p for p in [full, city, addr, ip] if p]
        locations_html += "<li>" + ", ".join(parts) + "</li>" if parts else ""

    profiles_html = ""
    for prof in person.get("professional_profiles", []):
        job = prof.get("job") or ""
        company = prof.get("company") or ""
        company_email = prof.get("company_email") or ""
        company_phone = prof.get("company_telephone_number") or ""
        company_addr = prof.get("company_address") or ""
        full = prof.get("full_name") or ""
        parts = [
            p
            for p in [full, job, company, company_addr, company_email, company_phone]
            if p
        ]
        profiles_html += "<li>" + ", ".join(parts) + "</li>" if parts else ""

    card = f"""
    <div class="person-card">
        <h4>{name}</h4>
        <div class="meta">
            <strong>Passport:</strong> {passport} &nbsp;|&nbsp;
            <strong>Email:</strong> {email} &nbsp;|&nbsp;
            <strong>Phone:</strong> {phone} &nbsp;|&nbsp;
            <strong>Sex:</strong> {sex}
        </div>
    """
    if locations_html:
        card += f"""
        <details style="margin-top:0.6rem">
            <summary style="color:#7a4a45;font-weight:600;font-size:0.9rem;cursor:pointer">
                Locations ({len(person.get('locations', []))})
            </summary>
            <ul style="color:#9e7b78;font-size:0.85rem;margin:0.3rem 0 0 1.2rem">
                {locations_html}
            </ul>
        </details>
        """
    if profiles_html:
        card += f"""
        <details style="margin-top:0.6rem">
            <summary style="color:#7a4a45;font-weight:600;font-size:0.9rem;cursor:pointer">
                Professional Profiles
                ({len(person.get('professional_profiles', []))})
            </summary>
            <ul style="color:#9e7b78;font-size:0.85rem;margin:0.3rem 0 0 1.2rem">
                {profiles_html}
            </ul>
        </details>
        """
    card += "</div>"
    st.markdown(card, unsafe_allow_html=True)


def _dedup_by_id(results: list[dict]) -> list[dict]:
    seen: set[int] = set()
    deduped: list[dict] = []
    for person in results:
        pid = person.get("id")
        if pid not in seen:
            seen.add(pid)
            deduped.append(person)
    return deduped


def _tab_search() -> None:
    with st.form("search_form", clear_on_submit=False):
        st.markdown(
            '<div class="section-label">Search Employees</div>',
            unsafe_allow_html=True,
        )

        col_id, col_loc = st.columns(2)

        with col_id:
            st.markdown(
                '<div class="section-label" style="font-size:0.85rem;margin-bottom:0.3rem">'
                "Identity</div>",
                unsafe_allow_html=True,
            )
            first_name = st.text_input("First name", key="s_first_name")
            last_name = st.text_input("Last name", key="s_last_name")
            passport = st.text_input("Passport", key="s_passport")
            person_id = st.number_input(
                "ID", min_value=1, step=1, key="s_id", format="%d"
            )

        with col_loc:
            st.markdown(
                '<div class="section-label" style="font-size:0.85rem;margin-bottom:0.3rem">'
                "Location & Profession</div>",
                unsafe_allow_html=True,
            )
            city = st.text_input("City", key="s_city")
            address = st.text_input("Address", key="s_address")
            job = st.text_input("Job", key="s_job")
            company = st.text_input("Company", key="s_company")

        with st.expander("Pagination", expanded=False):
            col_lim, col_off = st.columns(2)
            with col_lim:
                limit = st.number_input(
                    "Limit",
                    min_value=1,
                    max_value=100,
                    value=20,
                    step=1,
                    key="s_limit",
                )
            with col_off:
                offset = st.number_input(
                    "Offset", min_value=0, value=0, step=1, key="s_offset"
                )

        submitted = st.form_submit_button("Search", type="primary")

    if not submitted:
        st.markdown(
            '<div class="empty-state">Enter search criteria and click <b>Search</b>.</div>',
            unsafe_allow_html=True,
        )
        return

    identity_vals = {
        "first_name": first_name.strip() or None,
        "last_name": last_name.strip() or None,
        "passport": passport.strip() or None,
        "id": int(person_id) if person_id else None,
    }
    loc_vals = {
        "city": city.strip() or None,
        "address": address.strip() or None,
        "job": job.strip() or None,
        "company": company.strip() or None,
    }

    has_identity = any(v is not None for v in identity_vals.values())
    has_location = any(v is not None for v in loc_vals.values())

    if not has_identity and not has_location:
        st.warning("Please fill in at least one search field.")
        return

    results: list[dict] = []
    merged = False

    if has_identity and not has_location:
        params = {k: v for k, v in identity_vals.items() if v is not None}
        params["limit"] = limit
        params["offset"] = offset
        data = _api_get("/people/search", params)
        if data is not None:
            results = data

    elif has_location and not has_identity:
        params = {k: v for k, v in loc_vals.items() if v is not None}
        params["limit"] = limit
        params["offset"] = offset
        data = _api_get("/people/search/by-location-profession", params)
        if data is not None:
            results = data

    else:
        merged = True
        id_params = {k: v for k, v in identity_vals.items() if v is not None}
        id_params["limit"] = limit
        id_params["offset"] = offset
        loc_params = {k: v for k, v in loc_vals.items() if v is not None}
        loc_params["limit"] = limit
        loc_params["offset"] = offset

        id_data = _api_get("/people/search", id_params) or []
        loc_data = (
            _api_get("/people/search/by-location-profession", loc_params) or []
        )
        results = _dedup_by_id(id_data + loc_data)

    if not results:
        st.markdown(
            '<div class="empty-state">No results found.</div>',
            unsafe_allow_html=True,
        )
        return

    if merged:
        st.caption(
            f"Found {len(results)} unique result(s) (merged from two queries)."
        )
    else:
        st.caption(f"Found {len(results)} result(s).")

    for person in results:
        _render_person_card(person)


def _tab_statistics() -> None:
    data = _api_get("/statistics")
    if data is None:
        st.error("Could not load statistics from the API.")
        return

    rows = data.get("rows_per_table", {})
    missing = data.get("employees_missing_domain", {})

    st.markdown(
        '<div class="section-label">Records per table</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Employees", rows.get("employees", "\u2014"))
    c2.metric("Locations", rows.get("locations", "\u2014"))
    c3.metric("Prof. Profiles", rows.get("professional_profiles", "\u2014"))
    c4.metric("Bank Accounts", rows.get("bank_accounts", "\u2014"))
    c5.metric("Network Data", rows.get("network_data", "\u2014"))
    c6.metric("Processing Audit", rows.get("processing_audit", "\u2014"))

    st.markdown("")
    st.markdown(
        '<div class="section-label">Employees missing domain</div>',
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Locations", missing.get("locations", "\u2014"))
    m2.metric("Prof. Profiles", missing.get("professional_profiles", "\u2014"))
    m3.metric("Bank Accounts", missing.get("bank_accounts", "\u2014"))
    m4.metric("Network Data", missing.get("network_data", "\u2014"))


def main() -> None:
    st.set_page_config(
        page_title="HR Pro Data Platform",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not _health_check():
        st.warning("API unavailable \u2014 results may not load.")

    tab_search, tab_statistics = st.tabs(["Search", "Statistics"])

    with tab_search:
        _tab_search()

    with tab_statistics:
        _tab_statistics()


main()
