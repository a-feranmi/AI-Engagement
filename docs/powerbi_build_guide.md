# Engagement360 Power BI Build Guide

Use the CSVs in `artifacts/powerbi/` for the prototype dashboard. The intended production architecture is PostgreSQL -> Power BI; the local SQLite database is the portable fallback for the academic build environment.

## Page 1 — CEO Executive Cockpit
Cards: Engagements, Healthy, Watch, Critical, Risk-adjusted revenue exposure.
Visuals: Health-band distribution; risk trend; exposure by client; top 10 risky engagements.

## Page 2 — Engagement Health
Slicers: client, talent, role, industry.
Visuals: BEHS trend, component trends, engagement detail table.

## Page 3 — Root-Cause Intelligence
Visuals: issue category distribution, sentiment mix, issue category by client, negative-feedback trend.

## Page 4 — Revenue Protection
Visuals: contract exposure vs risk-adjusted exposure, exposure by client, role and account manager, critical exposure table.

## Page 5 — Intervention Effectiveness
Visuals: interventions by type/status, risk-before vs risk-after once outcomes are populated, completion rate and renewal outcomes.

## Design principle
Keep the CEO view readable in 30 seconds. Use conditional formatting for Healthy / Watch / Critical, but make the underlying numeric score available so the visual is not merely traffic-light decoration.
