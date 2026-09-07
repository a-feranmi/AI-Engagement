# Engagement360 — Suggested Power BI Measures

Use these measures after importing the `executive_portfolio`, `health_trend`, `revenue_protection`, `root_cause`, and `interventions` exports. Adapt table/column names to the final model.

```DAX
Engagements = DISTINCTCOUNT(executive_portfolio[engagement_id])

Healthy Engagements =
CALCULATE([Engagements], executive_portfolio[health_band] = "Healthy")

Watch Engagements =
CALCULATE([Engagements], executive_portfolio[health_band] = "Watch")

Critical Engagements =
CALCULATE([Engagements], executive_portfolio[risk_band] = "Critical")

Critical % = DIVIDE([Critical Engagements], [Engagements])

Risk Adjusted Exposure = SUM(executive_portfolio[risk_adjusted_exposure])

Contract Exposure = SUM(executive_portfolio[contract_exposure])

Average BEHS = AVERAGE(executive_portfolio[behs])

Average Risk Probability = AVERAGE(executive_portfolio[risk_probability])

Open Interventions =
CALCULATE(COUNTROWS(interventions), interventions[status] = "Open")

Closed Interventions =
CALCULATE(COUNTROWS(interventions), interventions[status] = "Closed")

Risk Reduced Outcomes =
CALCULATE(COUNTROWS(interventions), interventions[outcome] = "Risk reduced")

Intervention Completion Rate =
DIVIDE([Closed Interventions], COUNTROWS(interventions))

Risk Reduction Outcome Rate =
DIVIDE([Risk Reduced Outcomes], [Closed Interventions])
```

## Recommended visual-to-measure mapping

### CEO Executive Cockpit
- KPI cards: Engagements, Critical %, Average BEHS, Risk Adjusted Exposure
- Column chart: health band distribution
- Bar chart: risk-adjusted exposure by client
- Line chart: average BEHS by month
- Table: top 10 critical engagements

### Engagement Health
- Line chart: BEHS and component health scores by month
- Small multiples: performance / sentiment / milestones
- Slicers: client, role, talent, industry, account manager

### Root Cause
- Bar chart: issue category counts
- Stacked bar: issue category by sentiment label
- Matrix: client × issue category

### Revenue Protection
- Waterfall: contract exposure → risk-adjusted exposure
- Bar chart: exposure by client / role
- Table: highest exposure critical engagements

### Intervention Effectiveness
- Cards: open, closed, risk-reduced
- Bar chart: intervention types
- Table: intervention owner, priority, status, outcome
