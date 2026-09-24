"""Per-engagement risk drivers, ranked by SHAP.

For every engagement-month, SHAP values from the selected model are grouped
into business drivers (Milestone delay, Sentiment, Performance, ...). The top
three drivers that push risk UP (contribution >= DRIVER_MIN_SHAP log-odds) are
written as the narrative the app shows and the recommendation engine uses.
Drivers are only reported when the model places the engagement in the Watch or
Critical band; a low-risk engagement gets "No material driver detected".


"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import ARTIFACTS, MODEL_DIR, DRIVER_MIN_SHAP, WATCH_THRESHOLD
from base.explainability.shap_core import compute_shap, grouped_contributions, load_features

NO_DRIVER = "No material driver detected"


def main() -> None:
    df = load_features()
    vals, names = compute_shap(df)
    groups = grouped_contributions(vals, names)
    preds = pd.read_csv(MODEL_DIR / "all_predictions.csv", parse_dates=["as_of_date"])
    prob = df[["engagement_id", "as_of_date"]].merge(
        preds[["engagement_id", "as_of_date", "risk_probability"]],
        on=["engagement_id", "as_of_date"], how="left")["risk_probability"].fillna(0).to_numpy()

    top_drivers, details = [], []
    for i, (_, contrib) in enumerate(groups.iterrows()):
        if prob[i] < WATCH_THRESHOLD:
            top_drivers.append(NO_DRIVER)
            details.append("")
            continue
        up = contrib[contrib >= DRIVER_MIN_SHAP].sort_values(ascending=False).head(3)
        top_drivers.append(" | ".join(up.index) if len(up) else NO_DRIVER)
        details.append(" | ".join(f"{k} (+{v:.2f})" for k, v in up.items()) if len(up) else "")

    out = pd.DataFrame({"engagement_id": df["engagement_id"], "as_of_date": df["as_of_date"],
                        "top_drivers": top_drivers, "top_driver_detail": details})
    out.to_csv(ARTIFACTS / "risk_drivers.csv", index=False)
    has = out.top_drivers.ne(NO_DRIVER)
    print(f"SHAP drivers written for {len(out):,} rows ({has.mean():.1%} with a material driver)")
    print(out.loc[has, "top_drivers"].str.split(" \\| ").str[0].value_counts().head(8).to_string())


if __name__ == "__main__":
    main()
