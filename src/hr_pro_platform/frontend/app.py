from __future__ import annotations

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("HRP_API_BASE_URL", "http://127.0.0.1:8123").rstrip("/")

st.set_page_config(page_title="HR Pro Explorer", layout="wide", page_icon="🌸")

CUSTOM_CSS = """
<style>
/* Palette:
   background #E7C0C5
   card #e8a598
   primary accent #FFD0BF
   secondary lilac #9b8bb4
   highlight #77B692
   main text #3d2b2b
   muted #8a6f6f
   button text #3D1D10
*/
.stApp {
    background: #E7C0C5 !important;
}
[data-testid="stAppViewContainer"] {
    background: #E7C0C5 !important;
}
[data-testid="stHeader"] {
    background: #E7C0C5 !important;
}
.main .block-container {
    background: #E7C0C5 !important;
}
h1, h2, h3, h4, h5, h6, p, span, div {
    color: #3d2b2b;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #FFD0BF;
    border-radius: 12px;
    gap: 4px;
    padding: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: #3d2b2b !important;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 18px;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #e8a598 !important;
    color: #3D1D10 !important;
    border-bottom: none !important;
}
/* Buttons */
.stButton > button {
    background: #e8a598 !important;
    color: #3D1D10 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.8rem !important;
    font-weight: 700 !important;
}
.stButton > button:hover {
    background: #77B692 !important;
    color: #3D1D10 !important;
}
.stButton > button:active {
    background: #77B692 !important;
}
.stButton > button:focus {
    box-shadow: none !important;
}
/* Inputs */
[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stSlider"] label, [data-testid="stSelectbox"] label {
    color: #3d2b2b !important;
    font-weight: 600 !important;
}
/* Metrics */
[data-testid="stMetric"] {
    background: #e8a598 !important;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 8px rgba(61,43,43,0.12);
}
[data-testid="stMetricLabel"] {
    color: #9b8bb4 !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}
[data-testid="stMetricValue"] {
    color: #FFD0BF !important;
    font-weight: 800 !important;
}
.gap-metrics [data-testid="stMetricValue"] {
    color: #e8a598 !important;
}
/* Override gap metrics to dusty rose explicitly */
div.gap-metrics [data-testid="stMetric"] {
    background: #3d2b2b !important;
}
div.gap-metrics [data-testid="stMetricValue"] {
    color: #e8a598 !important;
}
/* Cards */
.hr-card {
    background: #e8a598;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(61,43,43,0.12);
    color: #3d2b2b;
}
.hr-card h4 {
    margin: 0 0 0.3rem 0;
    color: #3D1D10;
    font-size: 1.1rem;
    font-weight: 800;
}
.hr-card .muted {
    color: #8a6f6f;
    font-size: 0.85rem;
}
.hr-card .field-row {
    color: #3d2b2b;
    font-size: 0.9rem;
    line-height: 1.7;
}
.hr-card .field-row strong {
    color: #3d2b2b;
}
.section-label {
    color: #8a6f6f;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0.6rem 0 0.5rem 0;
}
.empty-state {
    text-align: center;
    color: #8a6f6f;
    padding: 2.8rem 1rem;
    font-size: 0.95rem;
}
[data-testid="stExpander"] {
    background: #FFD0BF;
    border-radius: 10px;
    border: 1px solid #e8a598;
}
[data-testid="stDataFrame"] {
    background: #FFD0BF;
    border-radius: 10px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _handle_api_error(resp: requests.Response) -> None:
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    st.error(f"API error {resp.status_code}: {detail}")


def _api_get_people_search(params: dict) -> list | None:
    try:
        resp = requests.get(f"{API_BASE}/people/search", params=params, timeout=15)
        if not resp.ok:
            _handle_api_error(resp)
            return None
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None
    except Exception:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None


def _api_get_by_location(params: dict) -> list | None:
    try:
        resp = requests.get(
            f"{API_BASE}/people/search/by-location-profession", params=params, timeout=15
        )
        if not resp.ok:
            _handle_api_error(resp)
            return None
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None
    except Exception:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None


def _api_get_statistics() -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/statistics", timeout=15)
        if not resp.ok:
            _handle_api_error(resp)
            return None
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None
    except Exception:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None


def _health_check() -> None:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if not resp.ok or resp.json().get("status") != "ok":
            st.warning("⚠️ API unavailable — data may not load.")
    except Exception:
        st.warning("⚠️ API unavailable — data may not load.")


_health_check()

tab_search, tab_statistics, tab_about = st.tabs(["🔍 Search", "📊 Statistics", "ℹ️ About"])

# ------------------------------------------------------------------ TAB 1
with tab_search:
    with st.form("search_form", clear_on_submit=False):
        col_id, col_loc = st.columns(2)
        with col_id:
            st.markdown('<div class="section-label">Identity</div>', unsafe_allow_html=True)
            first_name = st.text_input("first_name", key="s_first_name")
            last_name = st.text_input("last_name", key="s_last_name")
            passport = st.text_input("passport", key="s_passport")
            person_id = st.number_input("id", min_value=0, step=1, value=0, key="s_id", format="%d")
            st.caption("Leave id at 0 to omit.")
        with col_loc:
            st.markdown('<div class="section-label">Location & Role</div>', unsafe_allow_html=True)
            city = st.text_input("city", key="s_city")
            address = st.text_input("address", key="s_address")
            job = st.text_input("job", key="s_job")
            company = st.text_input("company", key="s_company")

        st.divider()
        col_lim, col_off = st.columns(2)
        with col_lim:
            limit = st.slider("limit", min_value=1, max_value=100, value=20, key="s_limit")
        with col_off:
            offset = st.number_input("offset", min_value=0, value=0, step=1, key="s_offset")

        submitted = st.form_submit_button("Search")

    # session state to persist results across reruns
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = None

    if submitted:
        id_val = int(person_id) if person_id and int(person_id) != 0 else None
        identity_params = {
            k: v
            for k, v in {
                "first_name": first_name.strip() or None,
                "last_name": last_name.strip() or None,
                "passport": passport.strip() or None,
                "id": id_val,
            }.items()
            if v is not None
        }
        location_params = {
            k: v
            for k, v in {
                "city": city.strip() or None,
                "address": address.strip() or None,
                "job": job.strip() or None,
                "company": company.strip() or None,
            }.items()
            if v is not None
        }

        has_identity = bool(identity_params)
        has_location = bool(location_params)

        if not has_identity and not has_location:
            st.warning("Fill in at least one field.")
            st.session_state["search_results"] = []
        elif has_identity and not has_location:
            params = {**identity_params, "limit": limit, "offset": offset}
            data = _api_get_people_search(params)
            st.session_state["search_results"] = data if data is not None else []
        elif has_location and not has_identity:
            params = {**location_params, "limit": limit, "offset": offset}
            data = _api_get_by_location(params)
            st.session_state["search_results"] = data if data is not None else []
        else:
            id_params = {**identity_params, "limit": limit, "offset": offset}
            loc_params = {**location_params, "limit": limit, "offset": offset}
            data_a = _api_get_people_search(id_params) or []
            data_b = _api_get_by_location(loc_params) or []
            merged: dict[int, dict] = {}
            for p in data_a + data_b:
                pid = p.get("id")
                if pid not in merged:
                    merged[pid] = p
            st.session_state["search_results"] = list(merged.values())

    results = st.session_state.get("search_results")

    if results is None:
        st.markdown(
            '<div class="empty-state">Search above to explore records.</div>',
            unsafe_allow_html=True,
        )
    elif len(results) == 0:
        # Distinguish between never searched vs empty result after search
        # If submitted was ever true, we show no results; otherwise empty state
        if submitted or st.session_state.get("search_results") == []:
            # Check if user actually submitted at least once: results is [] not None
            # Show appropriate message
            if submitted:
                st.markdown(
                    '<div class="empty-state">No results found.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="empty-state">Search above to explore records.</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="empty-state">Search above to explore records.</div>',
                unsafe_allow_html=True,
            )
    else:
        # Build table rows
        rows = []
        for p in results:
            pid = p.get("id")
            fn = p.get("first_name") or ""
            ln = p.get("last_name") or ""
            profs = p.get("professional_profiles") or []
            locs = p.get("locations") or []
            job_val = profs[0].get("job") if profs and profs[0].get("job") else "—"
            city_val = locs[0].get("city") if locs and locs[0].get("city") else "—"
            domains_count = (1 if locs else 0) + (1 if profs else 0)
            domains = f"{domains_count}/2"
            rows.append(
                {
                    "id": pid,
                    "first_name": fn,
                    "last_name": ln,
                    "job": job_val,
                    "city": city_val,
                    "domains": domains,
                    "passport": p.get("passport") or "—",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

        # Detail panel
        options = [
            (
                f"{p.get('id')} — "
                f"{(p.get('first_name') or '').strip()} "
                f"{(p.get('last_name') or '').strip()}".strip()
            )
            for p in results
        ]
        id_to_person = {opt: person for opt, person in zip(options, results, strict=True)}
        selected_label = st.selectbox("Select a person to view details", options=options)
        selected = id_to_person[selected_label]

        full_name = (
            " ".join(filter(None, [selected.get("first_name"), selected.get("last_name")])).strip()
            or "Unknown"
        )
        pid = selected.get("id")
        passport_val = selected.get("passport") or "—"
        email_val = selected.get("email") or "—"
        tel_val = selected.get("telephone_number") or "—"
        sex_raw = selected.get("sex")
        if isinstance(sex_raw, list):
            sex_val = ", ".join(sex_raw) if sex_raw else "—"
        else:
            sex_val = sex_raw or "—"

        st.markdown(
            f"""
            <div class="hr-card">
                <h4 style="color:#3D1D10;">{full_name}</h4>
                <div class="muted">id: {pid} &nbsp;·&nbsp; passport: {passport_val}</div>
                <div class="field-row" style="margin-top:0.6rem;">
                    <strong>email:</strong> {email_val} &nbsp;|&nbsp;
                    <strong>telephone:</strong> {tel_val} &nbsp;|&nbsp;
                    <strong>sex:</strong> {sex_val}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            with st.expander(f"📍 Locations ({len(selected.get('locations') or [])})"):
                locs = selected.get("locations") or []
                if not locs:
                    st.caption("No locations.")
                for idx, loc in enumerate(locs, 1):
                    st.markdown(f"**Location {idx}**")
                    has_any = False
                    for field in ["full_name", "city", "address", "ip_v4"]:
                        val = loc.get(field)
                        if val is not None and str(val).strip() != "":
                            st.markdown(f"`{field}`: {val}")
                            has_any = True
                    if not has_any:
                        st.caption("No fields")
                    if idx < len(locs):
                        st.divider()
        with col_b:
            with st.expander(
                f"💼 Professional profiles ({len(selected.get('professional_profiles') or [])})"
            ):
                profs = selected.get("professional_profiles") or []
                if not profs:
                    st.caption("No professional profiles.")
                for idx, prof in enumerate(profs, 1):
                    st.markdown(f"**Profile {idx}**")
                    has_any = False
                    for field in [
                        "full_name",
                        "company",
                        "company_address",
                        "company_email",
                        "company_telephone_number",
                        "job",
                    ]:
                        val = prof.get(field)
                        if val is not None and str(val).strip() != "":
                            st.markdown(f"`{field}`: {val}")
                            has_any = True
                    if not has_any:
                        st.caption("No fields")
                    if idx < len(profs):
                        st.divider()

