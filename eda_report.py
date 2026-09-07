from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
DB=ROOT/'artifacts'/'engagement360.sqlite'
OUT=ROOT/'artifacts'/'eda_report.md'
conn=sqlite3.connect(DB)
q=lambda s: pd.read_sql_query(s,conn)
lines=['# Engagement360 EDA & Business Diagnostic Report','', '## Portfolio overview']
over=q('select count(*) as engagements, avg(monthly_contract_value) as avg_monthly_value, sum(monthly_contract_value) as total_monthly_value from engagements')
lines.append(over.to_markdown(index=False))
health=q('select health_band, count(*) as observations, round(avg(behs),2) as avg_behs from engagement_health group by health_band order by health_band')
lines += ['', '## Engagement health distribution', health.to_markdown(index=False)]
latest=q('select * from v_latest_engagement_health')
lines += ['', f"Latest observations: {len(latest):,}", f"Average BEHS: {latest.beHs.mean() if 'beHs' in latest.columns else latest.behs.mean():.2f}"]
rev=q('select sum(risk_adjusted_exposure) as risk_adjusted_exposure, sum(contract_exposure) as contract_exposure from revenue_exposure')
lines += ['', '## Revenue exposure', rev.to_markdown(index=False)]
risk=q('select risk_band,count(*) as engagements,round(avg(risk_probability),3) as avg_probability from v_latest_risk group by risk_band')
lines += ['', '## Latest model risk', risk.to_markdown(index=False)]
root=q('select issue_category, count(*) as observations from sentiment_scores group by issue_category order by observations desc')
lines += ['', '## Feedback issue taxonomy', root.to_markdown(index=False)]
trend=q('select substr(as_of_date,1,7) as month, round(avg(behs),2) as avg_behs, round(avg(sentiment_health),2) as avg_sentiment_health from engagement_health group by month order by month')
lines += ['', '## Monthly health trend', trend.to_markdown(index=False)]
OUT.write_text('\n'.join(lines))
print(OUT)
