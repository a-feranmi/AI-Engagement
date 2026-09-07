from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

INDUSTRIES = ["FinTech", "Banking", "Telecom", "Healthcare", "Retail", "Insurance", "Energy", "Logistics"]
ROLES = ["Data Analyst", "Data Engineer", "Data Scientist", "ML Engineer", "Analytics Engineer", "AI Engineer", "BI Developer"]
SENIORITIES = ["Junior", "Mid", "Senior", "Lead"]
PRIMARY_SKILLS = ["SQL", "Python", "Power BI", "Spark", "AWS", "Azure", "GCP", "Machine Learning", "NLP", "Databricks"]
LOCATIONS = ["Lagos", "Abuja", "Port Harcourt", "Remote", "Accra"]
ISSUES = {
    "COMMUNICATION": ["communication", "updates", "stakeholders", "clarity"],
    "DELIVERY": ["delivery", "deliverables", "output", "implementation"],
    "TECHNICAL_SKILL": ["technical", "quality", "architecture", "code"],
    "QUALITY": ["quality", "defects", "rework", "accuracy"],
    "TIMELINE": ["deadline", "timeline", "delay", "schedule"],
    "COLLABORATION": ["team", "collaboration", "handover", "alignment"],
    "CLIENT_EXPECTATION": ["expectations", "scope", "requirements", "priority"],
    "AVAILABILITY": ["availability", "capacity", "attendance", "response time"],
}

POSITIVE_NOTES = [
    "Delivery remains on track and communication with the client is strong.",
    "The consultant has been responsive and the latest milestone was completed on time.",
    "Client feedback is positive and expectations are well aligned.",
    "The team reports good collaboration and consistent technical quality.",
]
NEGATIVE_TEMPLATES = {
    "COMMUNICATION": "The client raised concerns about communication and inconsistent updates.",
    "DELIVERY": "Several deliverables have required follow-up and delivery has become less predictable.",
    "TECHNICAL_SKILL": "The client noted technical gaps in recent work and requested additional support.",
    "QUALITY": "The quality of recent outputs has declined and additional rework is required.",
    "TIMELINE": "The project has experienced timeline pressure and recent milestones were delayed.",
    "COLLABORATION": "Collaboration has become difficult and the client reported alignment issues.",
    "CLIENT_EXPECTATION": "The client indicated that expectations and delivered scope are no longer fully aligned.",
    "AVAILABILITY": "Availability and response times have become inconsistent for the engagement.",
}


def clamp(x, lo, hi):
    return np.clip(x, lo, hi)


