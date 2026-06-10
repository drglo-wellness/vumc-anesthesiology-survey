# Faculty Survey Analysis Portal — Leadership Pitch

A short reference for the Thursday morning meeting.

## What it is

A password-protected internal web app that wraps the analysis pipeline used
to produce this year's Faculty Engagement & Well-being report. Department
leaders upload the REDCap CSV export and receive:

1. **The polished Word department report** (same one leadership saw for 2026).
2. **Per-division Word reports** — one focused report per division comparing
   that division's numbers to the department average, plus its top/bottom job
   factors and division-specific leadership ratings (for review with the
   Division Chief).
3. **Headline metrics at a glance** — sample size, MINI-Z total, % burnout,
   WBI mean, NPS.
4. **A longitudinal trends dashboard** comparing year-over-year movement for
   MINI-Z, burnout, well-being, and NPS — once two or more years are loaded.

## Why now

The 2026 retreat surfaced clear interest in tracking these indicators over
time. With 2025 and 2026 data available, we can already show direction.
Going forward, a small, self-service tool means the chair and chiefs can
regenerate the report themselves each cycle without waiting on a custom
analysis turnaround.

## What it does well

- **Reproducible**: same scoring (Mini-Z 2.0 per Linzer/InstitutePHI; 5-item
  subscales) every year, so trends are apples-to-apples.
- **Fast**: upload a CSV → 30 seconds later, the Word report is downloadable.
- **No PHI risk**: REDCap exports are anonymous, data is held only in browser
  session memory, never written to disk by the app, never committed to
  the source repository.
- **Cheap**: hosted free on Streamlit Community Cloud (free tier).
- **Maintainable**: ~2,100 lines of Python in 6 files. The analysis logic
  lives in one module (`src/analysis.py`) — any future scoring change happens
  in one place.

## What it doesn't do (yet)

- **PPTX export** — by design. The Word report is the durable deliverable;
  for the faculty meeting, the longitudinal charts can be screenshotted into
  a 4-5 slide deck (or a future version can auto-export Plotly charts as PNGs
  for slide insertion).
- **Persistent storage** — each user uploads each year for each session.
  When SharePoint integration or a department database is desired, the
  upload step can be replaced with a "load from SharePoint" tab.

## What we observed in 2025 → 2026

| Indicator | 2025 | 2026 | Change |
|---|---:|---:|---:|
| Respondents | 136 | 172 | +36 |
| MINI-Z total (clinical) | 34.2 | 34.8 | +0.5 |
| Subscale 1 — Supportive Work Env | 17.5 | 17.9 | +0.4 |
| Subscale 2 — Work Pace / EMR Stress | 16.8 | 16.9 | +0.2 |
| % Burnout (clinical) | 40.7% | 37.2% | **−3.5 pp** |
| % High stress (clinical) | 38.6% | 43.4% | **+4.8 pp** |
| % Job satisfaction (clinical) | 68.4% | 71.7% | +3.3 pp |
| WBI mean (overall) | 6.43 | 6.58 | +0.15 |
| NPS (overall) | −23.5 | −12.2 | **+11.3** |
| Retention risk (% at-risk) | 47.8% | 40.0% | **−7.8 pp** |

**Direction is encouraging on six of nine indicators**, including the two
leadership cares about most — burnout and retention. The single
counter-signal is high stress (+4.8 pp), which may simply reflect more
candor in the survey itself; worth flagging in the 2026 retreat closeout.

## What we'd ask of leadership

1. **Endorse this as the tool for the next survey cycle.** Whoever runs the
   2027 survey simply opens the URL, uploads the REDCap export, and downloads
   the report — no analyst handoff required.
2. **Designate two backup users** (probably the chair's office + one chief).
   Two-person access ensures continuity.
3. **Approve the existing Mini-Z 2.0 scoring** as the canonical scoring (it's
   what the published 2026 report uses).
4. **Decide whether to commission division-level reports** (the analysis
   already computes the numbers; we just need the rendering).

## Cost

$0. Streamlit Community Cloud free tier. No credit-card requirement.
GitHub repository is free (public, but contains no data — only code).
