"""Persist model outputs to the DB: risk_predictions, revenue_exposure,
sentiment_scores, risk_drivers; then (re)build the analytics views.

Run:  python -m etl.persist_model_outputs
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import ARTIFACTS, MODEL_DIR, WATCH_THRESHOLD, CRITICAL_THRESHOLD
from core.db import read_sql, write_df, create_views


def main() -> None:
    preds = pd.read_csv(MODEL_DIR / "all_predictions.csv", parse_dates=["as_of_date"])
    preds["risk_band"] = pd.cut(
        preds["risk_probability"], [-1, WATCH_THRESHOLD, CRITICAL_THRESHOLD, 1.01],
        labels=["Low", "Watch", "Critical"]).astype(str)
    write_df(preds[["engagement_id", "as_of_date", "risk_probability", "risk_band",
                    "model_name", "model_version"]], "risk_predictions")

    eng = read_sql("SELECT engagement_id, monthly_contract_value, expected_end_date FROM engagements")
    latest = preds.sort_values("as_of_date").groupby("engagement_id").tail(1).merge(eng, on="engagement_id", how="left")
    latest["as_of_date"] = pd.to_datetime(latest["as_of_date"])
    latest["expected_end_date"] = pd.to_datetime(latest["expected_end_date"])
    latest["remaining_months"] = ((latest.expected_end_date.dt.year - latest.as_of_date.dt.year) * 12 +
                                  (latest.expected_end_date.dt.month - latest.as_of_date.dt.month)).clip(lower=0)
    latest["contract_exposure"] = latest.monthly_contract_value * latest.remaining_months
    latest["risk_adjusted_exposure"] = latest.contract_exposure * latest.risk_probability
    write_df(latest[["engagement_id", "as_of_date", "monthly_contract_value", "remaining_months",
                     "contract_exposure", "risk_probability", "risk_adjusted_exposure"]], "revenue_exposure")

    sent = ARTIFACTS / "sentiment_scores.csv"
    if sent.exists():
        write_df(pd.read_csv(sent), "sentiment_scores")
    drivers = ARTIFACTS / "risk_drivers.csv"
    if drivers.exists():
        write_df(pd.read_csv(drivers), "risk_drivers")

    create_views()
    summary = {
        "risk_predictions": len(preds),
        "revenue_rows": len(latest),
        "risk_adjusted_exposure_total": float(latest.risk_adjusted_exposure.sum()),
        "critical_predictions": int((preds.risk_band == "Critical").sum()),
    }
    (ARTIFACTS / "output_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
