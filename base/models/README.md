# Modelling contract

Target: `churn_next_90d`.

Primary comparison:
- Logistic Regression — interpretable baseline
- Random Forest — nonlinear comparison model

Headline metric: recall, because false negatives represent missed intervention opportunities.
Report precision, recall, F1, ROC-AUC and confusion matrix.

Temporal rule: each feature row must only use information available on or before its prediction date.

Feature rule: one representative per signal. Composite or derived columns (BEHS, overall
score, raw delay next to milestone health, utilisation health, contract exposure) are
excluded from the model so coefficient directions stay interpretable; see
`docs/model_card.md`.

Robustness: the selected model is re-fitted under 5-fold cross-validation grouped by
client, reported in `metrics.json` under `robustness`.
