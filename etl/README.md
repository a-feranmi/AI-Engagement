# ETL

Scripts run in this order from `run_all.py`:

| Step | Script | What it does |
|---|---|---|
| Load | `load.py` | Loads every synthetic CSV into the database set by `DB_URL` (SQLite by default, PostgreSQL in the cloud) and writes `artifacts/data_quality_report.csv`. |
| Data quality | `data_quality.py` | Column profile (`data_quality_detail.csv`) plus 41 rule-based checks (`data_quality_rules.csv`): ranges, allowed values, date logic, cross-field consistency, referential integrity, uniqueness on each table's grain. Feeds `core/data_quality_scorecard.py`. |
| Persist | `persist_model_outputs.py` | Writes predictions, revenue exposure, sentiment and SHAP drivers to the database, rebuilds the analytics views and notarizes the build with artifact digests. |
| Seed | `seed_demo_interventions.py` | Seeds 45 demonstration interventions so the management loop is visible. |
| Export | `export_powerbi.py` | Flat CSVs for the Power BI report (`artifacts/powerbi/`). |

Rules mirror the CHECK and FOREIGN KEY constraints in `database/schema/schema.sql`.
