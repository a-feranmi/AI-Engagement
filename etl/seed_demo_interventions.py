"""Seed demonstration interventions so the management loop is visible in the app."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.db import read_sql, write_df


def main() -> None:
    latest = read_sql("""
        SELECT engagement_id, as_of_date, risk_probability, risk_band FROM (
            SELECT r.*, ROW_NUMBER() OVER(PARTITION BY engagement_id ORDER BY as_of_date DESC) rn
            FROM risk_predictions r) t
        WHERE rn = 1 ORDER BY risk_probability DESC LIMIT 45
    """)
    rows = []
    for i, r in latest.iterrows():
        status = "Closed" if i % 3 != 0 else "Open"
        rows.append({
            "engagement_id": r["engagement_id"],
            "intervention_date": str(pd.to_datetime(r["as_of_date"]).date()),
            "intervention_type": ["Client alignment", "Project reset", "Performance review",
                                  "Mentoring", "Scope clarification"][i % 5],
            "owner": ["Account Manager", "Talent Manager", "Delivery Lead"][i % 3],
            "priority": "High" if r["risk_probability"] >= 0.65 else "Medium",
            "status": status,
            "due_date": str((pd.to_datetime(r["as_of_date"]) + pd.Timedelta(days=7)).date()),
            "completed_date": str((pd.to_datetime(r["as_of_date"]) + pd.Timedelta(days=5)).date()) if status == "Closed" else None,
            "outcome": "Risk reduced" if status == "Closed" else None,
        })
    write_df(pd.DataFrame(rows), "interventions")
    print(f"Seeded {len(rows)} demonstration interventions")


if __name__ == "__main__":
    main()
