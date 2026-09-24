# BredgePulse Model Card

## Objective
Predict whether an engagement will terminate early within the next 90 days, using only
information available at or before the prediction date.

## Target
`churn_next_90d` (1 if the engagement terminates within 90 days of the observation month).

## Candidate models
- Logistic Regression: interpretable, selected.
- Random Forest: nonlinear comparison model.

Both run inside one scikit-learn `Pipeline` (median imputation and scaling for numeric
features, one-hot encoding for role) with class weighting for the ~25% positive class.

## Features
19 numeric signals plus role (see `core/config.py::FEATURES`): the four health components
and their month-on-month change, performance-review scores, client rating and feedback
volume, milestone count, utilisation and its change, engagement age, remaining months and
monthly contract value.

**Deliberately excluded** (still computed and shown on dashboards): BEHS and its change
(an exact weighted sum of the components), overall score (a blend of performance, rating
and milestone health), raw delay days and delayed-milestone count (milestone health is
derived from them), utilisation health (a rescaled copy of utilisation) and contract
exposure (value × remaining months).

*Why:* with those mechanically linked copies included, the model assigned "more delay" a
risk-lowering coefficient. Given milestone health, extra delay mathematically implies less
of the hidden deterioration, and the model exploited that. ROC-AUC was the same with or
without them (0.927), so removing them costs nothing and makes every coefficient's
direction interpretable. `tests/test_units.py` fails if a health signal's coefficient
ever turns risk-raising again.

## Evaluation design
**Primary: grouped temporal holdout.** Engagements are ordered by their first observed
month and the newest 25% are held out **as whole engagements**. No engagement appears in
both train and test, which prevents entity leakage while testing on the newest placements.

**Robustness: 5-fold cross-validation grouped by client.** One client has many
engagements, so the selected model is re-fitted with no client in both train and test.
This checks that performance does not depend on having seen a client before.

## Results (synthetic data, threshold 0.35)

| | Recall | Precision | F1 | ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression, temporal holdout | **0.892** | 0.410 | 0.562 | 0.927 |
| Random Forest, temporal holdout | 0.864 | 0.483 | 0.620 | 0.932 |
| Logistic Regression, client-grouped CV | 0.913 ± 0.024 | 0.381 ± 0.045 | 0.536 ± 0.047 | 0.950 ± 0.013 |

Confusion matrix (LR, holdout): 190 of 213 terminating engagement-months caught, 23
missed, 273 false alarms. Raising the threshold to 0.60 keeps recall ≥ 0.80 at 0.53
precision, which is the documented option if false alarms become costly.

Exact values: `artifacts/model/metrics.json`.

## Primary metric
Recall, because a false negative is a missed opportunity to intervene. Precision, F1 and
ROC-AUC are reported alongside it, and the precision cost is stated openly.

## Explainability
Grouped SHAP (`base/explainability/`): the exact LinearExplainer is applied to the
selected model and contributions are summed into business driver groups (Client
feedback, Performance, Sentiment, Milestone delivery, ...). Each Watch or Critical
engagement gets its top three risk-raising drivers, which the prescriptive layer maps,
in rank order, to a playbook action.

## Limitations
The dataset is synthetic; feature relationships are designed for academic demonstration.
Threshold 0.35 is an operational pilot threshold, not a financially validated cut-off.
Model outputs support, not replace, managerial judgment.

## Governance
Every build is notarized into the blockchain-inspired decision ledger
(`core/notarization.py`) with SHA-256 digests of the predictions, metrics and model, and
every intervention logged or closed against a prediction is notarized too. See
`docs/governance.md`.
