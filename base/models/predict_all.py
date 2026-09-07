"""Score every engagement-month with the selected model -> operational table."""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import ARTIFACTS, MODEL_DIR, FEATURES, CATEGORICAL, WATCH_THRESHOLD, CRITICAL_THRESHOLD

meta = json.loads((MODEL_DIR / "metrics.json").read_text())
selected = meta["selected_model"]
model = joblib.load(MODEL_DIR / f"{selected}.joblib")
df = pd.read_csv(ARTIFACTS / "model_features.csv", parse_dates=["as_of_date"])
p = model.predict_proba(df[FEATURES + CATEGORICAL])[:, 1]
out = df[["engagement_id", "as_of_date"]].copy()
out["risk_probability"] = p
out["risk_band"] = pd.cut(p, [-1, WATCH_THRESHOLD, CRITICAL_THRESHOLD, 1.01],
                          labels=["Low", "Watch", "Critical"]).astype(str)
out["model_name"] = selected.replace("_", " ").title()
out["model_version"] = "v1.0.0"
out.to_csv(MODEL_DIR / "all_predictions.csv", index=False)
print(f"Scored {len(out):,} rows with {selected}")
print(out.groupby("risk_band").size().to_string())
