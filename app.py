"""VUMC Department of Anesthesiology Faculty Survey — Streamlit app.

Wraps the existing analysis pipeline so survey leaders can upload a REDCap CSV
and instantly receive (a) the polished department Word report and (b) a
multi-year longitudinal trends view.
"""
from __future__ import annotations

import io
import os
import tempfile
from typing import Dict

import pandas as pd
import streamlit as st

from src.analysis import compute_results
from src.chart_builder import generate_charts
from src.division_report import build_all_division_reports, build_division_report
from src.longitudinal import render_longitudinal_view
from src.report_builder import build_report

st.set_page_config(
    page_title="VUMC Anesthesiology Faculty Survey",
    page_icon=":bar_chart:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------

def _check_password() -> bool:
    """Block the app behind a single shared password stored in st.secrets."""
    if st.session_state.get("password_ok"):
        return True

    st.title("VUMC Anesthesiology Faculty Survey")
    st.subheader("Department Engagement & Well-being — Analysis Portal")
    st.write("This portal is restricted to authorized department personnel.")

    expected = st.secrets.get("app_password") if hasattr(st, "secrets") else None
    if not expected:
        st.error(
            "App password is not configured. In Streamlit Cloud, open the app's "
            "Settings → Secrets and add a line like: `app_password = \"your-password\"`."
        )
        st.stop()

    pw = st.text_input("Password", type="password", key="_pw_input")
    if st.button("Sign in", type="primary"):
        if pw == expected:
            st.session_state["password_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
    return False


_check_password()

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "years_data" not in st.session_state:
    st.session_state["years_data"]: Dict[str, pd.DataFrame] = {}
if "results" not in st.session_state:
    st.session_state["results"]: Dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Sidebar — upload & manage years
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Upload & Manage Years")
    st.caption(
        "Upload the REDCap raw-data CSV export. The app deduplicates known test "
        "records automatically."
    )

    uploads = st.file_uploader(
        "REDCap CSV file(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="uploader",
    )
    year_input = st.text_input("Survey year", value="", placeholder="e.g. 2026")

    if st.button("Add year", type="primary", use_container_width=True):
        if not uploads:
            st.error("Pick at least one CSV file first.")
        elif not year_input.strip():
            st.error("Enter a survey year.")
        else:
            year_key = year_input.strip()
            try:
                # Concatenate multiple files for one year if user uploaded several
                frames = []
                for up in uploads:
                    up.seek(0)
                    frames.append(pd.read_csv(up))
                df = pd.concat(frames, ignore_index=True)
                with st.spinner(f"Computing results for {year_key}…"):
                    results = compute_results(df, year_key)
                st.session_state["years_data"][year_key] = df
                st.session_state["results"][year_key] = results
                st.success(
                    f"Added {year_key}: n = {results['sample']['n_total']} faculty "
                    f"({results['sample']['clinical']} clinical, "
                    f"{results['sample']['research']} research)."
                )
            except Exception as e:
                st.error(f"Failed to process file: {e}")

    st.divider()
    st.subheader("Loaded years")
    if not st.session_state["years_data"]:
        st.caption("(none yet)")
    else:
        for year_key in sorted(st.session_state["years_data"].keys()):
            r = st.session_state["results"][year_key]
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{year_key}** — n = {r['sample']['n_total']}")
            with col_b:
                if st.button("Remove", key=f"rm_{year_key}", use_container_width=True):
                    del st.session_state["years_data"][year_key]
                    del st.session_state["results"][year_key]
                    st.rerun()

    st.divider()
    st.caption(
        "Tip: passwords for this app are stored in Streamlit Cloud Secrets. "
        "Share the URL only with department personnel."
    )


# ---------------------------------------------------------------------------
# Main area — tabs
# ---------------------------------------------------------------------------

st.title("VUMC Anesthesiology Faculty Survey — Analysis Portal")
st.caption("Engagement & Well-being analytics for the Department of Anesthesiology")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Department Report", "Division Reports", "Longitudinal Trends", "About"]
)


# ===== TAB 1 — Department Report =====
with tab1:
    st.header("Department Report")
    st.write(
        "Pick a survey year and generate the comprehensive Word document — the same "
        "polished report previously produced by the analysis pipeline."
    )

    available_years = sorted(st.session_state["results"].keys())
    if not available_years:
        st.info("Upload a REDCap CSV in the sidebar to begin.")
    else:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            sel_year = st.selectbox("Survey year", available_years,
                                    index=len(available_years) - 1)
        r = st.session_state["results"][sel_year]

        st.subheader(f"Snapshot — {sel_year}")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Respondents (n)", r["sample"]["n_total"])
        mz_total = r["miniz"]["clinical"].get("total", {}).get("mean")
        m2.metric("MINI-Z total (clinical)",
                  f"{mz_total:.2f}" if mz_total is not None else "—",
                  help="Mean of all 10 items (range 10–50). ≥40 = joyful workplace.")
        bo = r["miniz"]["clinical"].get("burnout_pct")
        m3.metric("% Burnout (clinical)",
                  f"{bo:.1f}%" if bo is not None else "—",
                  help="MINI-Z item 2 ≤ 3 ('definitely burning out' or worse).")
        wbi = r["wellbeing"]["overall"]["mean"] if r["wellbeing"]["overall"] else None
        m4.metric("WBI mean (overall)",
                  f"{wbi:.2f}" if wbi is not None else "—",
                  help="Well-being index 0–10.")
        nps = r["nps"]["overall"]["nps"] if r["nps"]["overall"] else None
        m5.metric("NPS (overall)",
                  f"{nps:.1f}" if nps is not None else "—",
                  help="% Promoters (9–10) − % Detractors (0–6).")

        st.markdown("&nbsp;", unsafe_allow_html=True)

        if st.button(f"Generate {sel_year} Department Report",
                     type="primary", use_container_width=False):
            with st.spinner("Building charts and Word report…"):
                tmpdir = tempfile.mkdtemp(prefix=f"survey_{sel_year}_")
                generate_charts(r, tmpdir)
                buffer = io.BytesIO()
                build_report(r, tmpdir, sel_year, buffer)
                buffer.seek(0)
                st.session_state[f"_report_{sel_year}"] = buffer.getvalue()

        if st.session_state.get(f"_report_{sel_year}"):
            st.success("Report ready.")
            st.download_button(
                label=f"Download {sel_year} Word report (.docx)",
                data=st.session_state[f"_report_{sel_year}"],
                file_name=f"VUMC_Anesthesiology_Faculty_Survey_{sel_year}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=False,
            )


# ===== TAB 2 — Division Reports =====
with tab2:
    st.header("Division Reports")
    st.write(
        "Generate focused per-division Word reports. Each report compares the "
        "division's MINI-Z, well-being, NPS, and retention numbers to the "
        "department average, lists this division's top and bottom job factors, "
        "and shows leadership ratings — meant for review and discussion with "
        "the Division Chief."
    )

    available_years = sorted(st.session_state["results"].keys())
    if not available_years:
        st.info("Upload a REDCap CSV in the sidebar to begin.")
    else:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            sel_year = st.selectbox(
                "Survey year",
                available_years,
                index=len(available_years) - 1,
                key="div_year",
            )
        r = st.session_state["results"][sel_year]
        raw_df = st.session_state["years_data"][sel_year]

        # List of divisions with respondent counts
        div_list = [
            (d["division"], d["n"])
            for d in r["miniz"]["by_division"]
            if d["division"] and d["division"] != "Missing"
        ]
        div_names = [d[0] for d in div_list]

        st.markdown("**Divisions detected in this year's data**")
        df_div_summary = pd.DataFrame(
            [{"Division": n, "n respondents": k} for n, k in div_list]
        )
        st.dataframe(df_div_summary, use_container_width=True, hide_index=True)

        st.markdown("---")

        col_a, col_b = st.columns(2)

        # Single-division report
        with col_a:
            st.subheader("Single division")
            picked = st.selectbox(
                "Pick a division",
                div_names,
                key=f"div_single_{sel_year}",
            )
            if st.button(
                f"Generate {picked} report",
                type="primary",
                use_container_width=True,
                key=f"btn_single_{sel_year}_{picked}",
            ):
                with st.spinner(f"Building {picked} division report…"):
                    buf = io.BytesIO()
                    build_division_report(r, raw_df, picked, sel_year, buf)
                    buf.seek(0)
                    st.session_state[f"_div_{sel_year}_{picked}"] = buf.getvalue()

            cached = st.session_state.get(f"_div_{sel_year}_{picked}")
            if cached:
                safe_picked = picked.replace(" ", "_").replace("/", "_")
                st.download_button(
                    f"Download {picked} report (.docx)",
                    data=cached,
                    file_name=f"VUMC_Anesth_{sel_year}_{safe_picked}_Division_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"dl_single_{sel_year}_{picked}",
                )

        # All-division ZIP
        with col_b:
            st.subheader("All divisions (ZIP)")
            st.caption(
                f"Generates one Word doc per division (n = {len(div_names)} "
                "divisions) and packages them into a single ZIP download."
            )
            if st.button(
                f"Generate all {sel_year} division reports",
                type="primary",
                use_container_width=True,
                key=f"btn_zip_{sel_year}",
            ):
                with st.spinner(
                    f"Building {len(div_names)} division reports… (~5–15 s)"
                ):
                    zip_bytes = build_all_division_reports(
                        r, raw_df, sel_year, divisions=div_names
                    )
                    st.session_state[f"_div_zip_{sel_year}"] = zip_bytes

            cached_zip = st.session_state.get(f"_div_zip_{sel_year}")
            if cached_zip:
                st.success(
                    f"ZIP ready ({len(cached_zip) / 1024:.0f} KB, "
                    f"{len(div_names)} reports)."
                )
                st.download_button(
                    f"Download all {sel_year} division reports (.zip)",
                    data=cached_zip,
                    file_name=f"VUMC_Anesth_{sel_year}_Division_Reports.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key=f"dl_zip_{sel_year}",
                )


# ===== TAB 3 — Longitudinal Trends =====
with tab3:
    st.header("Longitudinal Trends")
    st.write(
        "Compare engagement and well-being metrics across all loaded survey years. "
        "Useful for retreat presentations and tracking interventions over time."
    )
    render_longitudinal_view(st.session_state["results"])


# ===== TAB 4 — About =====
with tab4:
    st.header("About this portal")
    st.markdown("""
**Purpose.** This portal wraps the analysis pipeline used to produce the
department's Faculty Engagement & Well-being report. Upload a REDCap raw-data
CSV export, and the portal will compute headline indicators, generate the
formatted Word report, and (with two or more years loaded) display longitudinal
trends.

### Methodology

**MINI-Z 2.0.** Ten items, each scored 1–5 with 5 = best (per the official
Linzer / InstitutePHI scoring manual; *no item reversal needed*).
- Subscale 1 — *Supportive Work Environment*: Q1 + Q2 + Q3 + Q4 + Q9
  (range 5–25; ≥ 20 = highly supportive).
- Subscale 2 — *Work Pace / EMR Stress*: Q5 + Q6 + Q7 + Q8 + Q10
  (range 5–25; ≥ 20 = reasonable pace).
- Total — sum of all 10 items (range 10–50; ≥ 40 = "joyful workplace").
- **Burnout** = response on Q2 of "definitely burning out" or worse (raw ≤ 3).
- **High stress** = agree/strongly agree on Q5 (raw ≤ 2).
- **Job satisfaction** = agree/strongly agree on Q1 (raw ≥ 4).
- Research faculty do not receive items 4, 6, 7, 10, so their subscale/total
  scores are not reported.

**Well-being Index (WBI).** Single 0–10 Cantril-style item. Bands: 0–5 low,
6–7 mid, 8–10 high.

**Net Promoter Score (NPS).** Standard NPS framing on the 0–10 "would you
recommend" item: 9–10 Promoter, 7–8 Passive, 0–6 Detractor.
NPS = %Promoters − %Detractors.

**Retention.** Item: "In 3 years, I will still be working at VUMC."
(0 = very unlikely, 4 = very likely.) "At-risk" = neutral or worse (≤ 2);
"likely to stay" = likely or very likely (≥ 3).

**Job factors.** Each factor rated for impact on satisfaction on a 5-pt
scale (very negative → very positive). Rescaled from raw 0–4 to −2…+2
(0 = neutral). Items coded "N/A" (8888) are dropped.

**Leadership.** Item agreement on a 1–5 scale (5 = strongly agree).
Some items are stored on a 0–4 scale and others reverse-scaled; all are
normalized to forward 1–5 before reporting.

### Data sources
- REDCap raw-data export (raw-coded values, 108 columns).
- Test records are auto-dropped: any response with "this is a test" in
  the free-text fields (`factorneg1`, `factorpos1`, `stayother`,
  `changesnetpromoter`, `comments`).
- Division, gender, ethnicity, FTE, and tenure labels are applied from
  the REDCap data dictionary (built into the analysis module).

### Notes
- REDCap responses are anonymous — longitudinal comparisons are aggregate only.
- The Streamlit Cloud password is stored in app secrets. To rotate it,
  update `app_password` in *Settings → Secrets* and ask users to refresh.
""")