# ------------------------------------------------------------------ TAB 2
with tab_statistics:
    stats = _api_get_statistics()
    if stats is None:
        st.error("Could not load statistics.")
    else:
        rows_tbl = stats.get("rows_per_table", {})
        missing = stats.get("employees_missing_domain", {})

        st.markdown('<div class="section-label">Records per table</div>', unsafe_allow_html=True)
        r1c1, r1c2, r1c3 = st.columns(3)
        r1c1.metric("Employees", rows_tbl.get("employees", "—"))
        r1c2.metric("Locations", rows_tbl.get("locations", "—"))
        r1c3.metric("Professional Profiles", rows_tbl.get("professional_profiles", "—"))
        r2c1, r2c2, r2c3 = st.columns(3)
        r2c1.metric("Bank Accounts", rows_tbl.get("bank_accounts", "—"))
        r2c2.metric("Network Data", rows_tbl.get("network_data", "—"))
        r2c3.metric("Processing Audit", rows_tbl.get("processing_audit", "—"))

        st.divider()

        st.markdown(
            '<div class="section-label">Employees missing a domain</div>',
            unsafe_allow_html=True,
        )
        # Wrap gap metrics to allow dusty-rose styling
        st.markdown('<div class="gap-metrics">', unsafe_allow_html=True)
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Locations", missing.get("locations", "—"))
        g2.metric("Professional Profiles", missing.get("professional_profiles", "—"))
        g3.metric("Bank Accounts", missing.get("bank_accounts", "—"))
        g4.metric("Network Data", missing.get("network_data", "—"))
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ TAB 3
with tab_about:
    st.markdown(
        """
        <div class="hr-card">
            <h4>What this tool is</h4>
            <p class="field-row" style="margin:0.4rem 0 0 0;">
                HR Pro Explorer is a read-only interface for querying curated
                employee records stored in PostgreSQL.
                It does not expose Kafka, MongoDB RAW events, or any financial fields.
            </p>
        </div>
        """,  # noqa: E501
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hr-card">
            <h4>Data boundary</h4>
            <p class="field-row" style="margin:0.4rem 0 0 0;">
                All records shown are synthetic and curated. The API queries PostgreSQL only.
                Bank account fields (IBAN, salary) are intentionally excluded from all responses.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hr-card">
            <h4>Endpoints in use</h4>
            <ul class="field-row" style="margin:0.4rem 0 0 1.1rem; line-height:1.8;">
                <li><code>GET /health</code> — liveness check, returns
                {"status": "ok"} when the API is reachable.</li>
                <li><code>GET /people/search</code> — search employees by identity
                fields (id, passport, first_name, last_name).</li>
                <li><code>GET /people/search/by-location-profession</code> — search
                employees by location or professional fields (city, address, job, company).</li>
                <li><code>GET /statistics</code> — aggregate counts per table and
                employees missing each domain.</li>
            </ul>
        </div>
        """,  # noqa: E501
        unsafe_allow_html=True,
    )
