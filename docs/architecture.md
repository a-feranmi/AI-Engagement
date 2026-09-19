flowchart LR
  A[Bredge operational sources\nTalent • Client • Engagement • Performance • Feedback • Milestones • Timesheets] --> B[ETL + data quality\nExtract • Validate • Clean • Transform]
  B --> C[(PostgreSQL\nRAW → CORE → ANALYTICS)]
  C --> D[Descriptive & diagnostic analytics\nBEHS • trends • root cause • revenue exposure]
  C --> E[ML / AI\nRisk model • NLP • SHAP • recommendations]
  D --> F[Power BI\nExecutive intelligence]
  E --> F
  E --> G[Streamlit\nOperational decision support]
  F --> H[Management action]
  G --> H
  H --> I[Intervention + outcome]
  I --> C
