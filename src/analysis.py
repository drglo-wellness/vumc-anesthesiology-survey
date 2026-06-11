"""Analysis pipeline for the VUMC Anesthesiology Faculty Survey.

Ports the logic in analysis2/analyze2.py into a callable function that operates
on the RAW REDCap CSV (coded values) only, applying labels via internal maps.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Code → label mappings (derived from REDCap data dictionary / labeled export)
# ---------------------------------------------------------------------------

DIVISION_MAP = {
    1: "Ambulatory",
    2: "Critical Care",
    3: "Cardiac",
    4: "MSA",
    5: "Neuro",
    6: "OB",
    7: "Pain",
    8: "Pediatric",
    9: "Pediatric Cardiac",
    10: "Research",
}
GENDER_MAP = {1: "Female", 2: "Male", 3: "Non-binary / other", 4: "Prefer not to answer"}
ETHNICITY_MAP = {
    0: "I am not Hispanic / Latino/a",
    1: "I am Hispanic / Latino/a",
    2: "Prefer not to answer",
}
TIMEVUMC_MAP = {
    1: "Less than 2 years",
    2: "2 to 5 years",
    3: "6 to 10 years",
    4: "10+ years",
}
FTE_MAP = {1: "1.0", 2: "0.51-0.9", 3: "0.5 or less"}
AD_MAP = {0: "0 - 22", 1: "23 - 39", 2: "40 - 52", 3: "53 - 100", 4: "101+"}
RACE_COLS = {
    "race___1": "American Indian/Alaska Native",
    "race___2": "Asian",
    "race___3": "Black/African American",
    "race___4": "Native Hawaiian/Pacific Islander",
    "race___5": "White",
    "race___6": "Prefer not to answer",
}
FTEREDUCE_MAP = {0: "No", 1: "Yes", 2: "Maybe", 3: "Prefer not to answer"}

MINIZ_ITEMS = [f"miniz{i}" for i in range(1, 11)]
MINIZ_LABELS = [
    "Q1. Job satisfaction",
    "Q2. Burnout (5=no symptoms)",
    "Q3. Values aligned with leaders",
    "Q4. Care team efficiency",
    "Q5. Stress (5=strongly disagree)",
    "Q6. EMR time at home (5=minimal)",
    "Q7. Documentation time",
    "Q8. Atmosphere (5=calm)",
    "Q9. Control over workload",
    "Q10. EMR frustration (5=strongly disagree)",
]
FACTOR_COLS = [
    "factor1", "factor2", "factor3", "factor5", "factor6", "factor7", "factor8",
    "factor10", "factor11", "factor14", "factor16", "factor17", "factor18",
    "factor23", "factor25_r", "factor25_r1", "factor26", "factor27", "factor28",
    "factor4_r", "factor4_r1", "factor9_r", "factor9_r1", "factor15_r", "factor15_r1",
]
FACTOR_LABELS = {
    "factor1": "Physical work environment (breakrooms, bathrooms, workstations, food)",
    "factor8": "Equipment availability, reliability, maintenance",
    "factor7": "Access to point-of-care labs (timely)",
    "factor2": "Control & predictability of overall clinical schedule",
    "factor3": "Day-to-day clinical assignments",
    "factor5": "Predictability of end-of-day relief",
    "factor6": "Availability/quality of clinical support staff",
    "factor9_r": "Oversight of SRNAs",
    "factor9_r1": "Evaluation of SRNAs",
    "factor10": "Collegiality among healthcare professionals",
    "factor11": "Dept leadership support resolving professional conflicts",
    "factor16": "Methods/processes for safety/professionalism reporting (Veritas)",
    "factor14": "Responsibilities outside clinical work (documentation, lectures, calls)",
    "factor28": "Engagement in resident/medical student education",
    "factor4_r": "Awarded appropriate academic time per CDA",
    "factor4_r1": "Actual receipt and scheduling of CDA",
    "factor26": "Departmental support for research efforts",
    "factor27": "Departmental support for education efforts",
    "factor15_r": "Availability of administrative support staff",
    "factor15_r1": "Quality of administrative support staff",
    "factor23": "Division leadership and culture",
    "factor17": "Mentorship and support for career development",
    "factor18": "Annual faculty review and promotion process",
    "factor25_r": "Total salary (base + incentives)",
    "factor25_r1": "Incentive and bonus pay structure",
}

STAY_COLS = {
    "staywhy___0": "Career advancement opportunities",
    "staywhy___10": "Improvements in length of clinical days/work week",
    "staywhy___11": "Receipt and scheduling of academic time",
    "staywhy___12": "Predictability of work schedule",
    "staywhy___2": "Increased availability of support staff",
    "staywhy___3": "Stronger sense of belonging/community",
    "staywhy___4": "Clarity around role expectations",
    "staywhy___5": "Improvements in division leadership",
    "staywhy___6": "Improvements in overall dept leadership",
    "staywhy___7": "More support for research/academic pursuits",
    "staywhy___8": "Improvements in base compensation/incentives",
    "staywhy___9": "Other",
}

# Leadership items: (raw_col, label, scale_type)
# scale_type: 'a'=0-4 forward, 'b'=1-5 forward, 'c'=1-5 reverse
LEADERSHIP_ITEMS = [
    ("trust1", "I trust my division chief", "a"),
    ("trust1a", "Respected/valued by division chief", "a"),
    ("lead1", "My division chief leads effectively", "a"),
    ("trust3a", "I trust my department chair", "a"),
    ("trust3b", "Respected/valued by department chair", "a"),
    ("lead3", "My department chair leads effectively", "a"),
    ("trust2a", "I trust executive leadership (vice chairs)", "a"),
    ("trust2", "Respected/valued by executive leadership", "a"),
    ("lead2", "Executive leadership team leads effectively", "a"),
    ("values1", "Dept leadership values my clinical contributions", "c"),
    ("values2", "Dept leadership values my research/innovation", "c"),
    ("values3", "Dept leadership values my education contributions", "c"),
    ("values4", "Dept leadership values my service/collaboration", "c"),
    ("values5", "Dept leadership values culture of safety", "c"),
    ("competinginterest", "Anesthesiology needs prioritized in competing interests", "a"),
    ("transparent1", "Career advancement expectations clear & consistent", "a"),
    ("transparent2", "Communication during faculty meetings clear/transparent", "b"),
    ("transparent3", "Understand dept leadership structure", "a"),
    ("facultymeeting", "Faculty meeting info relevant/important", "b"),
    ("accountability", "Clinical team members held accountable", "b"),
    ("community", "Sense of community/camaraderie at work", "b"),
]
KEY_LEADERSHIP = [
    "trust1", "trust1a", "lead1", "trust3a", "trust3b", "lead3",
    "trust2a", "trust2", "lead2", "community", "accountability",
    "transparent1", "transparent2", "facultymeeting",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _drop_test_records(df: pd.DataFrame) -> pd.DataFrame:
    """Drop responses that contain 'this is a test' in any free-text field."""
    text_cols = ["factorneg1", "factorpos1", "stayother", "changesnetpromoter", "comments"]
    text_cols = [c for c in text_cols if c in df.columns]
    if not text_cols:
        return df
    mask = pd.Series(False, index=df.index)
    for c in text_cols:
        mask = mask | df[c].astype(str).str.lower().str.contains("this is a test", na=False)
    return df.loc[~mask].copy()


def _safe_int(x):
    try:
        return int(x)
    except Exception:
        return None


def _round(x, n=2):
    try:
        return round(float(x), n)
    except Exception:
        return None


def _item_summary(df: pd.DataFrame, items, labels):
    out = []
    for c, lab in zip(items, labels):
        s = df[c].dropna()
        if len(s) == 0:
            out.append({"item": lab, "n": 0, "mean": None, "sd": None, "pct_favorable": None})
        else:
            n_fav = int((s >= 4).sum())
            out.append({
                "item": lab,
                "n": int(len(s)),
                "mean": round(float(s.mean()), 2),
                "sd": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                "pct_favorable": round(100 * n_fav / len(s), 1),
                "median": float(s.median()),
            })
    return out


def _miniz_full(df: pd.DataFrame) -> dict:
    """Compute MINI-Z item summary, subscales, total, and burnout/stress/sat percentages."""
    s1_items = ["miniz1", "miniz2", "miniz3", "miniz4", "miniz9"]
    s2_items = ["miniz5", "miniz6", "miniz7", "miniz8", "miniz10"]
    sub = df.dropna(subset=MINIZ_ITEMS)
    sub_s1 = df.dropna(subset=s1_items)
    sub_s2 = df.dropna(subset=s2_items)
    out = {"items": _item_summary(df, MINIZ_ITEMS, MINIZ_LABELS)}
    if len(sub) > 0:
        totals = sub[MINIZ_ITEMS].sum(axis=1)
        out["total"] = {
            "n": int(len(sub)),
            "mean": round(float(totals.mean()), 2),
            "sd": round(float(totals.std()), 2) if len(totals) > 1 else 0.0,
            "median": float(totals.median()),
            "min": int(totals.min()),
            "max": int(totals.max()),
            "joyful_n": int((totals >= 40).sum()),
            "joyful_pct": round(100 * (totals >= 40).sum() / len(sub), 1),
        }
    if len(sub_s1) > 0:
        s1 = sub_s1[s1_items].sum(axis=1)
        out["subscale1"] = {
            "n": int(len(sub_s1)),
            "mean": round(float(s1.mean()), 2),
            "sd": round(float(s1.std()), 2) if len(s1) > 1 else 0.0,
            "median": float(s1.median()),
            "min": int(s1.min()),
            "max": int(s1.max()),
            "supportive_n": int((s1 >= 20).sum()),
            "supportive_pct": round(100 * (s1 >= 20).sum() / len(sub_s1), 1),
        }
    if len(sub_s2) > 0:
        s2 = sub_s2[s2_items].sum(axis=1)
        out["subscale2"] = {
            "n": int(len(sub_s2)),
            "mean": round(float(s2.mean()), 2),
            "sd": round(float(s2.std()), 2) if len(s2) > 1 else 0.0,
            "median": float(s2.median()),
            "min": int(s2.min()),
            "max": int(s2.max()),
            "lowstress_n": int((s2 >= 20).sum()),
            "lowstress_pct": round(100 * (s2 >= 20).sum() / len(sub_s2), 1),
        }
    bo = df["miniz2"].dropna()
    out["burnout_pct"] = round(100 * (bo <= 3).sum() / len(bo), 1) if len(bo) > 0 else None
    out["burnout_n"] = int((bo <= 3).sum()) if len(bo) > 0 else 0
    out["burnout_total"] = int(len(bo))
    st = df["miniz5"].dropna()
    out["stress_pct"] = round(100 * (st <= 2).sum() / len(st), 1) if len(st) > 0 else None
    out["stress_n"] = int((st <= 2).sum()) if len(st) > 0 else 0
    js = df["miniz1"].dropna()
    out["jobsat_pct"] = round(100 * (js >= 4).sum() / len(js), 1) if len(js) > 0 else None
    out["jobsat_n"] = int((js >= 4).sum()) if len(js) > 0 else 0
    return out


def _wb(df: pd.DataFrame):
    if "wellbeingindex" not in df.columns:
        return None
    s = df["wellbeingindex"].dropna()
    if len(s) == 0:
        return None
    return {
        "n": int(len(s)),
        "mean": round(float(s.mean()), 2),
        "sd": round(float(s.std()), 2) if len(s) > 1 else 0.0,
        "median": float(s.median()),
        "min": int(s.min()),
        "max": int(s.max()),
        # WBI bands match the reference report: low ≤ 4, mid 5–7, high ≥ 8
        "low_pct": round(100 * (s <= 4).sum() / len(s), 1),
        "mid_pct": round(100 * ((s >= 5) & (s <= 7)).sum() / len(s), 1),
        "high_pct": round(100 * (s >= 8).sum() / len(s), 1),
    }


def _nps(df: pd.DataFrame):
    if "promoter" not in df.columns:
        return None
    s = df["promoter"].dropna()
    if len(s) == 0:
        return None
    n = int(len(s))
    p = int((s >= 9).sum())
    pas = int(((s >= 7) & (s <= 8)).sum())
    d = int((s <= 6).sum())
    return {
        "n": n,
        "mean": round(float(s.mean()), 2),
        "promoters_pct": round(100 * p / n, 1),
        "passives_pct": round(100 * pas / n, 1),
        "detractors_pct": round(100 * d / n, 1),
        "promoters_n": p,
        "passives_n": pas,
        "detractors_n": d,
        "nps": round(100 * p / n - 100 * d / n, 1),
    }


def _leave(df: pd.DataFrame):
    if "leave" not in df.columns:
        return None
    s = df["leave"].dropna()
    if len(s) == 0:
        return None
    n = int(len(s))
    return {
        "n": n,
        "mean": round(float(s.mean()), 2),
        "vunlikely": int((s == 0).sum()),
        "unlikely": int((s == 1).sum()),
        "neutral": int((s == 2).sum()),
        "likely": int((s == 3).sum()),
        "vlikely": int((s == 4).sum()),
        "at_risk_n": int((s <= 2).sum()),
        "at_risk_pct": round(100 * (s <= 2).sum() / n, 1),
        "likely_stay_n": int((s >= 3).sum()),
        "likely_stay_pct": round(100 * (s >= 3).sum() / n, 1),
    }


def _normalize_leadership(df: pd.DataFrame, col: str, scale: str) -> pd.Series:
    """Normalize leadership items to a forward 1-5 scale (5 = best).

    Auto-detects the raw scale (0-4 vs 1-5) per item per year because some
    items shifted coding between survey versions. Scales:
      "a" / "b" — forward (1/0 = strongly disagree, 5/4 = strongly agree)
      "c"       — reverse (1 = strongly agree, 5 = strongly disagree)
    """
    if col not in df.columns:
        return pd.Series([], dtype=float)
    s = df[col].replace(9999, np.nan).dropna()
    if len(s) == 0:
        return s
    obs_min, obs_max = float(s.min()), float(s.max())
    # 0-4 raw → shift to 1-5
    is_0_4 = obs_max <= 4 and obs_min >= 0
    is_1_5 = obs_max <= 5 and obs_min >= 1
    if is_0_4 and not is_1_5:
        s = s + 1
    # If 1-5 already, leave as-is
    if scale == "c":
        return 6 - s  # reverse so 5 = best
    return s


def _leadership_summary(df: pd.DataFrame):
    rows = []
    for col, lab, scale in LEADERSHIP_ITEMS:
        s = _normalize_leadership(df, col, scale)
        n = int(len(s))
        if n == 0:
            rows.append({"item": lab, "n": 0, "mean": None, "sd": None, "agree_pct": None, "disagree_pct": None})
            continue
        agree_n = int((s >= 4).sum())
        rows.append({
            "item": lab,
            "n": n,
            "mean": round(float(s.mean()), 2),
            "sd": round(float(s.std()), 2) if n > 1 else 0.0,
            "agree_pct": round(100 * agree_n / n, 1),
            "disagree_pct": round(100 * (s <= 2).sum() / n, 1),
        })
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_results(df_raw: pd.DataFrame, year) -> dict:
    """Compute the full results dict for a single survey-year DataFrame.

    Mirrors the structure produced by analysis2/analyze2.py's results.json.

    Parameters
    ----------
    df_raw : pd.DataFrame
        A REDCap raw-coded export. Must have the standard 108 columns; missing
        columns are tolerated where possible.
    year : int | str
        Survey year (stored on the returned dict and used by downstream report
        builders).
    """
    df = df_raw.copy()
    # Drop test records (any "this is a test" mention in free text)
    df = _drop_test_records(df)

    # Replace N/A codes
    for c in MINIZ_ITEMS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(9999, np.nan)
    for c in FACTOR_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(8888, np.nan)
    # Numeric coercion for other key columns
    for c in ["clinical", "division", "wellbeingindex", "promoter", "leave",
              "lifeevent", "ftereduce", "gender", "ethnicity", "timevumc", "fte", "ad"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in list(STAY_COLS.keys()) + list(RACE_COLS.keys()):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["GROUP"] = df["clinical"].map({1.0: "Clinical", 0.0: "Research"})
    df["division_label"] = df["division"].map(DIVISION_MAP)

    n_total = int(len(df))
    n_clin = int((df["GROUP"] == "Clinical").sum())
    n_res = int((df["GROUP"] == "Research").sum())

    # Coverage map — which metrics were collected in this year's survey
    coverage = {
        "miniz": all(c in df.columns for c in MINIZ_ITEMS),
        "wellbeing": "wellbeingindex" in df.columns,
        "nps": "promoter" in df.columns,
        "retention": "leave" in df.columns,
        "factors_present": [c for c in FACTOR_LABELS.keys() if c in df.columns],
        "leadership_present": [c for c, _, _ in LEADERSHIP_ITEMS if c in df.columns],
    }

    results = {
        "year": year,
        "sample": {"n_total": n_total, "clinical": n_clin, "research": n_res},
        "coverage": coverage,
    }

    # ---------------- MINI-Z ----------------
    mz = {
        "overall": _miniz_full(df),
        "clinical": _miniz_full(df[df["GROUP"] == "Clinical"]),
        "research": _miniz_full(df[df["GROUP"] == "Research"]),
    }
    mz["by_division"] = []
    for div, g in df.groupby("division_label"):
        if pd.isna(div):
            continue
        s = _miniz_full(g)
        mz["by_division"].append({"division": str(div), "n": int(len(g)),
                                  **{k: v for k, v in s.items() if k != "items"}})
    results["miniz"] = mz

    # ---------------- Well-being ----------------
    wb_res = {
        "overall": _wb(df),
        "clinical": _wb(df[df["GROUP"] == "Clinical"]),
        "research": _wb(df[df["GROUP"] == "Research"]),
    }
    wb_res["by_division"] = []
    for div, g in df.groupby("division_label"):
        if pd.isna(div):
            continue
        s = _wb(g)
        if s:
            wb_res["by_division"].append({"division": str(div), **s})
    wb_res["by_division"].sort(key=lambda x: -x["mean"])
    results["wellbeing"] = wb_res

    # ---------------- NPS ----------------
    nps_res = {
        "overall": _nps(df),
        "clinical": _nps(df[df["GROUP"] == "Clinical"]),
        "research": _nps(df[df["GROUP"] == "Research"]),
    }
    nps_res["by_division"] = []
    for div, g in df.groupby("division_label"):
        if pd.isna(div):
            continue
        s = _nps(g)
        if s:
            nps_res["by_division"].append({"division": str(div), **s})
    nps_res["by_division"].sort(key=lambda x: -x["nps"])
    results["nps"] = nps_res

    # ---------------- Retention ----------------
    ret = {
        "overall": _leave(df),
        "clinical": _leave(df[df["GROUP"] == "Clinical"]),
        "research": _leave(df[df["GROUP"] == "Research"]),
    }
    ret["by_division"] = []
    for div, g in df.groupby("division_label"):
        if pd.isna(div):
            continue
        s = _leave(g)
        if s:
            ret["by_division"].append({"division": str(div), **s})
    ret["by_division"].sort(key=lambda x: -x["at_risk_pct"])

    denom = int(df["leave"].notna().sum()) if "leave" in df.columns else 0
    stay_items = []
    for col, lab in STAY_COLS.items():
        if col in df.columns:
            n = int((df[col] == 1).sum())
        else:
            n = 0
        stay_items.append({"reason": lab, "n": n, "pct": round(100 * n / denom, 1) if denom > 0 else 0})
    stay_items.sort(key=lambda x: -x["n"])
    ret["stay_reasons"] = {"denom": denom, "items": stay_items}

    if "lifeevent" in df.columns:
        le = df["lifeevent"].dropna()
        if len(le) > 0:
            ret["lifeevent"] = {
                "n": int(len(le)),
                "no_n": int((le == 0).sum()),
                "no_pct": round(100 * (le == 0).sum() / len(le), 1),
                "unsure_n": int((le == 1).sum()),
                "unsure_pct": round(100 * (le == 1).sum() / len(le), 1),
                "yes_n": int((le == 2).sum()),
                "yes_pct": round(100 * (le == 2).sum() / len(le), 1),
            }
        else:
            ret["lifeevent"] = {"n": 0, "no_n": 0, "no_pct": 0, "unsure_n": 0,
                                "unsure_pct": 0, "yes_n": 0, "yes_pct": 0}
    else:
        ret["lifeevent"] = {"n": 0, "no_n": 0, "no_pct": 0, "unsure_n": 0,
                            "unsure_pct": 0, "yes_n": 0, "yes_pct": 0}

    # FTE reduce distribution using labels
    if "ftereduce" in df.columns:
        fr = df["ftereduce"].dropna().map(FTEREDUCE_MAP).dropna()
        fr_total = int(len(fr))
        dist = []
        if fr_total > 0:
            for k, v in fr.value_counts().items():
                dist.append({"value": str(k), "n": int(v),
                             "pct": round(100 * v / fr_total, 1)})
        ret["fte_reduce"] = {"n": fr_total, "distribution": dist}
    else:
        ret["fte_reduce"] = {"n": 0, "distribution": []}

    results["retention"] = ret

    # ---------------- Job-satisfaction factors ----------------
    def _factor_summary(sub_df: pd.DataFrame) -> list:
        out = []
        for c, lab in FACTOR_LABELS.items():
            if c not in sub_df.columns:
                out.append({"factor": lab, "n": 0, "mean": None, "raw_mean": None,
                            "net_positive": None, "very_pos_pct": 0, "som_pos_pct": 0,
                            "neutral_pct": 0, "som_neg_pct": 0, "very_neg_pct": 0,
                            "pos_pct": 0, "neg_pct": 0})
                continue
            s = sub_df[c].dropna()
            n = int(len(s))
            if n == 0:
                out.append({"factor": lab, "n": 0, "mean": None, "raw_mean": None,
                            "net_positive": None, "very_pos_pct": 0, "som_pos_pct": 0,
                            "neutral_pct": 0, "som_neg_pct": 0, "very_neg_pct": 0,
                            "pos_pct": 0, "neg_pct": 0})
                continue
            scaled = s - 2
            very_pos = int((s == 4).sum())
            som_pos = int((s == 3).sum())
            neutral = int((s == 2).sum())
            som_neg = int((s == 1).sum())
            very_neg = int((s == 0).sum())
            pos = very_pos + som_pos
            neg = very_neg + som_neg
            out.append({
                "factor": lab,
                "n": n,
                "mean": round(float(scaled.mean()), 2),
                "raw_mean": round(float(s.mean()), 2),
                "net_positive": round(100 * (pos - neg) / n, 1),
                "very_pos_pct": round(100 * very_pos / n, 1),
                "som_pos_pct": round(100 * som_pos / n, 1),
                "neutral_pct": round(100 * neutral / n, 1),
                "som_neg_pct": round(100 * som_neg / n, 1),
                "very_neg_pct": round(100 * very_neg / n, 1),
                "pos_pct": round(100 * pos / n, 1),
                "neg_pct": round(100 * neg / n, 1),
            })
        out.sort(key=lambda x: -(x["mean"] if x["mean"] is not None else -99))
        return out

    # Backward-compat: results["factors"] stays the overall list.
    # New: results["factors_clinical"] / results["factors_research"].
    results["factors"] = _factor_summary(df)
    results["factors_clinical"] = _factor_summary(df[df["GROUP"] == "Clinical"])
    results["factors_research"] = _factor_summary(df[df["GROUP"] == "Research"])

    # ---------------- Leadership ----------------
    ld = {
        "overall": _leadership_summary(df),
        "clinical": _leadership_summary(df[df["GROUP"] == "Clinical"]),
        "research": _leadership_summary(df[df["GROUP"] == "Research"]),
    }
    key_scales = {c: s for c, _, s in LEADERSHIP_ITEMS}
    ld["by_division"] = []
    for div, g in df.groupby("division_label"):
        if pd.isna(div):
            continue
        row = {"division": str(div), "n": int(len(g))}
        for c in KEY_LEADERSHIP:
            s = _normalize_leadership(g, c, key_scales[c])
            row[c + "_mean"] = round(float(s.mean()), 2) if len(s) > 0 else None
            row[c + "_n"] = int(len(s))
            row[c + "_agree_pct"] = round(100 * (s >= 4).sum() / len(s), 1) if len(s) > 0 else None
        ld["by_division"].append(row)
    results["leadership"] = ld

    # ---------------- Demographics ----------------
    demo = {"n_total": n_total, "clinical": n_clin, "research": n_res, "tables": {}}

    def _dist(series: pd.Series, label_map: dict):
        s = series.copy()
        rows = []
        total = int(len(s))
        if total == 0:
            return rows
        # value counts including NaN
        counts = s.value_counts(dropna=False)
        for k, v in counts.items():
            if isinstance(k, float) and np.isnan(k):
                lab = "Missing"
            else:
                lab = label_map.get(int(k) if isinstance(k, (int, float, np.integer, np.floating)) and not (isinstance(k, float) and np.isnan(k)) else k, str(k))
            rows.append({"value": lab, "n": int(v), "pct": round(100 * v / total, 1)})
        return rows

    if "gender" in df.columns:
        demo["tables"]["Gender"] = _dist(df["gender"], GENDER_MAP)
    if "ethnicity" in df.columns:
        demo["tables"]["Ethnicity"] = _dist(df["ethnicity"], ETHNICITY_MAP)
    if "timevumc" in df.columns:
        demo["tables"]["Time at VUMC"] = _dist(df["timevumc"], TIMEVUMC_MAP)
    if "fte" in df.columns:
        demo["tables"]["FTE"] = _dist(df["fte"], FTE_MAP)
    if "ad" in df.columns:
        demo["tables"]["Academic days FY"] = _dist(df["ad"], AD_MAP)
    if "division" in df.columns:
        demo["tables"]["Primary Division"] = _dist(df["division"], DIVISION_MAP)

    # Race (multi-select)
    race_summary = []
    for col, lab in RACE_COLS.items():
        if col in df.columns:
            n = int((df[col] == 1).sum())
            race_summary.append({"value": lab, "n": n,
                                 "pct": round(100 * n / n_total, 1) if n_total > 0 else 0})
    demo["race"] = race_summary

    results["demographics"] = demo
    return results
