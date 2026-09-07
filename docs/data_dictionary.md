# Initial Data Dictionary

| Entity | Key fields | Purpose |
|---|---|---|
| clients | client_id, industry, company_size | client context |
| talents | talent_id, role, seniority, experience | talent context |
| engagements | engagement_id, client_id, talent_id, dates, contract value | placement/assignment |
| performance_reviews | technical, delivery, communication, overall | structured performance signals |
| client_feedback | rating, comment, date | client sentiment/experience |
| project_milestones | due, completion, status, delay_days | delivery health |
| timesheets | expected, actual, utilisation | operational signal |
| checkins | date, note | unstructured engagement signal |
| placement_outcomes | outcome_type, successful | supervised target/outcome |
| engagement_health | BEHS components + band | transparent health layer |
| risk_predictions | probability, band, model version | ML output |
| interventions | type, owner, status, outcome | closed-loop action |
| revenue_exposure | exposure, risk-adjusted exposure | executive financial signal |
