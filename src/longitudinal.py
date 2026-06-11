"""Longitudinal Streamlit view: streamlined snapshot across loaded survey
years. Sections: headline trends, YoY deltas, MINI-Z subscale & item trends,
retention trends, job-factor highlights (top 5/bottom 5 per year + compare),
and leadership highlights (same pattern)."""
from __future__ import annotations

from typing import Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

NAVY = "#1F4E79"
TEAL = "#2E8B8B"
ACCENT = "#C0504D"
GOLD = "#C9A227"
PURPLE = "#6A4C93"
GRAY = "#7F7F7F"

PALETTE = [NAVY, TEAL, GOLD, ACCENT, PURPLE]


def _sort_key(y):
    try:
        return (0, int(y))
    except Exception:
        return (1, str(y))


def _line_chart(years, values, title, y_label, threshold=None,
                threshold_label=None, y_range=None, zero_line=False, color=NAVY):
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


def _fmt_delta(d, *, pp=False):
    if d is None or pd.isna(d):
        return "—"
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1f}pp" if pp else f"{sign}{d:.2f}"


def _compute_movers(results_by_year, years, accessor):
    """For an accessor(results, label) -> mean, return labels sorted by
    absolute change from first to last year."""
    first_y, last_y = years[0], years[-1]
    items_first = accessor(results_by_year[first_y])
    items_last = accessor(results_by_year[last_y])
    all_labels = sorted(set(items_first.keys()) | set(items_last.keys()))
    pairs = []
    for label in all_labels:
        fm = items_first.get(label)
        lm = items_last.get(label)
        if fm is None or lm is None:
            continue
        pairs.append((label, fm, lm, lm - fm))
    pairs.sort(key=lambda r: abs(r[3]), reverse=True)
    return pairs


def _compare_chart(years, years_str, results_by_year, selected_labels, accessor,
                   *, title, y_label, y_range, fmt="{:+.2f}"):
    fig = go.Figure()
    for i, y in enumerate(years):
        idx = accessor(results_by_year[y])
        vals = [idx.get(label) for label in selected_labels]
        fig.add_trace(go.Bar(
            x=[lab[:50] for lab in selected_labels],
            y=vals,
            name=str(y),
            marker_color=PALETTE[i % len(PALETTE)],
            text=[fmt.format(v) if v is not None else "—" for v in vals],
            textposition="outside",
        ))
    if y_range[0] < 0 < y_range[1]:
        fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        title=dict(text=title, font=dict(color=NAVY, size=15)),
        barmode="group",
        height=max(420, 80 * len(selected_labels)),
        yaxis_title=y_label,
        yaxis_range=list(y_range),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, title=""),
    )
    if len(selected_labels) > 4:
        fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
    return fig


