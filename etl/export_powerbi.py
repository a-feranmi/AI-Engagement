"""Export flat CSVs (one per Power BI page) from the analytics views."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import ARTIFACTS, MODEL_DIR, POWERBI_DIR
from core.db import read_sql

QUERIES = {
    "executive_portfolio": """
        SELECT h.engagement_id, h.as_of_date, h.behs, h.health_band, e.client_id,
               c.client_name, c.industry, e.talent_id, e.role, e.monthly_contract_value,
               r.risk_probability, r.risk_band, x.contract_exposure, x.risk_adjusted_exposure
        FROM v_latest_engagement_health h
        JOIN engagements e ON e.engagement_id = h.engagement_id
        JOIN clients c ON c.client_id = e.client_id
        LEFT JOIN v_latest_risk r ON r.engagement_id = h.engagement_id
        LEFT JOIN revenue_exposure x ON x.engagement_id = h.engagement_id""",
    "health_trend": "SELECT * FROM engagement_health",
    "root_cause": """SELECT issue_category, sentiment_label, COUNT(*) AS observations,
                     AVG(sentiment_score) AS avg_sentiment FROM sentiment_scores
                     GROUP BY issue_category, sentiment_label""",
    "revenue_protection": "SELECT * FROM v_revenue_protection",
    "interventions": "SELECT * FROM interventions",
}


def main() -> None:
    for name, q in QUERIES.items():
        read_sql(q).to_csv(POWERBI_DIR / f"{name}.csv", index=False)
    meta = json.loads((MODEL_DIR / "metrics.json").read_text())
    pd.DataFrame([{"model": m, **{k: v for k, v in vals.items() if k != "confusion_matrix"}}
                  for m, vals in meta["results"].items()]).to_csv(
        POWERBI_DIR / "model_metrics.csv", index=False)
    print(f"Exports written to {POWERBI_DIR}")


if __name__ == "__main__":
    main()
