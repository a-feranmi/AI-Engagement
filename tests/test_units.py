"""Unit tests: scoring, prescriptive logic, governance ledger, data-quality rules,
model directionality. These run without the full build except where noted."""
import json
import shutil
from pathlib import Path

import joblib
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- BEHS
def test_behs_weighted_sum_and_bands():
    from base.scoring.behs import calculate_behs, health_band
    assert calculate_behs(100, 100, 100, 100, 100) == 100
    assert calculate_behs(80, 60, 70, 50, 90) == pytest.approx(0.25*80 + 0.2*60 + 0.2*70 + 0.15*50 + 0.2*90)
    assert health_band(85) == "Healthy" and health_band(70) == "Watch" and health_band(40) == "Critical"
    with pytest.raises(ValueError):
        calculate_behs(120, 50, 50, 50, 50)


# ---------------------------------------------------------------- prescriptive
def test_recommendations_follow_shap_driver_order():
    from base.prescriptive.recommendations import recommend, parse_drivers
    drivers = parse_drivers("Milestone delivery | Client feedback | Performance")
    recs = recommend(risk_probability=0.8, behs=55, sentiment_health=30, performance_health=50,
                     delay_days=8, feedback_rating=2.5, drivers=drivers)
    assert [r.action for r in recs] == ["Project reset", "Client alignment", "Performance review"]
    assert all(r.priority == "High" for r in recs)
    assert "SHAP driver #1" in recs[0].reason


def test_recommendations_fall_back_to_rules_without_drivers():
    from base.prescriptive.recommendations import recommend
    recs = recommend(risk_probability=0.2, behs=90, sentiment_health=80, performance_health=90,
                     delay_days=0, feedback_rating=4.5, drivers=[])
    assert recs[0].action == "Continue monitoring" and recs[0].priority == "Low"


def test_driver_playbook_covers_every_driver_group():
    from core.config import FEATURE_LABELS
    from base.prescriptive.recommendations import DRIVER_PLAYBOOK
    assert set(FEATURE_LABELS.values()) <= set(DRIVER_PLAYBOOK)


# ---------------------------------------------------------------- governance ledger
def test_ledger_detects_tampering():
    from core.db import exec_sql
    from core.notarization import notarize, verify_chain
    for i in range(3):
        notarize("unit_test", f"ENG-{i}", {"i": i})
    assert verify_chain()["ok"]
    exec_sql("UPDATE governance_ledger SET payload=:p WHERE ref_id='ENG-1'", p='{"i":99}')
    result = verify_chain()
    assert not result["ok"] and result["broken_at"] is not None


def test_file_digest_changes_with_content(tmp_path):
    from core.notarization import file_digest
    f = tmp_path / "preds.csv"
    f.write_text("engagement_id,risk\nENG-1,0.40\n")
    before = file_digest(f)
    f.write_text("engagement_id,risk\nENG-1,0.41\n")
    assert file_digest(f) != before


# ---------------------------------------------------------------- data quality
def test_validity_rules_catch_corrupted_rows(tmp_path, monkeypatch):
    import etl.data_quality as dq
    src = ROOT / "data" / "synthetic"
    for f in src.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    fb = pd.read_csv(tmp_path / "client_feedback.csv")
    fb.loc[:4, "rating"] = 9                       # out of range
    fb.to_csv(tmp_path / "client_feedback.csv", index=False)
    eh = pd.read_csv(tmp_path / "engagement_health.csv")
    eh = pd.concat([eh, eh.head(3)])               # duplicate grain rows
    eh.to_csv(tmp_path / "engagement_health.csv", index=False)

    monkeypatch.setattr(dq, "DATA", tmp_path)
    monkeypatch.setattr(dq, "RULES_OUT", tmp_path / "rules.csv")
    rules = dq.validity_rules().set_index("rule")
    assert rules.loc["rating between 1 and 5", "rows_failed"] == 5
    assert rules.loc["unique on (engagement_id, as_of_date)", "rows_failed"] == 3


# ---------------------------------------------------------------- model directionality (needs build)
MODEL = ROOT / "artifacts" / "model" / "logistic_regression.joblib"


@pytest.mark.skipif(not MODEL.exists(), reason="run run_all.py first")
def test_logistic_coefficients_point_the_business_way():
    """Better health signals must never raise predicted risk. Guards against
    re-introducing collinear duplicates that flip coefficient signs."""
    model = joblib.load(MODEL)
    names = [n.split("__", 1)[-1] for n in model.named_steps["pre"].get_feature_names_out()]
    coef = dict(zip(names, model.named_steps["clf"].coef_[0]))
    for feature in ["performance_health", "client_feedback_health", "milestone_health",
                    "sentiment_health", "feedback_rating", "utilisation"]:
        assert coef[feature] < 0, f"{feature} should lower risk, coefficient={coef[feature]:.3f}"


@pytest.mark.skipif(not (ROOT / "artifacts" / "model" / "metrics.json").exists(), reason="run run_all.py first")
def test_robustness_check_recorded():
    m = json.loads((ROOT / "artifacts" / "model" / "metrics.json").read_text())
    assert m["robustness"]["recall"]["mean"] > 0.8
