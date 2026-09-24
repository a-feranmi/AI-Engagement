"""Prescriptive layer: turn risk + explanations into a recommended action.

Primary path: the engagement's SHAP-ranked risk drivers (see
base/explainability/risk_drivers.py) are mapped, in rank order, to an
intervention playbook, so the recommendation addresses whatever is actually
pushing the model's risk up.

Fallback path: if no SHAP drivers are available (e.g. the engagement is in the
Low band), transparent business rules on the raw signals are used.

Every recommendation is decision support only; a manager reviews and approves.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.config import WATCH_THRESHOLD, CRITICAL_THRESHOLD


@dataclass(frozen=True)
class Recommendation:
    priority: str
    action: str
    reason: str
    owner: str
    due_days: int


# SHAP driver group (core.config.FEATURE_LABELS values) -> playbook entry.
DRIVER_PLAYBOOK: dict[str, tuple[str, str, int]] = {
    "Milestone delivery": ("Project reset", "Delivery Lead", 5),
    "Performance":       ("Performance review", "Talent Manager", 7),
    "Communication":     ("Communication coaching", "Talent Manager", 7),
    "Client feedback":   ("Client alignment", "Account Manager", 7),
    "Sentiment":         ("Client alignment", "Account Manager", 7),
    "Engagement health": ("Engagement review", "Account Manager", 7),
    "Utilisation":       ("Capacity check", "Talent Manager", 7),
    "Contract stage":    ("Scope & contract review", "Account Manager", 14),
    "Contract value":    ("Scope & contract review", "Account Manager", 14),
    "Role profile":      ("Mentoring", "Talent Manager", 14),
}


def _priority(risk_probability: float) -> str:
    if risk_probability >= CRITICAL_THRESHOLD:
        return "High"
    if risk_probability >= WATCH_THRESHOLD:
        return "Medium"
    return "Low"


def parse_drivers(text: str | None) -> list[str]:
    """'Milestone delay | Performance' -> ['Milestone delay', 'Performance']."""
    if not text:
        return []
    return [d.strip() for d in str(text).split("|") if d.strip() in DRIVER_PLAYBOOK]


def recommend(*, risk_probability: float, behs: float, sentiment_health: float,
              performance_health: float, delay_days: float, feedback_rating: float,
              drivers: list[str] | None = None) -> list[Recommendation]:
    priority = _priority(risk_probability)
    recs: list[Recommendation] = []

    # 1) SHAP-driven: one action per distinct playbook entry, in driver rank order.
    for rank, driver in enumerate(drivers or [], 1):
        if driver not in DRIVER_PLAYBOOK:
            continue
        action, owner, due = DRIVER_PLAYBOOK[driver]
        if any(r.action == action for r in recs):
            continue
        recs.append(Recommendation(priority, action,
                                   f"SHAP driver #{rank}: {driver} is raising this engagement's risk.",
                                   owner, due))
    if recs:
        return recs[:3]

    # 2) Rule-based fallback on raw signals.
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
        drivers=parse_drivers(row.get("top_drivers")),
    )
    return "\n".join(f"- {r.action}: {r.reason} (owner={r.owner}, due={r.due_days} days)" for r in recs)
