"""Generate the PNG charts that the Word report embeds.

Ported from charts/make_charts.py and parameterized to take an in-memory
results dict and an output directory.
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

NAVY = "#1F4E79"
TEAL = "#2E8B8B"
ACCENT = "#C0504D"
GOLD = "#C9A227"
LIGHT = "#A9C4E2"
GRAY = "#7F7F7F"

PLT_RC = {
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
    "figure.dpi": 130,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
}


def generate_charts(r: dict, output_dir: str) -> dict:
    """Generate all charts for the report.

    Parameters
    ----------
    r : dict
        Results dict produced by ``analysis.compute_results``.
    output_dir : str
        Directory where PNG files will be written; created if missing.

    Returns
    -------
    dict
        Map of chart key -> absolute file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths: dict[str, str] = {}

    with plt.rc_context(PLT_RC):
        paths["wbi_by_division"] = _chart_wbi_by_division(r, output_dir)
        paths["nps_by_division"] = _chart_nps_by_division(r, output_dir)
        paths["retention_by_division"] = _chart_retention_by_division(r, output_dir)
        paths["miniz_by_division"] = _chart_miniz_by_division(r, output_dir)
        paths["factors_top_bottom"] = _chart_factors_top_bottom(r, output_dir)
        paths["stay_drivers"] = _chart_stay_drivers(r, output_dir)
        paths["leadership_overall"] = _chart_leadership_overall(r, output_dir)
        paths["miniz_items"] = _chart_miniz_items(r, output_dir)
        paths["key_outcomes_by_group"] = _chart_key_outcomes(r, output_dir)
        paths["division_count"] = _chart_division_count(r, output_dir)

    return paths


def _chart_wbi_by_division(r, out_dir):
    divs = sorted(r["wellbeing"]["by_division"], key=lambda x: x["mean"])
    if not divs:
        return _blank(out_dir, "wbi_by_division")
    labels = [d["division"] for d in divs]
    means = [d["mean"] for d in divs]
    ns = [d["n"] for d in divs]
    colors = [ACCENT if m < 5 else (GOLD if m < 7 else NAVY) for m in means]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bars = ax.barh(labels, means, color=colors, edgecolor="white")
    overall_mean = r["wellbeing"]["overall"]["mean"]
    ax.axvline(overall_mean, color=GRAY, linestyle="--", linewidth=1.5,
               label=f"Dept mean = {overall_mean}")
    for b, m, n in zip(bars, means, ns):
        ax.text(b.get_width() + 0.05, b.get_y() + b.get_height() / 2,
                f"{m} (n={n})", va="center", fontsize=9.5)
    ax.set_xlim(0, 10)
    ax.set_xlabel("Mean Well-being Index (1–10, higher = better)")
    ax.set_title("Well-being Index by Division", fontweight="bold", color=NAVY)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    return _save(fig, out_dir, "wbi_by_division")


def _chart_nps_by_division(r, out_dir):
    divs = sorted(r["nps"]["by_division"], key=lambda x: x["nps"])
    if not divs:
        return _blank(out_dir, "nps_by_division")
    labels = [d["division"] for d in divs]
    nps = [d["nps"] for d in divs]
    ns = [d["n"] for d in divs]
    colors = [ACCENT if v < -20 else (GOLD if v < 10 else NAVY) for v in nps]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bars = ax.barh(labels, nps, color=colors, edgecolor="white")
    ovr = r["nps"]["overall"]["nps"]
    ax.axvline(ovr, color=GRAY, linestyle="--", linewidth=1.5, label=f"Dept NPS = {ovr}")
    ax.axvline(0, color="black", linewidth=0.7)
    for b, m, n in zip(bars, nps, ns):
        x_off = 1 if m >= 0 else -1
        ha = "left" if m >= 0 else "right"
        ax.text(m + x_off, b.get_y() + b.get_height() / 2,
                f"{m} (n={n})", va="center", ha=ha, fontsize=9.5)
    ax.set_xlim(-100, 100)
    ax.set_xlabel("Net Promoter Score (% Promoters − % Detractors)")
    ax.set_title("Net Promoter Score by Division", fontweight="bold", color=NAVY)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    return _save(fig, out_dir, "nps_by_division")


