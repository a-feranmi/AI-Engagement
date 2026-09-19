"""Data Quality Scorecard, Data Governance applied.

Turns the column-level profiling already produced by etl/data_quality.py
into the four dimensions taught in the Data Quality session: completeness,
validity, uniqueness and freshness. This is deliberately built on top of the
existing profile (no new pipeline step), governance should formalise work
already being done, not duplicate it.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DETAIL = ROOT / "artifacts" / "data_quality_detail.csv"
DATA = ROOT / "data" / "synthetic"

KEY_COLUMNS = ["engagement_id", "client_id", "talent_id", "as_of_date", "monthly_contract_value"]


def scorecard() -> dict:
    """Return {'completeness':.., 'validity':.., 'uniqueness':.., 'freshness':..} in [0,1]."""
    if not DETAIL.exists():
        raise FileNotFoundError("Run etl/data_quality.py (part of run_all.py) before requesting a scorecard.")
    det = pd.read_csv(DETAIL)

    completeness = 1.0 - float(det["null_rate"].mean())

    # Uniqueness is only meaningful for each file's own grain / primary key —
    # a foreign key (e.g. client_id repeated across many engagements) is
    # SUPPOSED to repeat, so scoring it here would wrongly penalise the data.
    # Heuristic: per file, the "_id" column with the most distinct values is
    # that file's own primary key; only that column is checked for uniqueness.
    id_cols = det[det["column"].str.endswith("_id")]
    if len(id_cols):
        pk_per_file = id_cols.loc[id_cols.groupby("file")["unique"].idxmax()]
        uniqueness = float((pk_per_file["unique"] / pk_per_file["rows"]).clip(upper=1.0).mean())
    else:
        uniqueness = 1.0

    key_present = det[det["column"].isin(KEY_COLUMNS)]
    validity = 1.0 - float(key_present["null_rate"].mean()) if len(key_present) else completeness

    newest_mtime = 0.0
    for f in DATA.glob("*.csv"):
        newest_mtime = max(newest_mtime, f.stat().st_mtime)
    age_days = (datetime.now().timestamp() - newest_mtime) / 86400 if newest_mtime else 999.0
    freshness = max(0.0, 1.0 - age_days / 30.0)

    return {
        "completeness": round(completeness, 4),
        "validity": round(validity, 4),
        "uniqueness": round(uniqueness, 4),
        "freshness": round(freshness, 4),
    }


def grade(value: float) -> str:
    return "A" if value >= 0.98 else "B" if value >= 0.90 else "C"


if __name__ == "__main__":
    for dim, val in scorecard().items():
        print(f"{dim:12s} {val*100:5.1f}%   grade {grade(val)}")
