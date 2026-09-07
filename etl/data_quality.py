from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'synthetic'
OUT=ROOT/'artifacts'/'data_quality_detail.csv'

def profile():
    rows=[]
    for f in sorted(DATA.glob('*.csv')):
        df=pd.read_csv(f)
        for col in df.columns:
            rows.append({
                'file':f.name,'column':col,'dtype':str(df[col].dtype),
                'rows':len(df),'null_rate':round(float(df[col].isna().mean()),4),
                'unique':int(df[col].nunique(dropna=True))
            })
    out=pd.DataFrame(rows)
    out.to_csv(OUT,index=False)
    return out
if __name__=='__main__': print(profile().head(30).to_string(index=False))
