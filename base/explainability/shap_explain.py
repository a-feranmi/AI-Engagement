"""Global SHAP explanation for the selected early-warning model.

Writes:
  artifacts/shap_summary.json             top features by mean |SHAP|
  artifacts/global_feature_importance.json the same, grouped into business drivers
  artifacts/shap_values.npy               full SHAP matrix (git-ignored)


"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import ARTIFACTS
from base.explainability.shap_core import (compute_shap, grouped_contributions,
                                           load_features, raw_feature, selected_model_name)


def main() -> None:
    df = load_features()
    vals, names = compute_shap(df)

    mean_abs = np.abs(vals).mean(axis=0)
    # 'feature' keeps the one-hot level (e.g. role_BI Developer); 'raw_feature' is the source column.
    top = sorted(({"feature": n.split("__", 1)[-1], "raw_feature": raw_feature(n), "mean_abs_shap": float(v)}
                  for n, v in zip(names, mean_abs)),
                 key=lambda d: d["mean_abs_shap"], reverse=True)[:15]
    (ARTIFACTS / "shap_summary.json").write_text(json.dumps(
        {"model": selected_model_name(), "n_observations": int(len(df)), "top_features": top}, indent=2))

    groups = grouped_contributions(vals, names).abs().mean().sort_values(ascending=False)
    (ARTIFACTS / "global_feature_importance.json").write_text(json.dumps(
        [{"driver": k, "mean_abs_shap": float(v)} for k, v in groups.items()], indent=2))

    np.save(ARTIFACTS / "shap_values.npy", vals)
    print(f"Top SHAP features ({selected_model_name()}):")
    print(pd.DataFrame(top)[["feature", "mean_abs_shap"]].to_string(index=False))
    print("\nBusiness drivers by mean |SHAP|:")
    print(groups.round(3).to_string())


if __name__ == "__main__":
    main()