def main(out_dir: Path, n_clients: int = 60, n_talents: int = 500, n_engagements: int = 1200):
    out_dir.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range("2024-01-01", "2026-08-01", freq="MS")

    # -------------------------
    # Master data
    # -------------------------
    clients = pd.DataFrame({
        "client_id": [f"C-{i:04d}" for i in range(1, n_clients + 1)],
        "client_name": [f"Client {i:03d}" for i in range(1, n_clients + 1)],
        "industry": RNG.choice(INDUSTRIES, n_clients),
        "company_size": RNG.choice(["SME", "Mid-Market", "Enterprise"], n_clients, p=[0.25, 0.45, 0.30]),
        "account_manager_id": [f"AM-{RNG.integers(1, 16):03d}" for _ in range(n_clients)],
    })

    talent_roles = RNG.choice(ROLES, n_talents)
    talents = pd.DataFrame({
        "talent_id": [f"T-{i:04d}" for i in range(1, n_talents + 1)],
        "talent_name": [f"Synthetic Talent {i:04d}" for i in range(1, n_talents + 1)],
        "role": talent_roles,
        "seniority": RNG.choice(SENIORITIES, n_talents, p=[0.12, 0.42, 0.35, 0.11]),
        "years_experience": clamp(RNG.normal(5.5, 3.2, n_talents), 0.5, 18).round(1),
        "primary_skill": RNG.choice(PRIMARY_SKILLS, n_talents),
        "location": RNG.choice(LOCATIONS, n_talents),
    })

    # -------------------------
    # Engagements and latent trajectories
    # -------------------------
    eng_rows = []
    perf_rows = []
    fb_rows = []
    milestone_rows = []
    timesheet_rows = []
    checkin_rows = []
    outcome_rows = []
    health_rows = []

    used_talents = RNG.choice(talents.talent_id, n_engagements, replace=True)
    used_clients = RNG.choice(clients.client_id, n_engagements, replace=True)

    for i in range(1, n_engagements + 1):
        engagement_id = f"ENG-{i:05d}"
        client_id = used_clients[i - 1]
        talent_id = used_talents[i - 1]
        start = pd.Timestamp(RNG.choice(dates))
        months = int(RNG.integers(6, 13))
        end = start + pd.DateOffset(months=months)
        monthly_value = float(RNG.choice([900_000, 1_200_000, 1_500_000, 2_000_000, 2_400_000, 3_000_000]) * RNG.uniform(0.85, 1.20))
        baseline_risk = float(RNG.beta(2.2, 6.8))
        # Create three latent trajectory classes, intentionally imbalanced.
        trajectory = RNG.choice(["Healthy", "Watch", "Critical"], p=[0.58, 0.27, 0.15])
        trend = {"Healthy": RNG.normal(0.001, 0.002), "Watch": RNG.normal(-0.020, 0.005), "Critical": RNG.normal(-0.040, 0.008)}[trajectory]
        # Some engagements terminate early. Risk rises nonlinearly for critical journeys.
        early_term_prob = {"Healthy": 0.05, "Watch": 0.35, "Critical": 0.70}[trajectory] + baseline_risk * 0.10
        early_term = RNG.random() < min(0.88, early_term_prob)
        if early_term:
            term_month = int(RNG.integers(max(3, months // 3), max(4, months - 1)))
            termination_date = start + pd.DateOffset(months=term_month)
            if termination_date >= end:
                termination_date = None
                early_term = False
        else:
            termination_date = None

        eng_rows.append({
            "engagement_id": engagement_id,
            "client_id": client_id,
            "talent_id": talent_id,
            "role": talents.loc[talents.talent_id.eq(talent_id), "role"].iloc[0],
            "start_date": start.date(),
            "expected_end_date": end.date(),
            "monthly_contract_value": round(monthly_value, 2),
            "status": "Terminated" if early_term else "Active",
            "termination_date": termination_date.date() if termination_date is not None else None,
            "outcome": "Early Termination" if early_term else ("Renewed" if RNG.random() < 0.62 else "Completed"),
        })

        # Observation months before termination/end.
        obs_end = min(end, termination_date if termination_date is not None else dates.max())
        obs_dates = pd.date_range(start, obs_end, freq="MS")
        prev_behs = []
        for m_idx, dt in enumerate(obs_dates):
            progress = m_idx / max(1, len(obs_dates) - 1)
            # latent deterioration signal
            latent = baseline_risk + trend * m_idx + (0.38 if trajectory == "Critical" else 0.22 if trajectory == "Watch" else -0.02) * progress
            if early_term and termination_date is not None:
                months_to_term = max(0, (termination_date.year - dt.year) * 12 + (termination_date.month - dt.month))
                # Make the final 90-day window materially deteriorate, without using post-outcome information.
                if months_to_term <= 3:
                    latent += (4 - months_to_term) * 0.10
            latent = float(clamp(latent, 0.01, 0.99))
            noise = RNG.normal(0, 3.2)
            performance = float(clamp(86 - latent * 33 + noise, 35, 99))
            client_rating = float(clamp(4.65 - latent * 2.5 + RNG.normal(0, 0.20), 1, 5))
            delay_days = int(max(0, RNG.normal(latent * 9, 3)))
            milestone_health = float(clamp(100 - delay_days * 5 - latent * 16 + RNG.normal(0, 3), 15, 100))
            util = float(clamp(0.78 - latent * 0.16 + RNG.normal(0, 0.05), 0.35, 1.10))
            sentiment = float(clamp(0.45 - latent * 1.1 + RNG.normal(0, 0.12), -1, 1))
            note_issue = None
            if sentiment < -0.10 or latent > 0.42:
                note_issue = RNG.choice(list(ISSUES))
                note = NEGATIVE_TEMPLATES[note_issue]
            else:
                note = RNG.choice(POSITIVE_NOTES)

            overall = float(clamp(0.4 * performance + 0.35 * (client_rating / 5 * 100) + 0.25 * milestone_health, 0, 100))
            perf_rows.append({
                "engagement_id": engagement_id,
                "review_date": dt.date(),
                "technical_score": round(clamp(performance + RNG.normal(0, 4), 0, 100), 2),
                "delivery_score": round(clamp(performance + RNG.normal(0, 5) - delay_days * 0.8, 0, 100), 2),
                "communication_score": round(clamp(performance + RNG.normal(0, 5) + sentiment * 10, 0, 100), 2),
                "overall_score": round(overall, 2),
            })
            fb_rows.append({
                "engagement_id": engagement_id,
                "feedback_date": dt.date(),
                "rating": round(client_rating, 2),
                "comment": note,
            })
            milestone_rows.append({
                "engagement_id": engagement_id,
                "milestone_name": f"Sprint {m_idx + 1}",
                "due_date": (dt + pd.Timedelta(days=20)).date(),
                "completion_date": (dt + pd.Timedelta(days=20 + delay_days)).date(),
                "status": "Delayed" if delay_days > 3 else "Completed",
                "delay_days": delay_days,
            })
            actual_hours = float(clamp(RNG.normal(145 * util, 14), 55, 190))
            timesheet_rows.append({
                "engagement_id": engagement_id,
                "period_start": dt.date(),
                "expected_hours": 160.0,
                "actual_hours": round(actual_hours, 2),
                "utilisation_rate": round(actual_hours / 160.0, 4),
            })
            checkin_rows.append({
                "engagement_id": engagement_id,
                "checkin_date": (dt + pd.Timedelta(days=12)).date(),
                "note": note,
            })

            behs = 0.25 * performance + 0.20 * (client_rating / 5 * 100) + 0.20 * milestone_health + 0.15 * (util * 100) + 0.20 * ((sentiment + 1) / 2 * 100)
            band = "Healthy" if behs >= 80 else "Watch" if behs >= 60 else "Critical"
            health_rows.append({
                "engagement_id": engagement_id,
                "as_of_date": dt.date(),
                "performance_health": round(performance, 2),
                "client_feedback_health": round(client_rating / 5 * 100, 2),
                "milestone_health": round(milestone_health, 2),
                "utilisation_health": round(clamp(util * 100, 0, 100), 2),
                "sentiment_health": round((sentiment + 1) / 2 * 100, 2),
                "behs": round(behs, 2),
                "health_band": band,
            })
            prev_behs.append(behs)

        outcome_rows.append({
            "engagement_id": engagement_id,
            "outcome_date": (termination_date if termination_date is not None else end).date(),
            "outcome_type": "Early Termination" if early_term else ("Renewed" if eng_rows[-1]["outcome"] == "Renewed" else "Completed"),
            "successful": not early_term,
        })

    engagements = pd.DataFrame(eng_rows)
    performance = pd.DataFrame(perf_rows)
    feedback = pd.DataFrame(fb_rows)
    milestones = pd.DataFrame(milestone_rows)
    timesheets = pd.DataFrame(timesheet_rows)
    checkins = pd.DataFrame(checkin_rows)
    outcomes = pd.DataFrame(outcome_rows)
    health = pd.DataFrame(health_rows)

    # Make outcomes + monthly prediction labels for modelling.
    outcomes = outcomes.merge(engagements[["engagement_id", "termination_date"]], on="engagement_id", how="left")
    health = health.merge(outcomes[["engagement_id", "termination_date"]], on="engagement_id", how="left")
    health["termination_date"] = pd.to_datetime(health["termination_date"])
    health["as_of_date"] = pd.to_datetime(health["as_of_date"])
    health["days_to_termination"] = (health["termination_date"] - health["as_of_date"]).dt.days
    health["churn_next_90d"] = ((health["days_to_termination"] >= 0) & (health["days_to_termination"] <= 90)).astype(int)
    health.drop(columns=["termination_date", "days_to_termination"], inplace=True)

    # Ensure the latest observation has a financially useful risk proxy for the MVP.
    latest = health.sort_values("as_of_date").groupby("engagement_id").tail(1).copy()
    latest = latest.merge(engagements[["engagement_id", "monthly_contract_value", "expected_end_date"]], on="engagement_id", how="left")
    latest["as_of_date"] = pd.to_datetime(latest["as_of_date"])
    latest["expected_end_date"] = pd.to_datetime(latest["expected_end_date"])
    latest["remaining_months"] = ((latest["expected_end_date"].dt.year - latest["as_of_date"].dt.year) * 12 + (latest["expected_end_date"].dt.month - latest["as_of_date"].dt.month)).clip(lower=0)
    latest["contract_exposure"] = latest["monthly_contract_value"] * latest["remaining_months"]
    # Current prototype exposure uses BEHS-derived risk; the ML model will replace this after Day 6.
    latest["heuristic_risk_probability"] = clamp(1 - latest["behs"] / 100, 0.02, 0.95)
    latest["risk_adjusted_exposure"] = latest["contract_exposure"] * latest["heuristic_risk_probability"]

    # Drop helper columns before raw outputs.
    outcomes.drop(columns=["termination_date"], inplace=True)

    for frame, name in [
        (clients, "clients.csv"),
        (talents, "talents.csv"),
        (engagements, "engagements.csv"),
        (performance, "performance_reviews.csv"),
        (feedback, "client_feedback.csv"),
        (milestones, "project_milestones.csv"),
        (timesheets, "timesheets.csv"),
        (checkins, "checkins.csv"),
        (outcomes, "placement_outcomes.csv"),
        (health, "engagement_health.csv"),
        (latest, "latest_exposure.csv"),
    ]:
        frame.to_csv(out_dir / name, index=False)

    # Manifest with dataset facts for reproducibility.
    summary = {
        "clients": len(clients),
        "talents": len(talents),
        "engagements": len(engagements),
        "engagement_months": len(health),
        "performance_reviews": len(performance),
        "client_feedback": len(feedback),
        "milestones": len(milestones),
        "timesheets": len(timesheets),
        "checkins": len(checkins),
        "early_termination_rate": round((engagements["outcome"] == "Early Termination").mean(), 4),
        "churn_next_90d_rate": round(health["churn_next_90d"].mean(), 4),
        "latest_risk_adjusted_exposure": round(latest["risk_adjusted_exposure"].sum(), 2),
        "latest_behs_mean": round(latest["behs"].mean(), 2),
    }
    pd.Series(summary).to_json(out_dir / "manifest.json", indent=2)
    print(pd.Series(summary).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(Path(__file__).parent / "synthetic"))
    args = parser.parse_args()
    main(Path(args.out_dir))