def _chart_retention_by_division(r, out_dir):
    divs = sorted(r["retention"]["by_division"], key=lambda x: x["at_risk_pct"])
    if not divs:
        return _blank(out_dir, "retention_by_division")
    labels = [d["division"] for d in divs]
    ns = [d["n"] for d in divs]
    likely = [d["likely_stay_pct"] for d in divs]
    risk = [d["at_risk_pct"] for d in divs]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.barh(y, likely, color=NAVY, label="Likely / very likely to stay")
    ax.barh(y, risk, left=likely, color=ACCENT, label="At-risk (unlikely or unsure)")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of respondents")
    ax.set_title("Retention Outlook by Division — \"In 3 years, I will still be at VUMC\"",
                 fontweight="bold", color=NAVY)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
    plt.subplots_adjust(bottom=0.22)
    for i, (l, r2, n) in enumerate(zip(likely, risk, ns)):
        ax.text(l / 2, i, f"{l:.0f}%", va="center", ha="center", color="white",
                fontsize=9.5, fontweight="bold")
        ax.text(l + r2 / 2, i, f"{r2:.0f}%", va="center", ha="center", color="white",
                fontsize=9.5, fontweight="bold")
        ax.text(102, i, f"n={n}", va="center", fontsize=9, color=GRAY)
    return _save(fig, out_dir, "retention_by_division")


def _chart_miniz_by_division(r, out_dir):
    divs = [d for d in r["miniz"]["by_division"]
            if "subscale1" in d and "subscale2" in d and "total" in d]
    divs = sorted(divs, key=lambda x: (x.get("total") or {}).get("mean") or 0)
    if not divs:
        return _blank(out_dir, "miniz_by_division")
    labels = [d["division"] for d in divs]
    totals = [d["total"]["mean"] for d in divs]
    s1s = [d["subscale1"]["mean"] for d in divs]
    s2s = [d["subscale2"]["mean"] for d in divs]
    ns = [d["total"]["n"] for d in divs]
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.5), sharey=True)
    ax1, ax2, ax3 = axes
    y = np.arange(len(labels))
    ax1.barh(y, totals, color=NAVY)
    ax1.axvline(40, color=ACCENT, linestyle="--", linewidth=1.2, label="Joyful threshold (40)")
    ax1.set_xlim(10, 50)
    ax1.set_xlabel("Total (10–50)")
    ax1.set_title("Mini-Z Total")
    ax1.set_yticks(y)
    ax1.set_yticklabels(labels)
    ax1.legend(loc="lower right", fontsize=8, frameon=False)
    for i, (t, n) in enumerate(zip(totals, ns)):
        ax1.text(t + 0.5, i, f"{t} (n={n})", va="center", fontsize=8.5)
    ax2.barh(y, s1s, color=TEAL)
    ax2.axvline(20, color=ACCENT, linestyle="--", linewidth=1.0, label="Highly supportive (≥20)")
    ax2.set_xlim(5, 25)
    ax2.set_xlabel("Subscale 1 (5–25)")
    ax2.set_title("Subscale 1\nSupportive Work Env\n(Q1+Q2+Q3+Q4+Q9)")
    ax2.legend(loc="lower right", fontsize=7.5, frameon=False)
    for i, t in enumerate(s1s):
        ax2.text(t + 0.2, i, f"{t}", va="center", fontsize=8.5)
    ax3.barh(y, s2s, color=GOLD)
    ax3.axvline(20, color=ACCENT, linestyle="--", linewidth=1.0, label="Reasonable pace (≥20)")
    ax3.set_xlim(5, 25)
    ax3.set_xlabel("Subscale 2 (5–25)")
    ax3.set_title("Subscale 2\nWork Pace / EMR Stress\n(Q5+Q6+Q7+Q8+Q10)")
    ax3.legend(loc="lower right", fontsize=7.5, frameon=False)
    for i, t in enumerate(s2s):
        ax3.text(t + 0.2, i, f"{t}", va="center", fontsize=8.5)
    fig.suptitle("MINI-Z Scores by Division (Clinical Faculty Only)",
                 fontweight="bold", color=NAVY, y=1.02)
    plt.tight_layout()
    return _save(fig, out_dir, "miniz_by_division")


