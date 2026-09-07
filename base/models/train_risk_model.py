"""Data Science — Model Training & Evaluation.

Predicts churn_next_90d (early termination within the next 90 days). Trains an
interpretable baseline (Logistic Regression) and the main model (Random Forest)
inside a proper sklearn Pipeline (impute + scale numerics, one-hot the role).

Split: GROUPED TEMPORAL HOLDOUT. Engagements are ordered by their first observed
month and the most recent 25% are held out *whole* — so no engagement appears in
both train and test (prevents entity leakage) while still testing on the newest
placements (temporal realism). Recall is the headline metric: a missed at-risk
engagement (false negative) is a lost intervention opportunity.

Run:  python -m src.models.train_risk_model
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import (ARTIFACTS, MODEL_DIR, FEATURES, CATEGORICAL, TARGET,
                         WATCH_THRESHOLD, CRITICAL_THRESHOLD)

THRESHOLD = WATCH_THRESHOLD


def _metrics(y, p, thr=THRESHOLD):
    pred = (p >= thr).astype(int)
    return {
        "precision": round(precision_score(y, pred, zero_division=0), 3),
        "recall": round(recall_score(y, pred, zero_division=0), 3),
        "f1": round(f1_score(y, pred, zero_division=0), 3),
        "roc_auc": round(roc_auc_score(y, p), 3),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def _grouped_temporal_split(df: pd.DataFrame, test_frac=0.25):
    """Hold out the newest 25% of engagements (by first observed month), whole."""
    firsts = df.groupby("engagement_id")["as_of_date"].min().sort_values()
    n_test = int(len(firsts) * test_frac)
    test_ids = set(firsts.tail(n_test).index)
    is_test = df["engagement_id"].isin(test_ids)
    return df[~is_test].copy(), df[is_test].copy()


def main() -> None:
    df = pd.read_csv(ARTIFACTS / "model_features.csv", parse_dates=["as_of_date"])
    train, test = _grouped_temporal_split(df)
    Xtr, ytr = train[FEATURES + CATEGORICAL], train[TARGET]
    Xte, yte = test[FEATURES + CATEGORICAL], test[TARGET]

    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), FEATURES),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL),
    ])
    models = {
        "logistic_regression": Pipeline([
            ("pre", pre), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))]),
        "random_forest": Pipeline([
            ("pre", pre), ("clf", RandomForestClassifier(
                n_estimators=300, max_depth=10, min_samples_leaf=15,
                class_weight="balanced_subsample", random_state=42, n_jobs=-1))]),
    }

    results = {}
    for name, model in models.items():
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        results[name] = _metrics(yte, p)
        joblib.dump(model, MODEL_DIR / f"{name}.joblib")
        band = pd.cut(p, [-1, THRESHOLD, CRITICAL_THRESHOLD, 1.01],
                      labels=["Low", "Watch", "Critical"])
        pd.DataFrame({"engagement_id": test.engagement_id, "as_of_date": test.as_of_date,
                      "risk_probability": p, "risk_band": band}).to_csv(
            MODEL_DIR / f"{name}_predictions.csv", index=False)

    # Select on recall, tie-break F1.
    best = max(results, key=lambda k: (results[k]["recall"], results[k]["f1"]))

    # Operating threshold for >=0.80 recall on the chosen model (trade-off view).
    p_best = joblib.load(MODEL_DIR / f"{best}.joblib").predict_proba(Xte)[:, 1]
    op_thr, op_prec = None, None
    for thr in np.linspace(0.05, 0.9, 86):
        if recall_score(yte, (p_best >= thr).astype(int)) >= 0.80:
            op_thr, op_prec = round(float(thr), 3), round(
                float(precision_score(yte, (p_best >= thr).astype(int), zero_division=0)), 3)
    meta = {
        "split_method": "grouped_temporal_holdout_newest_25pct_by_engagement",
        "train_rows": len(train), "test_rows": len(test),
        "train_engagements": train.engagement_id.nunique(),
        "test_engagements": test.engagement_id.nunique(),
        "band_threshold": THRESHOLD, "results": results, "selected_model": best,
        "operating_threshold_for_80pct_recall": op_thr,
        "precision_at_that_threshold": op_prec,
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({"selected_model": best, "metrics": results[best],
                      "op_threshold_80_recall": op_thr,
                      "precision_there": op_prec}, indent=2))


if __name__ == "__main__":
    main()
