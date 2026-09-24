# BredgePulse
### Engagement Health, Early-Warning & Revenue Protection Platform
*Bredge LLC · MSc Data Science Management; strategic intervention & portfolio project*

**Live demo:**  [Web app](https://bredgepulse.streamlit.app/)  ·  [Power BI dashboard](https://app.powerbi.com/view?r=eyJrIjoiYWVmOGZhOTMtZTY0YS00MmYyLTlkZTctN2VjNGQ5YjQ3ZTEzIiwidCI6IjE0NWVhMmM0LTQ0NWYtNDdhOC05N2E3LWQ4MjdhYjk4ZTE0ZCJ9)


> All data is fully synthetic and Bredge-inspired. No confidential client data is used.

**Access:** the web app is role-gated (Administrator, Account Manager, Guest). If you'd like to explore it as an Administrator or Account Manager, reach out to me at **ample.oluwaferanmi26@gmail.com** for credentials.

---

## Overview

Bredge LLC places data and technology talent with client organisations. But once a
consultant is deployed, the **health of that placement is largely invisible** to the
business; Bredge typically only learns an engagement is failing when the client
terminates the contract. By then the recurring revenue is already lost, the consultant
is unexpectedly on the bench, and the client relationship is damaged.

The underlying problem is not a lack of data. Bredge has performance reviews, client
feedback, project milestones, timesheets, check-in notes and contract information, but
these signals live apart and never combine into a single, timely decision.

**BredgePulse** closes that gap. It integrates those fragmented signals into one
governed decision-intelligence platform that detects deteriorating engagements early,
explains *why* they are at risk, recommends a human-reviewed intervention, and quantifies
the financial exposure attached to the risk turning placement management from a
**reactive** process into a **predictive and prescriptive** one.

```
DATA  →  INSIGHT  →  PREDICTION  →  EXPLANATION  →  ACTION  →  OUTCOME
```

---

## What it does

BredgePulse delivers a complete management cycle:

- **Health monitoring:** A transparent Bredge Engagement Health Score (BEHS) bands every
  active placement as Healthy, Watch or Critical.
- **Early-warning prediction:** A machine-learning model estimates the probability that an
  engagement will terminate early within the next 90 days.
- **Root-cause intelligence:** NLP over client feedback surfaces the drivers behind the
  risk (communication, delivery, timeline, quality, expectations, and so on).
- **Prescriptive recommendation:** Each at-risk engagement receives a recommended next
  action with an owner and a time window, for a manager to review and approve.
- **Revenue protection:** Risk is translated into a **Revenue-at-Risk (₦)** figure so
  leadership sees financial exposure, not just counts.
- **Intervention tracking:** Actions and their outcomes are logged, closing the loop and
  feeding future learning.

---

## What was built

An end-to-end, reproducible platform:

- **Synthetic data engine:** Generates a realistic Bredge-inspired dataset (clients,
  talents, engagements and ~9.5k monthly signal records) with latent health trajectories
  that drive correlated signals and outcomes.
- **Database:** A relational schema (core entities → monthly signals → analytics layer)
  that runs on **SQLite locally and PostgreSQL in the cloud** through one database layer.
- **ETL & data quality:** A load pipeline plus 41 rule-based checks (ranges, allowed
  values, date logic, cross-field consistency, referential integrity, uniqueness on each
  table's grain) rolled up into a completeness / validity / uniqueness / freshness
  scorecard.
- **BEHS:** A transparent, management-defined engagement health score.
- **NLP:** VADER sentiment, domain-adapted with delivery-risk vocabulary, plus a keyword
  issue taxonomy applied only to comments that express a concern.
- **Feature engineering:** A temporally safe feature table (features use only information
  available at prediction time; the target looks forward 90 days).
- **Risk model:** Logistic Regression and Random Forest, compared and evaluated on a
  grouped temporal holdout, with a recall-first operating point, and re-checked with
  client-grouped cross-validation. Composite and duplicate features are excluded so
  every coefficient points the business way.
- **Explainability:** Grouped SHAP. Global driver importance, plus each at-risk
  engagement's top three drivers, which feed the prescriptive recommendations.
- **Analytics marts & Power BI exports:** Views and flat exports feeding five dashboard
  pages (executive cockpit, engagement health, root cause, revenue protection,
  intervention effectiveness).
- **Streamlit application:** An operational workspace to monitor the portfolio,
  investigate an engagement, re-score what-if scenarios with the live model, and log
  interventions.
- **Jupyter walkthrough:** `notebooks/01_bredgepulse_walkthrough.ipynb` runs the
  analysis end to end from the committed artifacts, in Jupyter, Anaconda or Google Colab.

---

## Architecture

```
                         SYNTHETIC BREDGE SOURCES
     performance · client feedback · milestones · timesheets · check-in notes · contracts
                                   │
                                   ▼
                    ETL LOAD  +  DATA-QUALITY PROFILING
                                   │
                                   ▼
              DATABASE  (SQLite local  /  PostgreSQL cloud)
              core entities → monthly signals → analytics layer
                                   │
              ┌────────────────────┴─────────────────────┐
              ▼                                           ▼
     ANALYTICS & SCORING                          AI / ML LAYER
     • BEHS health score                          • risk model (LogReg + RandomForest)
     • descriptive / diagnostic                   • NLP sentiment + issue taxonomy
     • Revenue-at-Risk                            • SHAP + per-engagement drivers
              └────────────────────┬─────────────────────┘
                                   ▼
                   ANALYTICS VIEWS (marts)
              ┌────────────────────┴─────────────────────┐
              ▼                                           ▼
     POWER BI  (5 pages)                        STREAMLIT APP
     executive · health · root cause ·          monitor → investigate →
     revenue protection · interventions         recommend → intervene → measure
                                   │
                                   ▼
                 INTERVENTION & OUTCOME LOG → continuous learning
```

A single database layer means the same code runs locally on SQLite and in the cloud on
PostgreSQL; the environment is selected by configuration alone.

---

## Tech stack

**Python** · **PostgreSQL / SQLite** (SQLAlchemy) · **pandas / NumPy** ·
**scikit-learn** (Logistic Regression, Random Forest) · **VADER** (NLP) · **SHAP**
(explainability) · **Plotly / Matplotlib** · **Power BI** · **Streamlit** ·
**Jupyter / Google Colab** · **pytest** · **Git / GitHub**.

---

## Results

Grouped temporal holdout: the newest 25% of engagements are held out whole, so no
engagement appears in both training and test. At the 0.35 intervention threshold:

| Model | Recall | Precision | F1 | ROC-AUC |
|---|---:|---:|---:|---:|
| **Logistic Regression (selected)** | **0.892** | 0.410 | 0.562 | 0.927 |
| Random Forest | 0.864 | 0.483 | 0.620 | 0.932 |

**Recall is prioritised**: a missed at-risk engagement (a false negative) is a lost
intervention opportunity and costs more than an occasional false alarm.

*Robustness:* re-fitted under 5-fold cross-validation grouped by client (no client in
both train and test), recall is 0.913 ± 0.024 and ROC-AUC 0.950 ± 0.013.

*Interpretability:* BEHS, overall score, raw delay days (milestone health is derived
from them) and utilisation health are kept for dashboards but excluded from the model.
With those mechanically linked copies included, "more delay" received a risk-lowering
coefficient and ROC-AUC was unchanged. A test (`tests/test_units.py`) now guards
coefficient directions.

Risk-adjusted revenue exposure across the portfolio: **₦2.46bn**. Exact figures are in
`artifacts/model/metrics.json` and `artifacts/output_summary.json`.

The AI is decision support only; the model detects, explains and recommends, and a human
manager reviews and approves every intervention.

## Run it locally

```bash
pip install -r requirements.txt
python run_all.py            # full build on local SQLite (leave DB_URL unset)
streamlit run app/app.py
python -m pytest tests -q    # tests always use a throw-away SQLite database
```

Set `DB_URL` (see `.env.example`) to build into PostgreSQL instead. A full build
**replaces** the tables in that database.

---

## Project structure

```
BredgePulse/
├── core/            configuration + one database engine (SQLite / Postgres)
├── data/            synthetic data generator + generated CSVs
├── database/        schema + analytics marts (views)
├── etl/             load, data quality, model persistence, Power BI export
├── base/            scoring (BEHS) · nlp · features · models · explainability · prescriptive
├── app/             Streamlit operational application
├── docs/            business case, methodology, model card, governance, architecture, exam mapping
├── notebooks/       Jupyter / Colab analytical walkthrough
├── tests/           automated checks (pytest)
└── run_all.py       one-command full build
```

---

## Data governance

- **Data quality scorecard:** 41 rule-based checks rolled up into completeness,
  validity, uniqueness and freshness, graded and shown live in the app with the
  per-rule results.
- **Blockchain-inspired decision notarization:** Every model run, intervention
  and outcome is SHA-256 hash-chained to the record before it. Each model run
  also records SHA-256 digests of the prediction file, metrics and model, so a
  change to any single prediction is detectable. A **Verify chain
  integrity** button in the app recomputes the whole chain on demand and
  reports the exact record where tampering or corruption occurred, if any.
- **Ethics, IP & data protection:** Synthetic data only, role-based access.
- **Agile Scrum delivery:** The 12-month roadmap runs as four quarterly
  releases, each delivered through two-week sprints and closing with a release
  review against pilot KPIs.

See `docs/governance.md` for the full write-up, including the honest
limitations of the hash-chain approach.

---

## Data & confidentiality

The dataset is synthetic and generated for academic demonstration using a Bredge-inspired
operating model. It contains no confidential Bredge or client information; realism of the
*patterns* (deteriorating engagements leading to churn) matters more than scale.