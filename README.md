# VUMC Anesthesiology Faculty Survey — Streamlit Portal

A web app that wraps the existing analysis pipeline for the Department of
Anesthesiology's Faculty Engagement & Well-being Survey. Survey leaders can
upload a REDCap raw-data CSV export and instantly:

1. Generate the polished department Word report (.docx).
2. View a longitudinal trends dashboard once two or more years are loaded.

## What the app does

- Drops the test record (any response with "this is a test" in the free-text
  fields).
- Computes MINI-Z 2.0 subscales (Q1+Q2+Q3+Q4+Q9 and Q5+Q6+Q7+Q8+Q10) plus the
  10-item total, with the joyful (≥40) and highly-supportive / reasonable-pace
  (≥20) thresholds.
- Computes burnout (Q2 ≤ 3), high-stress (Q5 ≤ 2), and job-satisfaction
  (Q1 ≥ 4) prevalences.
- Computes the Well-being Index (0–10 bands), NPS, retention (3-year horizon),
  job factors (−2…+2 rescaled), and leadership ratings (1–5 normalized).
- Generates 10 PNG charts and embeds them in the Word report.

## Local development

```bash
cd faculty_survey_app
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. You'll be prompted for the app password — set it
via `.streamlit/secrets.toml`:

```toml
app_password = "your-password-here"
```

## Deploying to Streamlit Community Cloud

See **DEPLOYMENT.md** for a step-by-step walk-through aimed at a non-developer
audience.

## Project layout

```
faculty_survey_app/
├── app.py                    # Streamlit entrypoint
├── src/
│   ├── __init__.py
│   ├── analysis.py           # compute_results(df_raw, year)
│   ├── chart_builder.py      # generate_charts(results, output_dir)
│   ├── longitudinal.py       # render_longitudinal_view(results_by_year)
│   └── report_builder.py     # build_report(results, charts_dir, year, output)
├── .streamlit/
│   └── config.toml           # light theme
├── requirements.txt
├── README.md
└── DEPLOYMENT.md
```

## Privacy / security notes

- REDCap survey responses are anonymous — there are no patient or
  identifiable-faculty fields produced by the pipeline.
- The app is password-gated; the password is stored in Streamlit Cloud's
  encrypted secrets store, not in the GitHub repository.
- Uploaded CSVs live only in the running Streamlit session memory — they are
  not persisted to disk between sessions.
