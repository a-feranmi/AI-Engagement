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
- **ETL & data quality:** A load pipeline with completeness, validity, uniqueness and
  freshness profiling.
- **BEHS:** A transparent, management-defined engagement health score.
- **NLP:** VADER sentiment plus a keyword issue-taxonomy classifier for diagnostics.
- **Feature engineering:** A temporally safe feature table (features use only information
  available at prediction time; the target looks forward 90 days).
- **Risk model:** Logistic Regression and Random Forest, compared and evaluated on a
  grouped temporal holdout, with a recall-first operating point.
- **Explainability:** SHAP global importance and per-engagement risk drivers.
- **Analytics marts & Power BI exports:** Views and flat exports feeding five dashboard
  pages (executive cockpit, engagement health, root cause, revenue protection,
  intervention effectiveness).
- **Streamlit application:** An operational workspace to monitor the portfolio,
  investigate an engagement, simulate what-if scenarios, and log interventions.

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
(explainability) · **Power BI** · **Streamlit** · **Git / GitHub**.

---

## Results

On a grouped temporal holdout, the newest 25% of engagements held out whole, so no
engagement appears in both training and test; the early-warning model reaches strong
recall with a clearly stated precision–recall trade-off. **Recall is prioritised**: a
missed at-risk engagement (a false negative) is a lost intervention opportunity and costs
more than an occasional false alarm. Current metrics are recorded in
`artifacts/model/metrics.json`; the primary model catches the large majority of at-risk
engagements at an operating threshold chosen for that goal.

The AI is decision support only; the model detects, explains and recommends, and a human
manager reviews and approves every intervention.

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
├── docs/            business case, methodology, model card, Power BI guides, exam mapping
├── tests/           automated checks
└── run_all.py       one-command full build
```

---

## Data governance

- **Data quality scorecard:** The existing completeness/validity/uniqueness/
  freshness profiling, graded and shown live in the app.
- **Blockchain-inspired decision notarization:** Every model run, intervention
  and outcome is SHA-256 hash-chained to the record before it. A **Verify chain
  integrity** button in the app recomputes the whole chain on demand and
  reports the exact record where tampering or corruption occurred, if any.
- **Ethics, IP & data protection:** Synthetic data only, role-based access.
- **Agile Scrum delivery:** The 12-month roadmap runs as four quarterly
  sprints, each closing with a review against pilot KPIs.

See `docs/governance.md` for the full write-up, including the honest
limitations of the hash-chain approach.

---

## Data & confidentiality

The dataset is synthetic and generated for academic demonstration using a Bredge-inspired
operating model. It contains no confidential Bredge or client information; realism of the
*patterns* (deteriorating engagements leading to churn) matters more than scale.