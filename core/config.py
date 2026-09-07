"""Central configuration for Engagement360.

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
#   DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/engagement360
DB_URL = os.getenv("DB_URL", f"sqlite:///{ARTIFACTS / 'engagement360.sqlite'}")

# Model feature list (shared by training, prediction and explainability).
FEATURES = [
    "behs", "performance_health", "client_feedback_health", "milestone_health",
    "utilisation_health", "sentiment_health",
    "behs_delta", "performance_health_delta", "client_feedback_health_delta",
    "milestone_health_delta", "utilisation_health_delta", "sentiment_health_delta",
    "technical_score", "delivery_score", "communication_score", "overall_score",
    "feedback_rating", "feedback_count", "delay_days", "delayed_milestones",
    "milestone_count", "utilisation", "utilisation_delta", "engagement_age_months",
    "remaining_months", "monthly_contract_value", "contract_exposure",
]
CATEGORICAL = ["role"]
TARGET = "risk_target"

# Banding thresholds on predicted probability.
WATCH_THRESHOLD = 0.35
CRITICAL_THRESHOLD = 0.65