def _chart_factors_top_bottom(r, out_dir):
    factors = [f for f in r["factors"] if f["mean"] is not None]
    if not factors:
        return _blank(out_dir, "factors_top_bottom")
    top10 = factors[:10]
    bot10 = sorted(factors, key=lambda x: x["mean"])[:10]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6))

    def plot_factors(ax, items, color, title):
        items = sorted(items, key=lambda x: x["mean"])
        labels = [it["factor"][:55] for it in items]
        means = [it["mean"] for it in items]
        ns = [it["n"] for it in items]
        bars = ax.barh(labels, means, color=color)
        ax.axvline(0, color="black", linewidth=0.7)
        ax.set_xlim(-2, 2)
        ax.set_title(title, fontweight="bold", color=NAVY)
        ax.set_xlabel("Mean impact on satisfaction (−2 very neg / +2 very pos)")
        for b, m, n in zip(bars, means, ns):
            x_off = 0.05 if m >= 0 else -0.05
            ha = "left" if m >= 0 else "right"
            ax.text(m + x_off, b.get_y() + b.get_height() / 2,
                    f"{m} (n={n})", va="center", ha=ha, fontsize=9)

    plot_factors(axes[0], top10, NAVY, "Top 10 Highest-Rated Job Factors")
    plot_factors(axes[1], bot10, ACCENT, "Top 10 Lowest-Rated Job Factors")
    plt.tight_layout()
    return _save(fig, out_dir, "factors_top_bottom")


