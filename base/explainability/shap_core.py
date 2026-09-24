"""Shared SHAP computation for the selected early-warning model.

Both the global summary (shap_explain.py) and the per-engagement risk drivers
(risk_drivers.py) come from this one function, so the app, the dashboard and
the slides all describe the same model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import ARTIFACTS, MODEL_DIR, FEATURES, CATEGORICAL, FEATURE_LABELS


def selected_model_name() -> str:
    return json.loads((MODEL_DIR / "metrics.json").read_text())["selected_model"]


def load_features() -> pd.DataFrame:
    return pd.read_csv(ARTIFACTS / "model_features.csv", parse_dates=["as_of_date"])


def raw_feature(transformed_name: str) -> str:
    """'num__delay_days' -> 'delay_days';  'cat__role_BI Developer' -> 'role'."""
    name = transformed_name.split("__", 1)[-1]
    for cat in CATEGORICAL:
        if name.startswith(cat + "_"):
            return cat
    return name


def compute_shap(df: pd.DataFrame, background_size: int = 400) -> tuple[np.ndarray, list[str]]:
    """SHAP values (log-odds contribution to risk) for every row of df.

    Returns (values [n_rows x n_transformed_features], transformed feature names).
    Logistic Regression uses the exact LinearExplainer; a tree model falls back
    to TreeExplainer.
    """
    name = selected_model_name()
    model = joblib.load(MODEL_DIR / f"{name}.joblib")
    pre, clf = model.named_steps["pre"], model.named_steps["clf"]
    X = pre.transform(df[FEATURES + CATEGORICAL])
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
    bg = X[np.random.default_rng(42).choice(len(X), min(background_size, len(X)), replace=False)]

    if name == "logistic_regression":
        explainer = shap.LinearExplainer(clf, bg)
        vals = explainer.shap_values(X)
    else:
        explainer = shap.TreeExplainer(clf, bg)
        vals = explainer.shap_values(X)
        if isinstance(vals, list):
            vals = vals[1]
        elif np.ndim(vals) == 3:
            vals = vals[:, :, 1]
    return np.asarray(vals), list(pre.get_feature_names_out())


def grouped_contributions(vals: np.ndarray, names: list[str]) -> pd.DataFrame:
    """Sum SHAP values into business-readable driver groups (FEATURE_LABELS)."""
    labels = [FEATURE_LABELS.get(raw_feature(n), raw_feature(n)) for n in names]
    frame = pd.DataFrame(vals, columns=names)
    return frame.T.groupby(labels, sort=False).sum().T
