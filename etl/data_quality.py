"""Data-quality profiling + rule-based validity checks (Data Governance: Data Quality).

Two outputs:
  artifacts/data_quality_detail.csv  column-level profile (dtype, null rate, distinct values)
  artifacts/data_quality_rules.csv   one row per business rule: rows checked, rows failed

The rules mirror the CHECK / FOREIGN KEY constraints in database/schema/schema.sql,
so validity is measured against the same definition the database enforces in
production: ranges, allowed values, date logic, cross-field consistency and
referential integrity.


"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from base.scoring.behs import BEHSWeights

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic"
OUT = ROOT / "artifacts" / "data_quality_detail.csv"
RULES_OUT = ROOT / "artifacts" / "data_quality_rules.csv"


def profile() -> pd.DataFrame:
    rows = []
    for f in sorted(DATA.glob("*.csv")):
        df = pd.read_csv(f)
        for col in df.columns:
            rows.append({
                "file": f.name, "column": col, "dtype": str(df[col].dtype),
                "rows": len(df), "null_rate": round(float(df[col].isna().mean()), 4),
                "unique": int(df[col].nunique(dropna=True)),
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    return out


# The grain (natural key) of each table. Uniqueness is measured on the grain:
# engagement_id is SUPPOSED to repeat in a monthly fact table, so checking it
# alone would wrongly penalise correct data.
GRAIN = {
    "clients": ["client_id"],
    "talents": ["talent_id"],
    "engagements": ["engagement_id"],
    "placement_outcomes": ["engagement_id"],
    "performance_reviews": ["engagement_id", "review_date"],
    "client_feedback": ["engagement_id", "feedback_date"],
    "project_milestones": ["engagement_id", "milestone_name"],
    "timesheets": ["engagement_id", "period_start"],
    "checkins": ["engagement_id", "checkin_date"],
    "engagement_health": ["engagement_id", "as_of_date"],
}


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv")


def _dates_ok(s: pd.Series) -> pd.Series:
    """True where the value is missing (nullable) or parses as a date."""
    return s.isna() | pd.to_datetime(s, errors="coerce").notna()


def validity_rules() -> pd.DataFrame:
    clients, talents, eng = _read("clients"), _read("talents"), _read("engagements")
    perf, fb, ms = _read("performance_reviews"), _read("client_feedback"), _read("project_milestones")
    ts, health = _read("timesheets"), _read("engagement_health")
    eng_ids = set(eng.engagement_id)
    w = BEHSWeights()

    checks: list[tuple[str, str, str, pd.Series]] = []

    def add(table, rule, dimension, passed):
        checks.append((table, rule, dimension, pd.Series(passed).fillna(False).astype(bool)))

    # engagements
    start = pd.to_datetime(eng.start_date, errors="coerce")
    end = pd.to_datetime(eng.expected_end_date, errors="coerce")
    add("engagements", "monthly_contract_value >= 0", "range", eng.monthly_contract_value >= 0)
    add("engagements", "expected_end_date >= start_date", "date logic", end >= start)
    add("engagements", "status in {Active, Terminated}", "allowed values", eng.status.isin(["Active", "Terminated"]))
    add("engagements", "client_id exists in clients", "referential", eng.client_id.isin(clients.client_id))
    add("engagements", "talent_id exists in talents", "referential", eng.talent_id.isin(talents.talent_id))
    add("engagements", "dates parse", "format",
        _dates_ok(eng.start_date) & _dates_ok(eng.expected_end_date) & _dates_ok(eng.termination_date))

    # performance reviews
    for c in ["technical_score", "delivery_score", "communication_score", "overall_score"]:
        add("performance_reviews", f"{c} between 0 and 100", "range", perf[c].between(0, 100))
    add("performance_reviews", "engagement_id exists", "referential", perf.engagement_id.isin(eng_ids))

    # client feedback
    add("client_feedback", "rating between 1 and 5", "range", fb.rating.between(1, 5))
    add("client_feedback", "comment is not empty", "completeness", fb.comment.fillna("").str.strip().ne(""))
    add("client_feedback", "engagement_id exists", "referential", fb.engagement_id.isin(eng_ids))

    # milestones
    due = pd.to_datetime(ms.due_date, errors="coerce")
    done = pd.to_datetime(ms.completion_date, errors="coerce")
    add("project_milestones", "delay_days >= 0", "range", ms.delay_days >= 0)
    add("project_milestones", "status in {Completed, Delayed}", "allowed values", ms.status.isin(["Completed", "Delayed"]))
    add("project_milestones", "delay_days = completion_date - due_date", "consistency",
        done.isna() | ((done - due).dt.days.clip(lower=0) == ms.delay_days))
    add("project_milestones", "engagement_id exists", "referential", ms.engagement_id.isin(eng_ids))

    # timesheets
    add("timesheets", "expected_hours > 0", "range", ts.expected_hours > 0)
    add("timesheets", "utilisation_rate between 0 and 1.5", "range", ts.utilisation_rate.between(0, 1.5))
    add("timesheets", "utilisation_rate = actual / expected hours", "consistency",
        np.isclose(ts.actual_hours / ts.expected_hours, ts.utilisation_rate, atol=0.01))
    add("timesheets", "engagement_id exists", "referential", ts.engagement_id.isin(eng_ids))

    # engagement health (BEHS)
    comps = ["performance_health", "client_feedback_health", "milestone_health", "utilisation_health", "sentiment_health"]
    for c in comps + ["behs"]:
        add("engagement_health", f"{c} between 0 and 100", "range", health[c].between(0, 100))
    recomputed = (health.performance_health * w.performance + health.client_feedback_health * w.client_feedback
                  + health.milestone_health * w.milestone + health.utilisation_health * w.utilisation
                  + health.sentiment_health * w.sentiment)
    add("engagement_health", "behs = weighted sum of components", "consistency",
        np.isclose(recomputed, health.behs, atol=0.05))
    add("engagement_health", "health_band in {Healthy, Watch, Critical}", "allowed values",
        health.health_band.isin(["Healthy", "Watch", "Critical"]))
    add("engagement_health", "churn_next_90d in {0, 1}", "allowed values", health.churn_next_90d.isin([0, 1]))

    # uniqueness on each table's grain
    for table, keys in GRAIN.items():
        df = _read(table)
        add(table, f"unique on ({', '.join(keys)})", "uniqueness", ~df.duplicated(keys, keep="first"))

    rows = [{"table": t, "rule": r, "dimension": d, "rows_checked": int(len(p)),
             "rows_failed": int((~p).sum()), "pass_rate": round(float(p.mean()), 4) if len(p) else 1.0}
            for t, r, d, p in checks]
    out = pd.DataFrame(rows)
    out.to_csv(RULES_OUT, index=False)
    return out


if __name__ == "__main__":
    print(profile().head(30).to_string(index=False))
    rules = validity_rules()
    print(f"\nValidity rules: {len(rules)} checked, "
          f"{int((rules.rows_failed > 0).sum())} with failures")
    print(rules.to_string(index=False))
