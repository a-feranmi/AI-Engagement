# Modelling contract

Target: `churn_next_90d`.

Primary comparison:
- Logistic Regression — interpretable baseline
- Random Forest — nonlinear comparison model

Headline metric: recall, because false negatives represent missed intervention opportunities.
Report precision, recall, F1, ROC-AUC and confusion matrix.

Temporal rule: each feature row must only use information available on or before its prediction date.
