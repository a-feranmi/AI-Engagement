# Mapping

| Required assessment area | BredgePulse evidence |
|---|---|
| 1. Executive Summary | Strategic gap, intervention, expected business value |
| 2. Strategic Approach | Descriptive -> Diagnostic -> Predictive -> Prescriptive; CRISP-DM |
| 3. Data/Business Gap & Root Cause | Five gaps; Fishbone; 5 Whys; EDA |
| 4. Data Science, AI & Innovation | BEHS; churn_next_90d model; NLP; SHAP; prescriptive AI |
| 5. Implementation & Change | 12-month Q1-Q4 roadmap; ADKAR; implementation governance |
| 6. Stakeholders, Performance & Impact | CEO/AM/Talent/Data stakeholders; business/model/data KPIs; revenue exposure |
| 7. Conclusion & Recommendations | Pilot approval; integrated data foundation; human-governed AI intervention |

## Programme modules evidenced (October 2025 calendar)

"Implemented" means running code in this repository. "Roadmap" means designed and
documented in `docs/architecture.md`, not built.

| Calendar module | Evidence | Status |
|---|---|---|
| Business Strategy; Project & Operations Management | Analytics maturity ladder, 12-month roadmap, three CEO decisions | Slides |
| Research Methodology | 5 Whys, root-cause analysis, grouped temporal holdout, client-grouped CV | Implemented |
| Fundamentals of Data Science; Data Driven Companies | End-to-end pipeline `run_all.py`; reactive → predictive → prescriptive | Implemented |
| Data Mining; Machine Learning | Feature engineering, Logistic Regression vs Random Forest, leakage control, multicollinearity treatment | Implemented |
| Advanced & Predictive Analytics | 90-day early-warning model, SHAP drivers, prescriptive playbook, model-based what-if | Implemented |
| Text Detection & Recognition; NLP | Domain-adapted VADER sentiment, issue taxonomy on concern comments | Implemented |
| Cloud Solutions | Streamlit Community Cloud app, Neon PostgreSQL, Power BI Service | Implemented |
| R and Python; Libraries for Data Science | Python: pandas, NumPy, scikit-learn, SHAP, VADER, SQLAlchemy, Plotly, Streamlit | Implemented |
| Jupyter Notebook; Anaconda & Google Colab | `notebooks/01_bredgepulse_walkthrough.ipynb` with an Open-in-Colab badge | Implemented |
| MongoDB & NoSQL; Distributed Architectures; Hadoop/Hive/Spark; Elasticsearch; Kafka; InfluxDB | Production scale-out path | Roadmap |
| Neural Networks, LLM & Modern AI | Human-reviewed LLM summarisation of check-in notes | Roadmap |
| Data Management & Visualization; Data Presentation (Power BI) | Five-page Power BI report, Streamlit dashboards, notebook charts | Implemented |
| Ethics, IP & Data Protection | Synthetic data, role-based access, AM sees own clients only | Implemented |
| Data Quality | 41 rule-based checks + four-dimension scorecard | Implemented |
| Data Notarization (Blockchain) | SHA-256 hash-chain ledger with artifact digests | Implemented |
| Agile Scrum | Quarterly releases delivered in two-week sprints | Plan |

## Critical wording
Use **risk-adjusted revenue exposure** or **Revenue-at-Risk estimate**, not guaranteed revenue loss. The model is trained and evaluated on a synthetic academic dataset; results are not claims about actual Bredge performance.