def render_longitudinal_view(results_by_year: Dict[str, dict]) -> None:
    """Streamlined longitudinal snapshot."""
    if not results_by_year:
        st.info("No survey years loaded yet. Use the sidebar to upload a REDCap CSV.")
        return
    if len(results_by_year) < 2:
        st.info("Longitudinal trends become available once at least two survey years "
                "are loaded. Upload another year in the sidebar.")
        return

    years = sorted(results_by_year.keys(), key=_sort_key)
    years_str = [str(y) for y in years]
    first_y, last_y = years[0], years[-1]
    delta_col = f"Δ {first_y}→{last_y}"

    # =====================================================================
    # 1. Headline Trends Across Years
    # =====================================================================
    st.subheader("Headline Trends")
    miniz_vals = [results_by_year[y]["miniz"]["clinical"].get("total", {}).get("mean")
                  for y in years]
    burnout_vals = [results_by_year[y]["miniz"]["clinical"].get("burnout_pct")
                    for y in years]
    wbi_vals = [results_by_year[y]["wellbeing"]["overall"]["mean"]
                if results_by_year[y]["wellbeing"]["overall"] else None
                for y in years]
    nps_vals = [results_by_year[y]["nps"]["overall"]["nps"]
                if results_by_year[y]["nps"]["overall"] else None
                for y in years]

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

    # =====================================================================
    # 2. Year-over-Year Deltas
    # =====================================================================
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

    # =====================================================================
    # 3. MINI-Z Subscale Trends
    # =====================================================================
    st.markdown("---")
    st.subheader("MINI-Z Subscale Trends — Clinical Faculty")
    s1_vals = [results_by_year[y]["miniz"]["clinical"].get("subscale1", {}).get("mean")
               for y in years]
    s2_vals = [results_by_year[y]["miniz"]["clinical"].get("subscale2", {}).get("mean")
               for y in years]

    fig = go.Figure()
    for label, vals, color in [
        ("Subscale 1 — Supportive Work Env (Q1+Q2+Q3+Q4+Q9)", s1_vals, NAVY),
        ("Subscale 2 — Work Pace / EMR Stress (Q5+Q6+Q7+Q8+Q10)", s2_vals, TEAL),
    ]:
        fig.add_trace(go.Scatter(
            x=years_str, y=vals,
            mode="lines+markers+text",
            text=[f"{v:.2f}" if v is not None else "—" for v in vals],
            textposition="top center",
            line=dict(color=color, width=3),
            marker=dict(size=10, color=color),
            name=label,
        ))
    fig.add_hline(y=20, line_dash="dash", line_color=ACCENT,
                  annotation_text="≥20 = highly supportive / reasonable pace",
                  annotation_position="top right")
    fig.update_layout(
        title=dict(text="MINI-Z Subscale Means by Year",
                   font=dict(color=NAVY, size=16)),
        xaxis_title="Survey Year",
        yaxis_title="Subscale mean (5–25)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(l=40, r=20, t=60, b=110),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                    xanchor="center", x=0.5),
    )
    fig.update_xaxes(showgrid=False, type="category")
    fig.update_yaxes(range=[5, 25], gridcolor="rgba(127,127,127,0.25)")
    st.plotly_chart(fig, use_container_width=True)

    sub_rows = []
    for y in years:
        mz = results_by_year[y]["miniz"]["clinical"]
        s1 = mz.get("subscale1") or {}
        s2 = mz.get("subscale2") or {}
        tot = mz.get("total") or {}
        sub_rows.append({
            "Year": y,
            "n (10-item)": tot.get("n"),
            "Total (10–50)": tot.get("mean"),
            "% ≥40 joyful": tot.get("joyful_pct"),
            "Subscale 1 (5–25)": s1.get("mean"),
            "S1 % ≥20": s1.get("supportive_pct"),
            "Subscale 2 (5–25)": s2.get("mean"),
            "S2 % ≥20": s2.get("lowstress_pct"),
        })
    st.dataframe(pd.DataFrame(sub_rows), use_container_width=True, hide_index=True)

    # =====================================================================
    # 4. MINI-Z Item-Level Trends
    # =====================================================================
    st.markdown("---")
    st.subheader("MINI-Z Item-Level Trends")
    st.caption(
        "Per-item mean rating across years (overall sample, 1–5 scale, "
        "5 = best on every item per Mini-Z 2.0). Hover for item n."
    )

    base_items = results_by_year[years[0]]["miniz"]["overall"]["items"]
    item_labels = [it["item"] for it in base_items]
    short_labels = [lab.split(".")[0] if "." in lab else lab[:6] for lab in item_labels]

    fig = go.Figure()
    for i, y in enumerate(years):
        items_idx = {it["item"]: it for it in
                     results_by_year[y]["miniz"]["overall"]["items"]}
        vals = [(items_idx.get(label) or {}).get("mean") for label in item_labels]
        ns = [(items_idx.get(label) or {}).get("n", 0) for label in item_labels]
        fig.add_trace(go.Bar(
            x=short_labels, y=vals, name=str(y),
            marker_color=PALETTE[i % len(PALETTE)],
            text=[f"{v:.2f}" if v is not None else "—" for v in vals],
            textposition="outside",
            customdata=[[lab, n] for lab, n in zip(item_labels, ns)],
            hovertemplate=("<b>%{customdata[0]}</b><br>"
                           "Mean: %{y:.2f}<br>n: %{customdata[1]}"
                           "<extra>%{fullData.name}</extra>"),
        ))
    fig.update_layout(
        title=dict(text="MINI-Z Item Means by Year",
                   font=dict(color=NAVY, size=15)),
        barmode="group", height=440,
        xaxis_title="MINI-Z Item",
        yaxis_title="Mean rating (1–5)",
        yaxis_range=[0, 5.8],
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, title=""),
    )
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
    st.plotly_chart(fig, use_container_width=True)

    item_rows = []
    first_idx = {it["item"]: it for it in results_by_year[first_y]["miniz"]["overall"]["items"]}
    last_idx = {it["item"]: it for it in results_by_year[last_y]["miniz"]["overall"]["items"]}
    for label in item_labels:
        row = {"Item": label}
        for y in years:
            items_idx = {it["item"]: it for it in
                         results_by_year[y]["miniz"]["overall"]["items"]}
            m = (items_idx.get(label) or {}).get("mean")
            sd = (items_idx.get(label) or {}).get("sd")
            row[str(y)] = (f"{m:.2f} (SD {sd:.2f})"
                           if (m is not None and sd is not None) else "—")
        first_m = (first_idx.get(label) or {}).get("mean")
        last_m = (last_idx.get(label) or {}).get("mean")
        row[delta_col] = (_fmt_delta(last_m - first_m)
                          if (first_m is not None and last_m is not None) else "—")
        item_rows.append(row)
    st.dataframe(pd.DataFrame(item_rows), use_container_width=True, hide_index=True)

    # =====================================================================
    # 5. Retention Trends (NEW)
    # =====================================================================
    st.markdown("---")
    st.subheader("Retention Trends")
    st.caption(
        "Item: \"In 3 years, I will still be working at VUMC.\" "
        "At-risk = neutral or worse; likely-to-stay = likely or very likely."
    )

    at_risk_vals = [(results_by_year[y]["retention"]["overall"] or {}).get("at_risk_pct")
                    for y in years]
    likely_vals = [(results_by_year[y]["retention"]["overall"] or {}).get("likely_stay_pct")
                   for y in years]
    ret_means = [(results_by_year[y]["retention"]["overall"] or {}).get("mean")
                 for y in years]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years_str, y=likely_vals, mode="lines+markers+text",
        text=[f"{v:.0f}%" if v is not None else "—" for v in likely_vals],
        textposition="top center",
        line=dict(color=NAVY, width=3),
        marker=dict(size=10, color=NAVY),
        name="% Likely-to-stay",
    ))
    fig.add_trace(go.Scatter(
        x=years_str, y=at_risk_vals, mode="lines+markers+text",
        text=[f"{v:.0f}%" if v is not None else "—" for v in at_risk_vals],
        textposition="bottom center",
        line=dict(color=ACCENT, width=3),
        marker=dict(size=10, color=ACCENT),
        name="% At-risk",
    ))
    fig.update_layout(
        title=dict(text="Retention — At-risk vs Likely-to-stay",
                   font=dict(color=NAVY, size=16)),
        xaxis_title="Survey Year",
        yaxis_title="% of respondents",
        yaxis_range=[0, 100],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=40, r=20, t=60, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=-0.20,
                    xanchor="center", x=0.5),
    )
    fig.update_xaxes(type="category")
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
    st.plotly_chart(fig, use_container_width=True)

    ret_rows = []
    for y, mean_v, at_risk, likely in zip(years, ret_means, at_risk_vals, likely_vals):
        ret_rows.append({
            "Year": y,
            "n": (results_by_year[y]["retention"]["overall"] or {}).get("n"),
            "Mean (0–4)": mean_v,
            "% At-risk": at_risk,
            "% Likely-to-stay": likely,
        })
    st.dataframe(pd.DataFrame(ret_rows), use_container_width=True, hide_index=True)

    # =====================================================================
    # 6. Job Factors — top 5/bottom 5 per year + compare
    # =====================================================================
    st.markdown("---")
    st.subheader("Job Factors")
    st.caption(
        "Year-specific top satisfiers and dissatisfiers (mean impact: "
        "−2 negative … +2 positive). Use the comparison picker below to "
        "track specific factors across years."
    )

    cols = st.columns(len(years))
    for i, y in enumerate(years):
        with cols[i]:
            st.markdown(f"### {y}")
            year_factors = [f for f in results_by_year[y]["factors"]
                            if f["mean"] is not None]
            top5 = year_factors[:5]
            bottom5 = year_factors[-5:][::-1]

            st.markdown("**Top 5 satisfiers**")
            st.dataframe(
                pd.DataFrame([
                    {"Factor": f["factor"][:55], "Mean": f["mean"], "n": f["n"]}
                    for f in top5
                ]),
                use_container_width=True, hide_index=True,
            )
            st.markdown("**Top 5 dissatisfiers**")
            st.dataframe(
                pd.DataFrame([
                    {"Factor": f["factor"][:55], "Mean": f["mean"], "n": f["n"]}
                    for f in bottom5
                ]),
                use_container_width=True, hide_index=True,
            )

    st.markdown("---")
    st.markdown("#### Side-by-side comparison — pick any factors")
    st.caption("Defaults to the five biggest absolute movers between the "
               "earliest and latest loaded years.")

    factor_accessor = lambda r: {f["factor"]: f["mean"] for f in r["factors"]
                                  if f["mean"] is not None}
    factor_movers = _compute_movers(results_by_year, years, factor_accessor)
    all_factor_labels = sorted({f["factor"] for y in years
                                for f in results_by_year[y]["factors"]
                                if f["mean"] is not None})
    factor_defaults = [label for label, _, _, _ in factor_movers[:5]] or all_factor_labels[:5]

    selected_factors = st.multiselect(
        "Job factors to compare",
        all_factor_labels,
        default=factor_defaults,
        key="factor_compare_multiselect",
    )
    if selected_factors:
        fig = _compare_chart(
            years, years_str, results_by_year, selected_factors,
            factor_accessor,
            title="Selected Job Factors — Mean Impact by Year",
            y_label="Mean impact (−2 negative → +2 positive)",
            y_range=(-2, 2),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Companion delta table
        pick_rows = []
        for label in selected_factors:
            row = {"Job factor": label}
            for y in years:
                row[str(y)] = factor_accessor(results_by_year[y]).get(label)
            fm = factor_accessor(results_by_year[first_y]).get(label)
            lm = factor_accessor(results_by_year[last_y]).get(label)
            row[delta_col] = round(lm - fm, 2) if (fm is not None and lm is not None) else None
            pick_rows.append(row)
        st.dataframe(pd.DataFrame(pick_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Pick at least one factor to render the comparison chart.")

    # =====================================================================
    # 7. Leadership Items — top 5/bottom 5 per year + compare (NEW)
    # =====================================================================
    st.markdown("---")
    st.subheader("Leadership Items")
    st.caption(
        "Year-specific top and bottom leadership ratings "
        "(mean on a 1–5 scale; 5 = strongly agree)."
    )

    cols = st.columns(len(years))
    for i, y in enumerate(years):
        with cols[i]:
            st.markdown(f"### {y}")
            items = sorted(
                [it for it in results_by_year[y]["leadership"]["overall"]
                 if it.get("mean") is not None],
                key=lambda x: -x["mean"],
            )
            top5 = items[:5]
            bottom5 = items[-5:][::-1]

            st.markdown("**Top 5 highest-rated**")
            st.dataframe(
                pd.DataFrame([
                    {"Item": it["item"][:55],
                     "Mean": it["mean"],
                     "% Agree+": it.get("agree_pct")}
                    for it in top5
                ]),
                use_container_width=True, hide_index=True,
            )
            st.markdown("**Top 5 lowest-rated**")
            st.dataframe(
                pd.DataFrame([
                    {"Item": it["item"][:55],
                     "Mean": it["mean"],
                     "% Agree+": it.get("agree_pct")}
                    for it in bottom5
                ]),
                use_container_width=True, hide_index=True,
            )

    st.markdown("---")
    st.markdown("#### Side-by-side comparison — pick any leadership items")
    st.caption("Defaults to the five biggest absolute movers between the "
               "earliest and latest loaded years.")

    ld_accessor = lambda r: {it["item"]: it["mean"]
                              for it in r["leadership"]["overall"]
                              if it.get("mean") is not None}
    ld_movers = _compute_movers(results_by_year, years, ld_accessor)
    all_ld_labels = sorted({it["item"] for y in years
                            for it in results_by_year[y]["leadership"]["overall"]})
    ld_defaults = [label for label, _, _, _ in ld_movers[:5]] or all_ld_labels[:5]

    selected_ld = st.multiselect(
        "Leadership items to compare",
        all_ld_labels,
        default=ld_defaults,
        key="ld_compare_multiselect",
    )
    if selected_ld:
        fig = _compare_chart(
            years, years_str, results_by_year, selected_ld,
            ld_accessor,
            title="Selected Leadership Items — Mean Rating by Year",
            y_label="Mean rating (1–5)",
            y_range=(1, 5),
            fmt="{:.2f}",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Companion delta table
        pick_rows = []
        for label in selected_ld:
            row = {"Leadership item": label}
            for y in years:
                row[str(y)] = ld_accessor(results_by_year[y]).get(label)
            fm = ld_accessor(results_by_year[first_y]).get(label)
            lm = ld_accessor(results_by_year[last_y]).get(label)
            row[delta_col] = round(lm - fm, 2) if (fm is not None and lm is not None) else None
            pick_rows.append(row)
        st.dataframe(pd.DataFrame(pick_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Pick at least one leadership item to render the comparison chart.")

    # =====================================================================
    # Footer
    # =====================================================================
    st.markdown("---")
    st.caption(
        "Longitudinal comparisons are aggregate only (REDCap responses are "
        "anonymous). Item-level rows use the overall sample; subscale and "
        "headline rows use the clinical sample where applicable."
    )
