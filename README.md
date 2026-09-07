# Engagement360
### AI-Powered Engagement Health, Early-Warning & Revenue Protection Platform — Bredge LLC
*MSc Data Science Management — strategic intervention & portfolio project*

**The gap:** Bredge places talent with clients, but a placement's health is invisible until the
client terminates the contract — a lagging, too-late signal. Fragmented engagement, performance,
milestone, utilisation and client-sentiment data never becomes one timely decision.

**The intervention:** Engagement360 joins those signals into one governed platform that
**monitors → predicts → explains → recommends → measures**, flags every placement
**Healthy / Watch / Critical**, and quantifies the **Revenue-at-Risk (₦)** attached to each —
60–90 days before a likely termination.

> Data is fully synthetic and Bredge-inspired. No confidential client data is used.

---

## Architecture

```
Synthetic sources → ETL load + data quality → DATABASE (SQLite local / Postgres cloud)
   → BEHS health score → NLP (VADER sentiment + issue taxonomy) → temporal-safe features
   → risk model (Logistic Regression + Random Forest) → SHAP + risk drivers
   → scoring + Revenue-at-Risk + prescriptive actions
   → analytics views → Power BI exports  +  Streamlit app (monitor → investigate → intervene)
```

One database layer (`core/db.py`) means the **same code runs on SQLite locally and Postgres in the
cloud** — you switch by setting `DB_URL`, nothing else changes.

---

## Project structure

```
engagement360/
├── core/                     config + one DB engine (SQLite/Postgres)
│   ├── config.py             paths, DB_URL, feature list, thresholds
│   └── db.py                 read_sql / exec_sql / write_df / create_views
├── data/
│   ├── generate_synthetic.py latent-trajectory synthetic data generator
│   └── synthetic/            generated CSVs
├── database/
│   ├── schema/schema.sql     Postgres DDL (reference)
│   └── marts/                analytics views (Postgres + SQLite)
├── etl/
│   ├── load.py               CSV → DB (DB-agnostic)
│   ├── data_quality.py       profiling report
│   ├── persist_model_outputs.py  risk_predictions, revenue_exposure, views
│   ├── seed_demo_interventions.py
│   └── export_powerbi.py     one CSV per Power BI page
├── base/
│   ├── scoring/behs.py       Bredge Engagement Health Score (management metric)
│   ├── nlp/score_feedback.py VADER sentiment + issue taxonomy
│   ├── features/build_features.py  temporal-safe feature table
│   ├── models/               train_risk_model.py, predict_all.py
│   ├── explainability/       shap_explain.py, risk_drivers.py
│   └── prescriptive/recommendations.py  human-reviewed next actions
├── app/app.py                Streamlit operational app
├── docs/                     business case, methodology, model card, Power BI guides, exam mapping
├── tests/                    pytest checks
├── run_all.py                one-command full build
├── requirements.txt · .env.example · Makefile · docker-compose.yml
```

---

## Quickstart (SQLite — zero setup)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_all.py            # generate → load → nlp → features → train → score → export
streamlit run app/app.py     # open the app
```

`run_all.py` builds everything into a local SQLite file at `artifacts/engagement360.sqlite`.

---

## Deploy to the cloud (public portfolio app)

1. **Create a free Postgres** on **Neon** or **Supabase**; copy the connection string.
2. `cp .env.example .env` and set:
   ```
   DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/engagement360
   ```
3. `python run_all.py` — the whole pipeline now builds directly in Postgres.
4. **Power BI:** connect to the same Postgres (or import the CSVs in `artifacts/powerbi/`).
5. **Streamlit Community Cloud:** deploy `app/app.py`, set `DB_URL` as a secret → public URL for
   your portfolio site. (No code change — the app reads whatever `DB_URL` points to.)

> Public-app note: the app can write interventions to the DB. For a public demo, consider a
> read-only DB role or a periodic reset so visitors can't accumulate rows.

---

## Modelling choices (for the write-up / viva)

- **Grouped temporal holdout** — engagements are ordered by first observed month and the newest 25%
  are held out *whole*, so no engagement is in both train and test (prevents entity leakage) while
  testing on the most recent placements. See `artifacts/model/metrics.json`.
- **Recall-first** — a missed at-risk engagement (false negative) is a lost intervention, costlier
  than a false alarm. Metrics report an operating threshold that reaches ≥80% recall and the
  precision paid for it. The precision–recall trade-off is stated, not hidden.
- **Temporal-leakage prevention** — features use only information available up to the prediction
  month; the target (`churn_next_90d`) looks forward.
- **BEHS** — a transparent, management-defined health score (weights are MVP assumptions, not
  empirically proven weights) that sits alongside the ML model.
- **NLP** — VADER sentiment (self-contained, deploy-safe) plus a keyword issue taxonomy for
  root-cause diagnostics.
- **Revenue-at-Risk** = `contract_value × remaining_months × risk_probability` — an expected
  exposure estimate, not a claim the money will be lost.
- **Human-in-the-loop** — the model detects, explains and recommends; a manager reviews and
  approves every intervention, which is logged for the outcome loop.

Run tests with `PYTHONPATH=. pytest tests/`.
