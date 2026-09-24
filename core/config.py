"""Central configuration for BredgePulse.

Single source of truth for paths, the database URL, the model feature list and
scoring thresholds. Default DB is a local SQLite file (zero setup); set DB_URL
to a Postgres connection string for cloud / deployment.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "synthetic"
ARTIFACTS = ROOT / "artifacts"
MODEL_DIR = ARTIFACTS / "model"
POWERBI_DIR = ARTIFACTS / "powerbi"
for _d in (ARTIFACTS, MODEL_DIR, POWERBI_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# SQLite by default; override with DB_URL for Postgres (Neon / Supabase).
#   DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/bredgepulse
DB_URL = os.getenv("DB_URL", f"sqlite:///{ARTIFACTS / 'bredgepulse.sqlite'}")

# Model feature list (shared by training, prediction and explainability).
#
# Deliberately EXCLUDED from the model (still computed and shown on dashboards):
#   behs, behs_delta          exact weighted sum of the five health components
#   overall_score             blend of performance, client rating and milestone health
#   delay_days, delayed_milestones   milestone_health is derived from delay days
#   utilisation_health(_delta)       rescaled copy of utilisation
#   contract_exposure         monthly_contract_value x remaining_months
# Keeping mechanically-linked copies of the same signal made Logistic Regression
# assign counter-intuitive signs (more delay -> lower risk) while adding no
# predictive power (ROC-AUC 0.927 with or without them). One representative per
# signal keeps every coefficient's direction interpretable.
FEATURES = [
    "performance_health", "client_feedback_health", "milestone_health", "sentiment_health",
    "performance_health_delta", "client_feedback_health_delta", "milestone_health_delta",
    "sentiment_health_delta",
    "technical_score", "delivery_score", "communication_score",
    "feedback_rating", "feedback_count", "milestone_count",
    "utilisation", "utilisation_delta", "engagement_age_months",
    "remaining_months", "monthly_contract_value",
]
CATEGORICAL = ["role"]
TARGET = "risk_target"

# Business-readable driver groups for model features, used for SHAP risk drivers.
# Related features (a level and its month-on-month change, or several scores of
# the same signal) are summed into one group, so the app reports "Performance"
# rather than four separate performance columns (grouped SHAP). Labels for
# features not in FEATURES are kept so the mapping stays valid if they return.
FEATURE_LABELS = {
    "behs": "Engagement health", "behs_delta": "Engagement health",
    "performance_health": "Performance", "performance_health_delta": "Performance",
    "technical_score": "Performance", "delivery_score": "Performance",
    "overall_score": "Performance",
    # communication_score is one of four performance-review scores; alone it gets a
    # small positive coefficient (overlap with the others), so it is explained as
    # part of the Performance group, whose net direction is correct.
    "communication_score": "Performance",
    "client_feedback_health": "Client feedback", "client_feedback_health_delta": "Client feedback",
    "feedback_rating": "Client feedback", "feedback_count": "Client feedback",
    "sentiment_health": "Sentiment", "sentiment_health_delta": "Sentiment",
    "milestone_health": "Milestone delivery", "milestone_health_delta": "Milestone delivery",
    "delay_days": "Milestone delivery", "delayed_milestones": "Milestone delivery",
    "milestone_count": "Milestone delivery",
    "utilisation_health": "Utilisation", "utilisation_health_delta": "Utilisation",
    "utilisation": "Utilisation", "utilisation_delta": "Utilisation",
    "engagement_age_months": "Contract stage", "remaining_months": "Contract stage",
    "monthly_contract_value": "Contract value", "contract_exposure": "Contract value",
    "role": "Role profile",
}

# Minimum SHAP contribution (log-odds) for a feature group to count as a driver.
DRIVER_MIN_SHAP = 0.15

# Banding thresholds on predicted probability.
WATCH_THRESHOLD = 0.35
CRITICAL_THRESHOLD = 0.65
