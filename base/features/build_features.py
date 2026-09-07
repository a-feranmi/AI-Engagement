from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'synthetic'
OUT=ROOT/'artifacts'/'model_features.csv'

def main():
    h=pd.read_csv(DATA/'engagement_health.csv', parse_dates=['as_of_date'])
    e=pd.read_csv(DATA/'engagements.csv', parse_dates=['start_date','expected_end_date','termination_date'])
    p=pd.read_csv(DATA/'performance_reviews.csv', parse_dates=['review_date'])
    f=pd.read_csv(DATA/'client_feedback.csv', parse_dates=['feedback_date'])
    m=pd.read_csv(DATA/'project_milestones.csv', parse_dates=['due_date','completion_date'])
    t=pd.read_csv(DATA/'timesheets.csv', parse_dates=['period_start'])
    o=pd.read_csv(DATA/'placement_outcomes.csv', parse_dates=['outcome_date'])

    h=h.sort_values(['engagement_id','as_of_date']).copy()
    for col in ['behs','performance_health','client_feedback_health','milestone_health','utilisation_health','sentiment_health']:
        h[f'{col}_delta']=h.groupby('engagement_id')[col].diff()
    h['engagement_month']=h['as_of_date'].dt.to_period('M').dt.to_timestamp()

    # Aggregate structured operational signals to the same engagement-month grain.
    p['month']=p['review_date'].dt.to_period('M').dt.to_timestamp()
    p_m=p.groupby(['engagement_id','month'],as_index=False).agg(
        technical_score=('technical_score','mean'),delivery_score=('delivery_score','mean'),communication_score=('communication_score','mean'),overall_score=('overall_score','mean'))
    f['month']=f['feedback_date'].dt.to_period('M').dt.to_timestamp()
    f_m=f.groupby(['engagement_id','month'],as_index=False).agg(feedback_rating=('rating','mean'),feedback_count=('rating','size'))
    m['month']=m['due_date'].dt.to_period('M').dt.to_timestamp()
    m_m=m.groupby(['engagement_id','month'],as_index=False).agg(delay_days=('delay_days','mean'),delayed_milestones=('status',lambda s:(s=='Delayed').sum()),milestone_count=('status','size'))
    t['month']=t['period_start'].dt.to_period('M').dt.to_timestamp()
    t_m=t.groupby(['engagement_id','month'],as_index=False).agg(utilisation=('utilisation_rate','mean'),actual_hours=('actual_hours','sum'),expected_hours=('expected_hours','sum'))

    x=h.merge(e[['engagement_id','client_id','talent_id','role','start_date','expected_end_date','monthly_contract_value']],on='engagement_id',how='left')
    for extra in [p_m,f_m,m_m,t_m]: x=x.merge(extra,left_on=['engagement_id','engagement_month'],right_on=['engagement_id','month'],how='left').drop(columns=['month'],errors='ignore')
    x['engagement_age_months']=((x['as_of_date'].dt.year-x['start_date'].dt.year)*12+(x['as_of_date'].dt.month-x['start_date'].dt.month)).clip(lower=0)
    x['remaining_months']=((x['expected_end_date'].dt.year-x['as_of_date'].dt.year)*12+(x['expected_end_date'].dt.month-x['as_of_date'].dt.month)).clip(lower=0)
    x['contract_exposure']=x['monthly_contract_value']*x['remaining_months']
    x['feedback_rating']=x['feedback_rating'].fillna(x['client_feedback_health']/20)
    x['feedback_count']=x['feedback_count'].fillna(0)
    x['delay_days']=x['delay_days'].fillna(0)
    x['delayed_milestones']=x['delayed_milestones'].fillna(0)
    x['milestone_count']=x['milestone_count'].fillna(1)
    x['utilisation']=x['utilisation'].fillna(x['utilisation_health']/100)
    x['utilisation_delta']=x['utilisation'].groupby(x['engagement_id']).diff()
    x['risk_target']=x['churn_next_90d'].astype(int)

    # Only rows with valid target and all core features; temporal holdout by date.
    feature_cols=['behs','performance_health','client_feedback_health','milestone_health','utilisation_health','sentiment_health',
                  'behs_delta','performance_health_delta','client_feedback_health_delta','milestone_health_delta','utilisation_health_delta','sentiment_health_delta',
                  'technical_score','delivery_score','communication_score','overall_score','feedback_rating','feedback_count','delay_days','delayed_milestones','milestone_count',
                  'utilisation','utilisation_delta','engagement_age_months','remaining_months','monthly_contract_value','contract_exposure']
    x[feature_cols]=x[feature_cols].replace([np.inf,-np.inf],np.nan).fillna(0)
    cols=['engagement_id','as_of_date','client_id','talent_id','role','risk_target']+feature_cols
    x[cols].to_csv(OUT,index=False)
    print(f'Wrote {OUT} rows={len(x)} positives={x.risk_target.mean():.3%}')
if __name__=='__main__':main()
