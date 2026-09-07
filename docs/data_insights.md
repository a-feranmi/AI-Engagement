# Engagement360 — Business Diagnostic Evidence

> All values below are generated from the synthetic academic dataset and must be labelled as such in the MSc presentation. They demonstrate the analytical method; they are not claims about Bredge's actual portfolio.

## Portfolio snapshot
- 1,200 engagements in the synthetic portfolio.
- 9,544 engagement-month observations.
- 24.9% of engagements have an early-termination outcome in the synthetic history.
- Latest portfolio average BEHS: 69.91/100.
- Latest health bands: 240 Healthy, 707 Watch, 253 Critical.
- Latest model risk bands: 748 Low, 89 Watch, 363 Critical.
- Latest model risk-adjusted revenue exposure: approximately ₦2.45bn.

## Predictive-model evidence
The holdout is the most recent 25% of engagements, held out whole so no engagement leaks across the split. The primary early-warning model is selected on recall (see artifacts/model/metrics.json), because the project prioritises catching at-risk engagements over avoiding false alarms:

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Precision | 0.398 | 0.593 |
| Recall | **0.903** | 0.849 |
| F1 | 0.552 | **0.699** |
| ROC-AUC | 0.944 | **0.952** |

Critical interpretation: Random Forest has stronger precision/F1/AUC, while Logistic Regression has higher recall. For an early-warning intervention system, the latter is deliberately preferred because false negatives represent missed opportunities to intervene. Threshold = 0.35 for the MVP.

## Root-cause evidence
Among negative feedback records, the largest issue categories are Timeline, Availability, Communication, Quality and Technical Skill. The categories are diagnostic signals, not causal findings.

## Financial interpretation
Risk-adjusted exposure is calculated as remaining contract value multiplied by predicted risk probability. This is an expected-exposure estimate; it is not a forecast of guaranteed revenue loss.

## Suggested presentation statement
“On the synthetic pilot portfolio, the model identifies 363 latest engagements in the Critical risk band and approximately ₦2.45bn in risk-adjusted revenue exposure. This demonstrates how engagement-risk analytics can move management from retrospective issue discovery to prioritised proactive intervention.”
