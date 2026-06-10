"""Longitudinal Streamlit view: line charts and YoY tables across loaded years."""
from __future__ import annotations

from typing import Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

NAVY = "#1F4E79"
TEAL = "#2E8B8B"
ACCENT = "#C0504D"
GOLD = "#C9A227"
GRAY = "#7F7F7F"


def _line_chart(years, values, title, y_label, threshold=None, threshold_label=None,
                y_range=None, zero_line=False, color=NAVY):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=values, mode="lines+markers+text",
        text=[f"{v:.1f}" if v is not None else "—" for v in values],
        textposition="top center",
        line=dict(color=color, width=3),
        marker=dict(size=10, color=color),
        name=y_label,
    ))
    if threshold is not None:
        fig.add_hline(y=threshold, line_dash="dash", line_color=ACCENT,
                      annotation_text=threshold_label or f"Threshold = {threshold}",
                      annotation_position="top right")
    if zero_line:
        fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        title=dict(text=title, font=dict(color=NAVY, size=16)),
        xaxis_title="Survey Year",
        yaxis_title=y_label,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=40, r=20, t=60, b=40),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, type="category")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(127,127,127,0.25)")
    if y_range:
        fig.update_yaxes(range=y_range)
    return fig


def render_longitudinal_view(results_by_year: Dict[str, dict]) -> None:
    """Render longitudinal charts and tables comparing metrics across years."""
    if not results_by_year:
        st.info("No survey years loaded yet. Use the sidebar to upload a REDCap CSV.")
        return
    if len(results_by_year) < 2:
        st.info("Longitudinal trends become available once at least two survey years are "
                "loaded. Upload another year in the sidebar.")
        return

    # Sort years ascending (treat as strings to match dict keys, but sort numerically when possible)
    def _sort_key(y):
        try:
            return (0, int(y))
        except Exception:
            return (1, str(y))

    years = sorted(results_by_year.keys(), key=_sort_key)
    years_str = [str(y) for y in years]

    miniz_vals = [results_by_year[y]["miniz"]["clinical"].get("total", {}).get("mean") for y in years]
    burnout_vals = [results_by_year[y]["miniz"]["clinical"].get("burnout_pct") for y in years]
    wbi_vals = [results_by_year[y]["wellbeing"]["overall"]["mean"] if results_by_year[y]["wellbeing"]["overall"] else None for y in years]
    nps_vals = [results_by_year[y]["nps"]["overall"]["nps"] if results_by_year[y]["nps"]["overall"] else None for y in years]

    st.subheader("Headline Trends Across Years")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            _line_chart(years_str, miniz_vals,
                        "MINI-Z Total (Clinical Faculty)",
                        "Mean (out of 50)",
                        threshold=40, threshold_label="Joyful threshold (40)",
                        y_range=[10, 50], color=NAVY),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            _line_chart(years_str, burnout_vals,
                        "% Clinical Burnout",
                        "% burnout (Q2 ≤ 3)",
                        y_range=[0, 100], color=ACCENT),
            use_container_width=True,
        )
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(
            _line_chart(years_str, wbi_vals,
                        "Well-being Index (Overall)",
                        "Mean (0–10)",
                        threshold=8, threshold_label="High WBI threshold (8)",
                        y_range=[0, 10], color=TEAL),
            use_container_width=True,
        )
    with c4:
        st.plotly_chart(
            _line_chart(years_str, nps_vals,
                        "Net Promoter Score (Overall)",
                        "NPS",
                        y_range=[-100, 100], zero_line=True, color=GOLD),
            use_container_width=True,
        )

    st.markdown("---")
    st.subheader("Year-over-Year Deltas")
    delta_rows = []
    for i in range(1, len(years)):
        prev_y, curr_y = years[i - 1], years[i]
        prev_r, curr_r = results_by_year[prev_y], results_by_year[curr_y]

        def _d(curr, prev):
            if curr is None or prev is None:
                return None
            return round(curr - prev, 2)

        row = {
            "From → To": f"{prev_y} → {curr_y}",
            "Δ Sample n": _d(curr_r["sample"]["n_total"], prev_r["sample"]["n_total"]),
            "Δ MINI-Z total (clin)": _d(
                curr_r["miniz"]["clinical"].get("total", {}).get("mean"),
                prev_r["miniz"]["clinical"].get("total", {}).get("mean"),
            ),
            "Δ % burnout (clin)": _d(
                curr_r["miniz"]["clinical"].get("burnout_pct"),
                prev_r["miniz"]["clinical"].get("burnout_pct"),
            ),
            "Δ WBI mean": _d(
                curr_r["wellbeing"]["overall"]["mean"] if curr_r["wellbeing"]["overall"] else None,
                prev_r["wellbeing"]["overall"]["mean"] if prev_r["wellbeing"]["overall"] else None,
            ),
            "Δ NPS": _d(
                curr_r["nps"]["overall"]["nps"] if curr_r["nps"]["overall"] else None,
                prev_r["nps"]["overall"]["nps"] if prev_r["nps"]["overall"] else None,
            ),
        }
        delta_rows.append(row)
    st.dataframe(pd.DataFrame(delta_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Top Job Factors — Comparison Across Years")
    st.caption("Top 5 most-positive job factors in the latest year, compared across all loaded years (mean impact, −2…+2).")
    latest_year = years[-1]
    latest_factors = [f for f in results_by_year[latest_year]["factors"]
                      if f["mean"] is not None][:5]
    top_factor_labels = [f["factor"] for f in latest_factors]

    rows = []
    for label in top_factor_labels:
        row = {"Job factor": label[:60]}
        for y in years:
            yfactors = {f["factor"]: f["mean"] for f in results_by_year[y]["factors"]}
            row[str(y)] = yfactors.get(label)
        rows.append(row)
    factor_df = pd.DataFrame(rows)
    st.dataframe(factor_df, use_container_width=True, hide_index=True)

    # Bar chart: grouped by year
    fig = go.Figure()
    palette = [NAVY, TEAL, GOLD, ACCENT, "#6A4C93"]
    for i, y in enumerate(years):
        yfactors = {f["factor"]: f["mean"] for f in results_by_year[y]["factors"]}
        vals = [yfactors.get(label) for label in top_factor_labels]
        fig.add_trace(go.Bar(
            x=[label[:40] for label in top_factor_labels],
            y=vals,
            name=str(y),
            marker_color=palette[i % len(palette)],
            text=[f"{v:.2f}" if v is not None else "—" for v in vals],
            textposition="auto",
        ))
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        title=dict(text="Top Job Factors — Mean Impact by Year", font=dict(color=NAVY, size=15)),
        barmode="group",
        height=440,
        yaxis_title="Mean impact (−2 negative → +2 positive)",
        yaxis_range=[-2, 2],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title="Year",
    )
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Longitudinal comparisons are aggregate only (REDCap responses are anonymous).")
