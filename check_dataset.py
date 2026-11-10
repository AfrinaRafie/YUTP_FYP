"""
check_dataset.py - Is the dataset learnable? (honest time-based test, no leakage)
Train: history up to Oct 2024 -> did they give Nov 2024-Oct 2025?
Test : history up to Oct 2025 -> did they give Nov 2025-Oct 2026?  (period the model never saw)
Run:  python check_dataset.py
"""
import sqlite3, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
con=sqlite3.connect("yutp_donor_system_v2.db")
d=pd.read_sql("select * from donors",con); g=pd.read_sql("select * from donations",con,parse_dates=["donation_date"])
a=pd.read_sql("select * from event_attendance",con,parse_dates=["event_date"])
def build(cut):
    cut=pd.Timestamp(cut); end=cut+pd.DateOffset(months=12)
    h=g[g.donation_date<=cut]; f=g[(g.donation_date>cut)&(g.donation_date<=end)]
    ev=a[a.event_date<=cut]
    x=h.groupby("donor_id").agg(recency=("donation_date",lambda s:(cut-s.max()).days),
        frequency=("donation_date","size"), monetary=("donation_amount","sum"), avg_gift=("donation_amount","mean"),
        tenure=("donation_date",lambda s:(cut-s.min()).days))
    x["gifts_12m"]=h[h.donation_date>cut-pd.DateOffset(months=12)].groupby("donor_id").size().reindex(x.index,fill_value=0)
    x["events_total"]=ev.groupby("donor_id").size().reindex(x.index,fill_value=0)
    x["events_12m"]=ev[ev.event_date>cut-pd.DateOffset(months=12)].groupby("donor_id").size().reindex(x.index,fill_value=0)
    x["days_since_event"]=(cut-ev.groupby("donor_id").event_date.max()).dt.days.reindex(x.index).fillna(3000)
    x=x.join(d.set_index("donor_id")[["donor_category","is_hnwi"]])
    x=pd.get_dummies(x,columns=["donor_category"],dtype=int)
    x["monetary"]=np.log1p(x.monetary); x["avg_gift"]=np.log1p(x.avg_gift)
    y=x.index.isin(f.donor_id).astype(int)
    return x,y
Xtr,ytr=build("2024-10-31"); Xte,yte=build("2025-10-31"); Xte=Xte.reindex(columns=Xtr.columns,fill_value=0)
print(f"train donors {len(Xtr)} (gave again {ytr.mean():.0%}) | test donors {len(Xte)} (gave again {yte.mean():.0%})")
models={"Logistic Regression":make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000)),
 "Random Forest":RandomForestClassifier(400,min_samples_leaf=5,random_state=0,n_jobs=-1),
 "Gradient Boosting":HistGradientBoostingClassifier(random_state=0)}
for n,m in models.items():
    m.fit(Xtr,ytr); p=m.predict_proba(Xte)[:,1]
    print(f"{n:20s} ROC-AUC {roc_auc_score(yte,p):.3f} | accuracy {accuracy_score(yte,p>0.5):.3f} | F1 {f1_score(yte,p>0.5):.3f}")
base=(Xte.recency<365).astype(int); print(f"{'Simple rule (gave <1yr)':20s} accuracy {accuracy_score(yte,base):.3f}")
rf=models["Random Forest"]; print("Top features:", pd.Series(rf.feature_importances_,Xtr.columns).sort_values(ascending=False).head(6).round(3).to_dict())
