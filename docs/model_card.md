# Engagement360 Model Card

## Objective
Predict whether an engagement will experience early termination/escalation within the next 90 days using only information available at or before the prediction date.

## Target
`churn_next_90d`

## Candidate models
- Logistic Regression — interpretable baseline.
- Random Forest — nonlinear comparison model.

## Evaluation design
Grouped temporal holdout: engagements are ordered by their first observed month and the most recent 25% are held out **as whole engagements**. No engagement appears in both train and test, which prevents entity leakage while still evaluating on the newest placements (temporal realism).

## Primary metric
Recall is emphasized because a false negative represents a missed opportunity to intervene. Precision/F1/ROC-AUC are reported alongside it.

## Current MVP results
See `artifacts/model/metrics.json` for the exact metrics. These are results on synthetic academic data and are not evidence of performance on real Bredge data.

## Limitations
The dataset is synthetic; feature relationships are designed for academic demonstration. Threshold 0.35 is an operational pilot threshold, not a clinically or financially validated cutoff. Model outputs should support, not replace, managerial judgment.
