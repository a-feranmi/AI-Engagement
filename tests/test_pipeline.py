from pathlib import Path
import json
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "artifacts" / "engagement360.sqlite"


def test_core_tables_have_rows():
    conn = sqlite3.connect(DB)
    for table in ["clients", "talents", "engagements", "engagement_health", "risk_predictions"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert n > 0
    conn.close()


def test_prediction_probabilities_are_bounded():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT risk_probability FROM risk_predictions", conn)
    conn.close()
    assert df.risk_probability.between(0, 1).all()


def test_revenue_exposure_non_negative():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT contract_exposure, risk_adjusted_exposure FROM revenue_exposure", conn)
    conn.close()
    assert (df >= 0).all().all()


def test_model_metrics_exist():
    metrics = json.loads((ROOT / "artifacts" / "model" / "metrics.json").read_text())
    assert metrics["selected_model"] in metrics["results"]
    assert metrics["results"][metrics["selected_model"]]["recall"] > 0.5
