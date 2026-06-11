"""Longitudinal Streamlit view: line charts, YoY tables, item-level trends,
and side-by-side job-factor comparison across loaded years."""
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


def render_longitudinal_view(results_by_year: Dict[str, dict]) -> None:
    """Render Streamlit longitudinal sections — line charts, item/subscale tables,
    full-factor table, and side-by-side comparison."""
    if not results_by_year:
        st.info("No survey years loaded yet. Use the sidebar to upload a REDCap CSV.")
        return
    if len(results_by_year) < 2:
        st.info("Longitudinal trends become available once at least two survey years "
                "are loaded. Upload another year in the sidebar.")
        return

    years = sorted(results_by_year.keys(), key=_sort_key)
    years_str = [str(y) for y in years]

    # =====================================================================
    # Section 1: Headline Trends Across Years
    # =====================================================================
    st.subheader("Headline Trends Across Years")
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
    # Section 2: Year-over-Year Deltas Table
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
    # Section 3: MINI-Z Subscale Trends (S1, S2, Total)
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

    # Compact subscale/total table
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
    # Section 4: MINI-Z Item-Level Trends (all 10 items)
    # =====================================================================
    st.markdown("---")
    st.subheader("MINI-Z Item-Level Trends")
    st.caption(
        "Per-item mean rating across years (overall sample, 1–5 scale, "
        "5 = best on every item per Mini-Z 2.0). Hover for item n."
    )

    # Item labels from first year, assumed consistent across years
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

    # Item-level table with delta latest vs first
    item_rows = []
    first_y, last_y = years[0], years[-1]
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
        if first_m is not None and last_m is not None:
            d = last_m - first_m
            row[f"Δ {first_y}→{last_y}"] = _fmt_delta(d)
        else:
            row[f"Δ {first_y}→{last_y}"] = "—"
        item_rows.append(row)
    st.dataframe(pd.DataFrame(item_rows), use_container_width=True, hide_index=True)

    # =====================================================================
    # Section 5: Top/Bottom Job Factors by Year (year-specific snapshots)
    # =====================================================================
    st.markdown("---")
    st.subheader("Top & Bottom Job Factors — by Year")
    st.caption(
        "Each year's top 5 satisfiers and top 5 dissatisfiers, side by side. "
        "Mean impact: −2 (very negative) … +2 (very positive)."
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

    # =====================================================================
    # Section 6: All Factors — Full Table Across Years
    # =====================================================================
    st.markdown("---")
    st.subheader("All Job Factors — Year-by-Year Means")
    st.caption(
        "Mean impact (−2 negative → +2 positive) for every factor in every "
        "loaded year, sorted by latest-year mean. The Δ column shows change "
        "from the earliest to the latest loaded year."
    )

    all_factor_labels = sorted({f["factor"]
                                for y in years
                                for f in results_by_year[y]["factors"]
                                if f["mean"] is not None})

    delta_col = f"Δ {first_y}→{last_y}"
    factor_rows = []
    for label in all_factor_labels:
        row = {"Job factor": label}
        for y in years:
            factors_idx = {f["factor"]: f for f in results_by_year[y]["factors"]}
            row[str(y)] = (factors_idx.get(label) or {}).get("mean")
        first_factors = {f["factor"]: f for f in results_by_year[first_y]["factors"]}
        last_factors = {f["factor"]: f for f in results_by_year[last_y]["factors"]}
        first_m = (first_factors.get(label) or {}).get("mean")
        last_m = (last_factors.get(label) or {}).get("mean")
        row[delta_col] = round(last_m - first_m, 2) if (first_m is not None and last_m is not None) else None
        factor_rows.append(row)
    factor_df = pd.DataFrame(factor_rows)

    # Sort by latest-year mean descending
    if str(last_y) in factor_df.columns:
        factor_df = factor_df.sort_values(
            by=str(last_y), ascending=False, na_position="last"
        ).reset_index(drop=True)
    st.dataframe(factor_df, use_container_width=True, hide_index=True)

    # Biggest movers chart (top 10 by absolute Δ)
    if delta_col in factor_df.columns:
        movers = factor_df.copy()
        movers["abs_delta"] = movers[delta_col].abs()
        movers = movers.sort_values(by="abs_delta", ascending=False,
                                    na_position="last").head(10)
        if not movers.empty:
            st.markdown("**Biggest movers (top 10 by absolute change)**")
            fig = go.Figure()
            for i, y in enumerate(years):
                vals = [results_by_year[y]["factors"]
                        for _ in range(1)]  # placeholder
                factors_idx = {f["factor"]: f for f in results_by_year[y]["factors"]}
                y_vals = [(factors_idx.get(label) or {}).get("mean")
                          for label in movers["Job factor"]]
                fig.add_trace(go.Bar(
                    x=[lab[:50] for lab in movers["Job factor"]],
                    y=y_vals,
                    name=str(y),
                    marker_color=PALETTE[i % len(PALETTE)],
                    text=[f"{v:.2f}" if v is not None else "—" for v in y_vals],
                    textposition="outside",
                ))
            fig.add_hline(y=0, line_color="black", line_width=1)
            fig.update_layout(
                title=dict(text="Top 10 Movers — Mean Impact by Year",
                           font=dict(color=NAVY, size=15)),
                barmode="group",
                height=520,
                yaxis_title="Mean impact (−2 negative → +2 positive)",
                yaxis_range=[-2, 2],
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1, title=""),
            )
            fig.update_xaxes(tickangle=-30)
            fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
            st.plotly_chart(fig, use_container_width=True)

    # =====================================================================
    # Section 7: Side-by-Side Factor Comparison (user picks)
    # =====================================================================
    st.markdown("---")
    st.subheader("Side-by-Side Job Factor Comparison")
    st.caption(
        "Pick any subset of factors to compare across years. Defaults to the "
        "five biggest absolute movers."
    )

    # Default selection: top 5 movers
    default_pick = []
    if delta_col in factor_df.columns:
        movers = factor_df.copy()
        movers["abs_delta"] = movers[delta_col].abs()
        movers = movers.sort_values(by="abs_delta", ascending=False,
                                    na_position="last")
        default_pick = movers["Job factor"].head(5).tolist()
    if not default_pick:
        default_pick = all_factor_labels[:5]

    selected = st.multiselect(
        "Factors to compare",
        all_factor_labels,
        default=default_pick,
        key="factor_compare_multiselect",
    )

    if selected:
        fig = go.Figure()
        for i, y in enumerate(years):
            factors_idx = {f["factor"]: f for f in results_by_year[y]["factors"]}
            vals = [(factors_idx.get(label) or {}).get("mean")
                    for label in selected]
            fig.add_trace(go.Bar(
                x=[lab[:50] for lab in selected],
                y=vals,
                name=str(y),
                marker_color=PALETTE[i % len(PALETTE)],
                text=[f"{v:.2f}" if v is not None else "—" for v in vals],
                textposition="outside",
            ))
        fig.add_hline(y=0, line_color="black", line_width=1)
        fig.update_layout(
            title=dict(text="Selected Factors — Mean Impact by Year",
                       font=dict(color=NAVY, size=15)),
            barmode="group",
            height=max(420, 70 * len(selected)),
            yaxis_title="Mean impact (−2 negative → +2 positive)",
            yaxis_range=[-2, 2],
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, title=""),
        )
        if len(selected) > 4:
            fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)")
        st.plotly_chart(fig, use_container_width=True)

        # Companion delta table for the picked factors
        pick_rows = []
        for label in selected:
            row = {"Job factor": label}
            for y in years:
                factors_idx = {f["factor"]: f for f in results_by_year[y]["factors"]}
                row[str(y)] = (factors_idx.get(label) or {}).get("mean")
            first_factors = {f["factor"]: f for f in results_by_year[first_y]["factors"]}
            last_factors = {f["factor"]: f for f in results_by_year[last_y]["factors"]}
            fm = (first_factors.get(label) or {}).get("mean")
            lm = (last_factors.get(label) or {}).get("mean")
            row[delta_col] = round(lm - fm, 2) if (fm is not None and lm is not None) else None
            pick_rows.append(row)
        st.dataframe(pd.DataFrame(pick_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Pick at least one factor to render the comparison chart.")

    # =====================================================================
    # Footer
    # =====================================================================
    st.markdown("---")
    st.caption(
        "Longitudinal comparisons are aggregate only (REDCap responses are "
        "anonymous). Item-level rows use the overall sample; subscale and "
        "headline rows use the clinical sample where applicable."
    )
