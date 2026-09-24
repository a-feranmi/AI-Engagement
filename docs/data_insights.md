# BredgePulse: Business Diagnostic Evidence

> All values below are generated from the synthetic academic dataset and must be labelled
> as such in the MSc presentation. They demonstrate the analytical method; they are not
> claims about Bredge's actual portfolio.

## Portfolio snapshot
- 1,200 engagements across 60 clients in the synthetic portfolio.
- 9,544 engagement-month observations.
- 24.9% of engagements terminated early in the synthetic history.
- Latest portfolio average BEHS: 69.91/100.
- Latest health bands (BEHS): 240 Healthy, 707 Watch, 253 Critical.
- Latest model risk bands: 750 Low, 92 Watch, 358 Critical (37.5% at risk).
- Risk-adjusted revenue exposure: approximately ₦2.46bn.

## Predictive-model evidence
Grouped temporal holdout (newest 25% of engagements held out whole), threshold 0.35:

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Precision | 0.410 | **0.483** |
| Recall | **0.892** | 0.864 |
| F1 | 0.562 | **0.620** |
| ROC-AUC | 0.927 | **0.932** |

Client-grouped 5-fold CV (robustness): recall 0.913 ± 0.024, ROC-AUC 0.950 ± 0.013.

Critical interpretation: Random Forest has stronger precision, F1 and AUC; Logistic
Regression has higher recall and coefficients whose direction can be read directly. For
an early-warning intervention system the latter is preferred, because false negatives are
missed opportunities to intervene.

## Root-cause evidence
1,983 of 9,544 feedback comments express a concern (domain-adapted VADER). Among them the
issue mix is broad and flat: Timeline 276, Availability 253, Communication 252, Delivery
250, Quality 247, Technical skill 244, Client expectation 233, Collaboration 228. No single
issue dominates, which supports continuous multi-signal monitoring over a one-off fix.
Portfolio-wide, the signals that move predicted risk most are client feedback,
performance and sentiment (grouped SHAP). These are diagnostic signals, not causal findings.

## Financial interpretation
Risk-adjusted exposure = remaining contract value × predicted risk probability. This is
an expected-exposure estimate, not a forecast of guaranteed revenue loss.

## Suggested presentation statement
"On the synthetic pilot portfolio, the model places 358 current engagements in the
Critical risk band and quantifies approximately ₦2.46bn in risk-adjusted revenue exposure,
moving management from retrospective issue discovery to prioritised, proactive
intervention."
