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
RULES = ROOT / "artifacts" / "data_quality_rules.csv"
DATA = ROOT / "data" / "synthetic"

KEY_COLUMNS = ["engagement_id", "client_id", "talent_id", "as_of_date", "monthly_contract_value"]


def scorecard() -> dict:
    """Return {'completeness':.., 'validity':.., 'uniqueness':.., 'freshness':..} in [0,1]."""
    if not DETAIL.exists():
        raise FileNotFoundError("Run etl/data_quality.py (part of run_all.py) before requesting a scorecard.")
    det = pd.read_csv(DETAIL)

    completeness = 1.0 - float(det["null_rate"].mean())

    rules = pd.read_csv(RULES) if RULES.exists() else None

    # Uniqueness: duplicates measured on each table's grain (natural key), see
    # etl/data_quality.py::GRAIN. A foreign key such as engagement_id repeating
    # across months is correct, so it is never scored on its own.
    if rules is not None and (rules["dimension"] == "uniqueness").any():
        u = rules[rules["dimension"] == "uniqueness"]
        uniqueness = 1.0 - float(u["rows_failed"].sum() / u["rows_checked"].sum())
    else:
        id_cols = det[det["column"].str.endswith("_id")]
        pk_per_file = id_cols.loc[id_cols.groupby("file")["unique"].idxmax()] if len(id_cols) else id_cols
        uniqueness = float((pk_per_file["unique"] / pk_per_file["rows"]).clip(upper=1.0).mean()) if len(id_cols) else 1.0

    # Validity: share of row-level rule checks passed (ranges, allowed values,
    # date logic, cross-field consistency, referential integrity); see
    # etl/data_quality.py::validity_rules. Falls back to key-column presence
    # only if the rules file has not been generated yet.
    if rules is not None:
        v = rules[rules["dimension"] != "uniqueness"]
        checked = v["rows_checked"].sum()
        validity = 1.0 - float(v["rows_failed"].sum() / checked) if checked else 1.0
    else:
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


def rule_results() -> pd.DataFrame:
    """Per-rule validity results for display (empty if not generated yet)."""
    return pd.read_csv(RULES) if RULES.exists() else pd.DataFrame()


def grade(value: float) -> str:
    return "A" if value >= 0.98 else "B" if value >= 0.90 else "C"


if __name__ == "__main__":
    for dim, val in scorecard().items():
        print(f"{dim:12s} {val*100:5.1f}%   grade {grade(val)}")
