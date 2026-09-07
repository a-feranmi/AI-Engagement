"""ETL — Load (unified, DB-agnostic).

Loads every synthetic CSV into the configured database (SQLite or Postgres)
through the shared engine, and writes a data-quality summary. Replaces the old
sqlite-only build_local_db.py and the separate load_postgres.py — one path now.

Run:  python -m etl.load
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import DATA_DIR, ARTIFACTS
from core.db import write_df, dialect

SOURCE = {
    "clients": "clients.csv", "talents": "talents.csv",
    "engagements": "engagements.csv", "performance_reviews": "performance_reviews.csv",
    "client_feedback": "client_feedback.csv", "project_milestones": "project_milestones.csv",
    "timesheets": "timesheets.csv", "checkins": "checkins.csv",
    "placement_outcomes": "placement_outcomes.csv", "engagement_health": "engagement_health.csv",
}


def main() -> None:
    print(f"Loading into {dialect()} database")
    quality = []
    for table, fname in SOURCE.items():
        df = pd.read_csv(DATA_DIR / fname)
        write_df(df, table)
        quality.append({
            "table": table, "rows": len(df), "columns": df.shape[1],
            "null_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        })
        print(f"  {table:<22} {len(df):>7,} rows")
    qdf = pd.DataFrame(quality)
    qdf.to_csv(ARTIFACTS / "data_quality_report.csv", index=False)
    print("\nData-quality summary:")
    print(qdf.to_string(index=False))


if __name__ == "__main__":
    main()
