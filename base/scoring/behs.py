"""Bredge Engagement Health Score (BEHS).

Weights are management-defined MVP weights and are not presented as empirically
validated causal weights.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class BEHSWeights:
    performance: float = 0.25
    client_feedback: float = 0.20
    milestone: float = 0.20
    utilisation: float = 0.15
    sentiment: float = 0.20


def calculate_behs(
    performance: float,
    client_feedback: float,
    milestone: float,
    utilisation: float,
    sentiment: float,
    weights: BEHSWeights = BEHSWeights(),
) -> float:
    """Return BEHS on a 0–100 scale."""
    values = [performance, client_feedback, milestone, utilisation, sentiment]
    if any(v < 0 or v > 100 for v in values):
        raise ValueError("All BEHS components must be between 0 and 100")
    score = (
        performance * weights.performance
        + client_feedback * weights.client_feedback
        + milestone * weights.milestone
        + utilisation * weights.utilisation
        + sentiment * weights.sentiment
    )
    return round(score, 2)


def health_band(behs: float) -> str:
    if not 0 <= behs <= 100:
        raise ValueError("BEHS must be between 0 and 100")
    if behs >= 80:
        return "Healthy"
    if behs >= 60:
        return "Watch"
    return "Critical"