def _chart_stay_drivers(r, out_dir):
    drivers = r["retention"]["stay_reasons"]["items"][:10]
    drivers = sorted(drivers, key=lambda x: x["pct"])
    labels = [d["reason"][:55] for d in drivers]
    pcts = [d["pct"] for d in drivers]
    ns = [d["n"] for d in drivers]
    denom = r["retention"]["stay_reasons"]["denom"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.barh(labels, pcts, color=NAVY)
    ax.set_xlabel(f"% of respondents (n = {denom})")
    ax.set_title("Top Drivers of Stay Decision\n\"What changes would most influence a decision to stay?\"",
                 fontweight="bold", color=NAVY)
    for b, p, n in zip(bars, pcts, ns):
        ax.text(p + 0.5, b.get_y() + b.get_height() / 2,
                f"{p}% (n={n})", va="center", fontsize=9.5)
    ax.set_xlim(0, max(pcts) * 1.25 if max(pcts) > 0 else 10)
    return _save(fig, out_dir, "stay_drivers")


def _chart_leadership_overall(r, out_dir):
    ld = r["leadership"]["overall"]
    groups = [
        ("Division Chief",
         ["I trust my division chief",
          "Respected/valued by division chief",
          "My division chief leads effectively"]),
        ("Department Chair",
         ["I trust my department chair",
          "Respected/valued by department chair",
          "My department chair leads effectively"]),
        ("Vice Chairs (Exec)",
         ["I trust executive leadership (vice chairs)",
          "Respected/valued by executive leadership",
          "Executive leadership team leads effectively"]),
    ]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    positions, data, colors, xticks = [], [], [], []
    sub_lab = ["Trust", "Respected /\nvalued", "Leads\neffectively"]
    group_palette = [NAVY, TEAL, GOLD]
    group_centers = []
    group_spans = []
    group_labels = []
    pos = 0
    for gi, (gname, items) in enumerate(groups):
        grp_start = pos
        for j, it in enumerate(items):
            m = next((x for x in ld if x["item"] == it), None)
            if m is None or m["mean"] is None:
                continue
            positions.append(pos)
            data.append(m["mean"])
            colors.append(group_palette[gi])
            xticks.append(sub_lab[j])
            pos += 1
        group_centers.append((grp_start + pos - 1) / 2)
        group_spans.append((grp_start - 0.4, pos - 0.6))
        group_labels.append(gname)
        pos += 1.0
    if not positions:
        return _blank(out_dir, "leadership_overall")
    ax.bar(positions, data, color=colors, edgecolor="white", width=0.7)
    ax.set_xticks(positions)
    ax.set_xticklabels(xticks, rotation=0, ha="center", fontsize=9)
    ax.set_ylim(0, 5.6)
    ax.set_ylabel("Mean rating (1–5)")
    ax.set_yticks([1, 2, 3, 4, 5])
    for p, d in zip(positions, data):
        ax.text(p, d + 0.08, f"{d}", ha="center", fontsize=9, fontweight="bold")
    ax.axhline(4, color=GRAY, linestyle=":", linewidth=1, alpha=0.7)
    ax.text(positions[-1] + 0.7, 4.04, "Agree (4)", color=GRAY, fontsize=8)
    for (start, end), c, l, palette_color in zip(group_spans, group_centers, group_labels, group_palette):
        ax.plot([start, end], [5.35, 5.35], color=palette_color, lw=2.5, solid_capstyle="butt")
        ax.text(c, 5.45, l, ha="center", va="bottom", fontweight="bold", fontsize=11, color=palette_color)
    ax.set_title("Leadership Ratings — Overall Department", fontweight="bold", color=NAVY, pad=30)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    return _save(fig, out_dir, "leadership_overall")


def _chart_miniz_items(r, out_dir):
    items = r["miniz"]["clinical"]["items"]
    valid = [it for it in items if it["mean"] is not None]
    if not valid:
        return _blank(out_dir, "miniz_items")
    labels = [it["item"] for it in valid]
    means = [it["mean"] for it in valid]
    sds = [it["sd"] or 0 for it in valid]
    ns = [it["n"] for it in valid]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.barh(y, means, xerr=sds, color=NAVY, ecolor=GRAY, capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 5.2)
    ax.set_xlabel("Mean ± SD (1 = worst, 5 = best)")
    ax.set_title("MINI-Z Items — Clinical Faculty", fontweight="bold", color=NAVY)
    for b, m, sd, n in zip(bars, means, sds, ns):
        ax.text(m + sd + 0.1, b.get_y() + b.get_height() / 2,
                f"{m} ± {sd}  (n={n})", va="center", fontsize=9)
    return _save(fig, out_dir, "miniz_items")


def _chart_key_outcomes(r, out_dir):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    groups = ["Overall", "Clinical", "Research"]
    mz_o = r["miniz"]["overall"]
    mz_c = r["miniz"]["clinical"]
    mz_r = r["miniz"]["research"]
    b_pct = [mz_o["burnout_pct"] or 0, mz_c["burnout_pct"] or 0, mz_r["burnout_pct"] or 0]
    s_pct = [mz_o["stress_pct"] or 0, mz_c["stress_pct"] or 0, mz_r["stress_pct"] or 0]
    j_pct = [mz_o["jobsat_pct"] or 0, mz_c["jobsat_pct"] or 0, mz_r["jobsat_pct"] or 0]
    x = np.arange(len(groups))
    w = 0.27
    ax.bar(x - w, b_pct, w, color=ACCENT, label="Burnout (item 2 ≤ 3)")
    ax.bar(x, s_pct, w, color=GOLD, label="High stress (item 5 Agree+)")
    ax.bar(x + w, j_pct, w, color=NAVY, label="Job satisfaction (item 1 Agree+)")
    for i, (b, s, j) in enumerate(zip(b_pct, s_pct, j_pct)):
        ax.text(i - w, b + 1, f"{b}%", ha="center", fontsize=9)
        ax.text(i, s + 1, f"{s}%", ha="center", fontsize=9)
        ax.text(i + w, j + 1, f"{j}%", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel("% of respondents")
    ax.set_ylim(0, 120)
    ax.set_title("Key MINI-Z Outcomes by Group", fontweight="bold", color=NAVY)
    ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
    return _save(fig, out_dir, "key_outcomes_by_group")


def _chart_division_count(r, out_dir):
    divs_data = [d for d in r["demographics"]["tables"].get("Primary Division", [])
                 if d["value"] != "Missing"]
    if not divs_data:
        return _blank(out_dir, "division_count")
    divs_data = sorted(divs_data, key=lambda x: x["n"])
    labels = [d["value"] for d in divs_data]
    ns = [d["n"] for d in divs_data]
    total_n = r["demographics"]["n_total"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(labels, ns, color=NAVY)
    ax.set_xlabel(f"Faculty count (total n = {total_n})")
    ax.set_title("Respondents by Primary Division", fontweight="bold", color=NAVY)
    for b, n in zip(bars, ns):
        pct = round(100 * n / total_n, 1) if total_n > 0 else 0
        ax.text(n + 0.3, b.get_y() + b.get_height() / 2,
                f"{n} ({pct}%)", va="center", fontsize=9.5)
    return _save(fig, out_dir, "division_count")


def _save(fig, out_dir, name):
    path = os.path.join(out_dir, f"{name}.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def _blank(out_dir, name):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, "(no data)", ha="center", va="center", color=GRAY, fontsize=14)
    ax.set_axis_off()
    return _save(fig, out_dir, name)
