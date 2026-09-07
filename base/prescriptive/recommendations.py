from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    priority: str
    action: str
    reason: str
    owner: str
    due_days: int


def recommend(*, risk_probability: float, behs: float, sentiment_health: float,
               performance_health: float, delay_days: float, feedback_rating: float) -> list[Recommendation]:
    recs: list[Recommendation] = []
    if risk_probability >= 0.65:
        priority = "High"
    elif risk_probability >= 0.35:
        priority = "Medium"
    else:
        priority = "Low"

    if sentiment_health < 40 or feedback_rating < 3.2:
        recs.append(Recommendation(priority, "Client alignment", "Client sentiment/feedback is deteriorating.", "Account Manager", 7))
    if delay_days >= 5:
        recs.append(Recommendation(priority, "Project reset", "Milestone delay indicates delivery slippage.", "Delivery Lead", 5))
    if performance_health < 65:
        recs.append(Recommendation(priority, "Performance review", "Performance health is below the operating threshold.", "Talent Manager", 7))
    if behs < 60 and not recs:
        recs.append(Recommendation(priority, "Engagement review", "Overall engagement health is in the critical band.", "Account Manager", 7))
    if not recs:
        recs.append(Recommendation(priority, "Continue monitoring", "No major intervention trigger is currently present.", "Account Manager", 14))
    return recs[:3]


def as_prompt_context(row: dict) -> str:
    recs = recommend(
        risk_probability=float(row.get("risk_probability", 0)),
        behs=float(row.get("behs", 0)),
        sentiment_health=float(row.get("sentiment_health", 50)),
        performance_health=float(row.get("performance_health", 70)),
        delay_days=float(row.get("delay_days", 0)),
        feedback_rating=float(row.get("feedback_rating", 4)),
    )
    return "\n".join(f"- {r.action}: {r.reason} (owner={r.owner}, due={r.due_days} days)" for r in recs)
