"""Engagement360 - full build. Runs every stage in dependency order.

Runs each stage as a file path (not `python -m ...`), so it does not depend on
package/module resolution or PYTHONPATH quirks (works on Windows out of the box).
Uses the database configured by DB_URL (SQLite by default; set DB_URL for
Postgres). Run:  python run_all.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(ROOT) + os.pathsep + ENV.get("PYTHONPATH", "")

STEPS = [
    ("Generate synthetic data", "data/generate_synthetic.py"),
    ("ETL load", "etl/load.py"),
    ("Data-quality profile", "etl/data_quality.py"),
    ("NLP (VADER) sentiment + issues", "base/nlp/score_feedback.py"),
    ("Feature engineering", "base/features/build_features.py"),
    ("Train + evaluate models", "base/models/train_risk_model.py"),
    ("Score all engagement-months", "base/models/predict_all.py"),
    ("SHAP global explanation", "base/explainability/shap_explain.py"),
    ("Per-engagement risk drivers", "base/explainability/risk_drivers.py"),
    ("Persist model outputs + views", "etl/persist_model_outputs.py"),
    ("Seed demo interventions", "etl/seed_demo_interventions.py"),
    ("Export Power BI CSVs", "etl/export_powerbi.py"),
]

for i, (label, script) in enumerate(STEPS, 1):
    print(f"\n{'='*68}\n[{i}/{len(STEPS)}] {label}\n{'='*68}")
    subprocess.run([sys.executable, script], cwd=str(ROOT), env=ENV, check=True)

print("\nENGAGEMENT360 BUILD COMPLETE - launch the app with:  streamlit run app/app.py")
