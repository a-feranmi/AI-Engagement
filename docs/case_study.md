# Engagement360 — Portfolio Case Study

## Problem
Bredge-inspired placement operations generate multiple engagement-health signals, but those signals are difficult to combine into one timely decision. The strategic gap is therefore not data availability; it is the absence of an integrated predictive engagement-risk capability.

## Strategic intervention
Engagement360 is a governed decision-intelligence platform that moves the operating model from reactive issue discovery to proactive intervention:

**Monitor → Diagnose → Predict → Explain → Recommend → Intervene → Measure**

## Technical architecture
Structured and unstructured operational sources feed a Python ETL pipeline and PostgreSQL-ready data model. The analytics layer calculates the Bredge Engagement Health Score (BEHS), while the ML/AI layer predicts next-90-day deterioration, analyses feedback sentiment/issues, explains model drivers and generates human-reviewed intervention recommendations. Power BI provides executive intelligence; Streamlit provides operational decision support.

## Data science
- Grouped temporal holdout (whole engagements, newest 25%) so no engagement appears in both train and test.
- Logistic Regression baseline versus Random Forest.
- Recall prioritized for early-warning use; threshold 0.35 in the MVP.
- SHAP/global feature importance used to support explanation.
- Leakage controlled by using only information available at prediction time.

## AI
NLP enriches structured signals by extracting sentiment and issue categories from client feedback/check-in notes. Prescriptive recommendations are generated from model outputs and rule-based controls so the prototype remains auditable and human-governed.

## Business value
The executive layer translates predictive risk into **risk-adjusted revenue exposure**:

`remaining contract value × predicted risk probability`

This creates a common language between data science and commercial management without claiming guaranteed revenue loss.

## Portfolio disclaimer
All data in this project are synthetic and generated for academic demonstration using a Bredge-inspired operating model. The metrics illustrate the proposed methodology and are not claims about actual Bredge performance.
