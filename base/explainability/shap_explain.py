from __future__ import annotations
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import shap

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'artifacts'/'model'/'logistic_regression.joblib'
DATA=ROOT/'artifacts'/'model_features.csv'
OUT=ROOT/'artifacts'/'shap_summary.json'
FEATURES=['behs','performance_health','client_feedback_health','milestone_health','utilisation_health','sentiment_health','behs_delta','performance_health_delta','client_feedback_health_delta','milestone_health_delta','utilisation_health_delta','sentiment_health_delta','technical_score','delivery_score','communication_score','overall_score','feedback_rating','feedback_count','delay_days','delayed_milestones','milestone_count','utilisation','utilisation_delta','engagement_age_months','remaining_months','monthly_contract_value','contract_exposure']


def main():
    model=joblib.load(MODEL)
    df=pd.read_csv(DATA)
    sample=df.sample(min(400,len(df)),random_state=42)
    X=sample[FEATURES+['role']]
    pre=model.named_steps['pre']; clf=model.named_steps['clf']
    Xt=pre.transform(X)
    explainer=shap.LinearExplainer(clf,Xt,feature_perturbation='interventional')
    vals=explainer.shap_values(Xt)
    if isinstance(vals,list): vals=vals[1]
    vals=np.asarray(vals)
    names=list(pre.get_feature_names_out())
    mean_abs=np.abs(vals).mean(axis=0)
    top=sorted([{'feature':n,'mean_abs_shap':float(v)} for n,v in zip(names,mean_abs)],key=lambda x:x['mean_abs_shap'],reverse=True)[:15]
    OUT.write_text(json.dumps({'n_observations':len(sample),'top_features':top},indent=2))
    np.save(ROOT/'artifacts'/'shap_values.npy',vals)
    print('Top SHAP features:')
    print(pd.DataFrame(top).to_string(index=False))
if __name__=='__main__':main()
