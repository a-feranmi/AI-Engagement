from __future__ import annotations
import json
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'artifacts'/'model'/'random_forest.joblib'
DATA=ROOT/'artifacts'/'model_features.csv'
OUT=ROOT/'artifacts'/'risk_drivers.csv'
FEATURES=['behs','performance_health','client_feedback_health','milestone_health','utilisation_health','sentiment_health','behs_delta','performance_health_delta','client_feedback_health_delta','milestone_health_delta','utilisation_health_delta','sentiment_health_delta','technical_score','delivery_score','communication_score','overall_score','feedback_rating','feedback_count','delay_days','delayed_milestones','milestone_count','utilisation','utilisation_delta','engagement_age_months','remaining_months','monthly_contract_value','contract_exposure']
LABELS={'behs':'Engagement health','performance_health':'Performance','client_feedback_health':'Client feedback','milestone_health':'Milestones','utilisation_health':'Utilisation','sentiment_health':'Sentiment','delay_days':'Milestone delay','feedback_rating':'Feedback rating','communication_score':'Communication score','delivery_score':'Delivery score','overall_score':'Overall performance'}

def main():
    model=joblib.load(MODEL); df=pd.read_csv(DATA,parse_dates=['as_of_date']); X=df[FEATURES+['role']]
    rf=model.named_steps['clf']; pre=model.named_steps['pre']
    transformed=pre.transform(X)
    # Model-agnostic global importance from RF is sufficient for MVP; label the top drivers per observation heuristically.
    importances=rf.feature_importances_
    names=list(pre.get_feature_names_out()); imp_map=pd.Series(importances,index=names).sort_values(ascending=False)
    global_top=[]
    for n,v in imp_map.head(12).items():
        raw=n.split('__',1)[-1]
        global_top.append({'feature':raw,'importance':float(v),'label':LABELS.get(raw,raw)})
    (ROOT/'artifacts'/'global_feature_importance.json').write_text(json.dumps(global_top,indent=2))
    # Simple local driver narrative based on direction from portfolio median; good for app explanations.
    rows=[]
    for _,r in df.iterrows():
        drivers=[]
        if r.behs<60: drivers.append(('Engagement health',100-r.behs))
        if r.performance_health<65: drivers.append(('Performance',100-r.performance_health))
        if r.sentiment_health<40: drivers.append(('Sentiment',100-r.sentiment_health))
        if r.delay_days>=5: drivers.append(('Milestone delay',r.delay_days))
        if r.feedback_rating<3.2: drivers.append(('Client feedback',5-r.feedback_rating))
        drivers=sorted(drivers,key=lambda z:z[1],reverse=True)[:3]
        rows.append({'engagement_id':r.engagement_id,'as_of_date':r.as_of_date,'top_drivers':' | '.join(d[0] for d in drivers) if drivers else 'No material driver detected'})
    pd.DataFrame(rows).to_csv(OUT,index=False)
if __name__=='__main__':main()
