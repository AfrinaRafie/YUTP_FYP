"""
ai/train_models.py
------------------
Trains every AI model the dashboard uses, evaluates them HONESTLY, and saves
predictions back into the database.

  1. Likelihood model  - will the donor give in the next 12 months? (classification)
                         Compares Logistic Regression, Random Forest, Gradient Boosting
                         against a simple rule, then keeps the best.
  2. Value model       - how much will they give in the next 12 months? (regression)
  3. SHAP explanations - WHY each donor got their score (top 3 reasons)
  4. Donor segments    - K-Means clustering into behaviour groups (unsupervised)

Honest evaluation = time-based split:
    train : history up to SNAPSHOT-24m  -> what happened in the following 12 months
    test  : history up to SNAPSHOT-12m  -> what happened in the following 12 months
The test period is never seen during training, and the answer is never an input.

After evaluation, the models are re-trained on ALL labelled data and used to
score every donor as of SNAPSHOT (predicting the next 12 months).

Run (from the project folder):  python ai/train_models.py
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, precision_score, r2_score,
                             recall_score, roc_auc_score, silhouette_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ai.features import FEATURE_LABELS, build_features, build_targets, load_tables  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "yutp_donor_system_v2.db"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)
SEED = 42


def month_end(ts):
    return (pd.Timestamp(ts) + pd.offsets.MonthEnd(0)).normalize()


# ---------------------------------------------------------------------------
# 0. Data + honest time-based split
# ---------------------------------------------------------------------------
donors, gifts, events = load_tables(DB_PATH)
SNAPSHOT = month_end(gifts["donation_date"].max())
TRAIN_CUT = SNAPSHOT - pd.DateOffset(months=24)
TEST_CUT = SNAPSHOT - pd.DateOffset(months=12)

X_tr = build_features(donors, gifts, events, TRAIN_CUT)
y_tr, amt_tr = build_targets(gifts, X_tr.index, TRAIN_CUT)
X_te = build_features(donors, gifts, events, TEST_CUT)
y_te, amt_te = build_targets(gifts, X_te.index, TEST_CUT)

print(f"Snapshot (today): {SNAPSHOT.date()}")
print(f"Train: features to {TRAIN_CUT.date()}, {len(X_tr):,} donors, {y_tr.mean():.0%} gave again")
print(f"Test : features to {TEST_CUT.date()}, {len(X_te):,} donors, {y_te.mean():.0%} gave again\n")


# ---------------------------------------------------------------------------
# 1. Likelihood model - compare candidates honestly
# ---------------------------------------------------------------------------
def scores(y_true, prob, threshold=0.5):
    pred = (prob >= threshold).astype(int)
    return {
        "roc_auc": round(roc_auc_score(y_true, prob), 3) if len(set(prob)) > 2 else None,
        "accuracy": round(accuracy_score(y_true, pred), 3),
        "precision": round(precision_score(y_true, pred), 3),
        "recall": round(recall_score(y_true, pred), 3),
        "f1": round(f1_score(y_true, pred), 3),
    }


candidates = {
    "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
    "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=10,
                                            random_state=SEED, n_jobs=-1),
    "Gradient Boosting": HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300,
                                                         random_state=SEED),
}

comparison = {}
baseline_prob = (X_te["recency_days"] <= 365).astype(float).values  # simple business rule
comparison["Simple rule (gave in last 12 months)"] = scores(y_te, baseline_prob)

for name, model in candidates.items():
    model.fit(X_tr, y_tr)
    comparison[name] = scores(y_te, model.predict_proba(X_te)[:, 1])

print("LIKELIHOOD MODEL - honest test on unseen period")
print(pd.DataFrame(comparison).T.to_string(), "\n")

best_name = max(candidates, key=lambda n: comparison[n]["roc_auc"])
print(f"Best model: {best_name}\n")


# ---------------------------------------------------------------------------
# 2. Value model - predicted amount in next 12 months
#    expected amount = P(give) x amount-if-they-give   (a standard "hurdle" approach)
# ---------------------------------------------------------------------------
def fit_value_model(X, amount):
    """Regression on log(amount) for donors who gave. Predicting on a log scale
    under-estimates big gifts when converted back, so we apply Duan's smearing
    correction (multiply by the average of exp(residual))."""
    givers = amount > 0
    reg = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=300, random_state=SEED)
    y_log = np.log1p(amount[givers])
    reg.fit(X[givers], y_log)
    reg.smearing_ = float(np.mean(np.exp(y_log - reg.predict(X[givers]))))
    return reg


def predict_amount(reg, X):
    return np.expm1(reg.predict(X)) * reg.smearing_


value_model = fit_value_model(X_tr, amt_tr)
best_clf = candidates[best_name]
p_te = best_clf.predict_proba(X_te)[:, 1]
expected_te = p_te * predict_amount(value_model, X_te)

givers_te = amt_te > 0
value_metrics = {
    "r2_log_amount_givers": round(r2_score(np.log1p(amt_te[givers_te]), value_model.predict(X_te[givers_te])), 3),
    "mae_rm_all_donors": round(mean_absolute_error(amt_te, expected_te), 0),
    "baseline_mae_rm_last_12m": round(mean_absolute_error(amt_te, np.expm1(X_te["amount_12m_log"])), 0),
    "predicted_total_rm": round(float(expected_te.sum()), 0),
    "actual_total_rm": round(float(amt_te.sum()), 0),
}
print("VALUE MODEL - honest test on unseen period")
for k, v in value_metrics.items():
    print(f"  {k:28s} {v:,}")
print()


# ---------------------------------------------------------------------------
# 3. Final models: re-train on ALL labelled data, score everyone as of SNAPSHOT
# ---------------------------------------------------------------------------
X_all = pd.concat([X_tr, X_te])
y_all = pd.concat([y_tr, y_te])
amt_all = pd.concat([amt_tr, amt_te])

final_clf = type(best_clf)(**best_clf.get_params()) if best_name != "Logistic Regression" else \
    make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
final_clf.fit(X_all, y_all)
final_value = fit_value_model(X_all, amt_all)

X_now = build_features(donors, gifts, events, SNAPSHOT)
# Cap at 1-99%: no honest model is ever 100% sure about human behaviour
likelihood = np.clip(final_clf.predict_proba(X_now)[:, 1], 0.01, 0.99)
amount_if_give = predict_amount(final_value, X_now)
expected_amount = likelihood * amount_if_give


def band(p):
    # Fixed, explainable thresholds - NOT forced percentages
    return "High Potential" if p >= 0.70 else "Moderate Potential" if p >= 0.40 else "Low Potential"


# ---------------------------------------------------------------------------
# 4. SHAP - why did each donor get their score?
# ---------------------------------------------------------------------------
if best_name == "Logistic Regression":
    scaler, lr = final_clf.named_steps["standardscaler"], final_clf.named_steps["logisticregression"]
    explainer = shap.LinearExplainer(lr, scaler.transform(X_all))
    shap_values = explainer.shap_values(scaler.transform(X_now))
else:
    explainer = shap.TreeExplainer(final_clf)
    sv = explainer.shap_values(X_now)
    shap_values = sv[:, :, 1] if np.ndim(sv) == 3 else (sv[1] if isinstance(sv, list) else sv)

shap_df = pd.DataFrame(shap_values, index=X_now.index, columns=X_now.columns)


def describe(feature, value):
    """Turn a feature value into plain English for the reason text."""
    if feature == "recency_days":
        return f"last gave {int(value)} days ago"
    if feature == "days_since_event":
        return "no events attended" if value >= 3650 else f"last event {int(value)} days ago"
    if feature == "tenure_days":
        return f"donor for {value / 365:.1f} years"
    if feature in ("monetary_log", "avg_gift_log", "amount_12m_log"):
        return f"{FEATURE_LABELS[feature].lower()}: RM {np.expm1(value):,.0f}"
    if feature == "campaign_share":
        return f"{value:.0%} of gifts during campaigns"
    if feature.startswith("cat_") or feature == "is_hnwi":
        return FEATURE_LABELS[feature] if value else f"not a {FEATURE_LABELS[feature].lower()}"
    return f"{FEATURE_LABELS[feature].lower()}: {int(value)}"


def top_reasons(donor_id, n=3):
    row = shap_df.loc[donor_id]
    top = row.reindex(row.abs().sort_values(ascending=False).index)[:n]
    return [{"feature": f, "label": FEATURE_LABELS[f], "text": describe(f, X_now.at[donor_id, f]),
             "impact": round(float(v), 3), "direction": "up" if v > 0 else "down"} for f, v in top.items()]


global_importance = shap_df.abs().mean().sort_values(ascending=False)


# ---------------------------------------------------------------------------
# 5. Donor segments - K-Means (unsupervised learning)
# ---------------------------------------------------------------------------
seg_cols = ["recency_days", "frequency", "monetary_log", "events_12m", "tenure_days"]
seg_X = X_now[seg_cols].copy()
seg_X["frequency"] = np.log1p(seg_X["frequency"])
seg_scaler = StandardScaler().fit(seg_X)
Z = seg_scaler.transform(seg_X)

sil = {}
for k in range(3, 7):
    km_k = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Z)
    sil[k] = round(silhouette_score(Z, km_k.labels_), 3)
K = 4  # 4 segments are easy for staff to act on; silhouette scores reported for transparency
kmeans = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit(Z)
labels = kmeans.labels_

prof = X_now[seg_cols].assign(cluster=labels, likelihood=likelihood).groupby("cluster").mean()
names = {}
remaining = list(prof.index)
lapsed = prof.loc[remaining, "recency_days"].idxmax(); names[lapsed] = "Lapsed"; remaining.remove(lapsed)
champ = prof.loc[remaining].eval("frequency * events_12m / (recency_days + 30)").idxmax()
names[champ] = "Loyal Champions"; remaining.remove(champ)
new = prof.loc[remaining, "tenure_days"].idxmin(); names[new] = "New & Growing"; remaining.remove(new)
for c in remaining:
    names[c] = "Regular Supporters"  # long-time frequent givers, fewer events

segment = pd.Series(labels, index=X_now.index).map(names)
segment_profile = (X_now[seg_cols].assign(segment=segment.values, likelihood=likelihood,
                                          expected_amount=expected_amount)
                   .groupby("segment")
                   .agg(donors=("recency_days", "size"), avg_recency_days=("recency_days", "mean"),
                        avg_gifts=("frequency", "mean"), avg_events_12m=("events_12m", "mean"),
                        avg_likelihood=("likelihood", "mean"), expected_rm_12m=("expected_amount", "sum"))
                   .round(2))
print("DONOR SEGMENTS (K-Means, k=4) - silhouette by k:", sil)
print(segment_profile.to_string(), "\n")

# Preferred fund (descriptive, from history - not a prediction)
fav_fund = (gifts[gifts["donation_date"] > SNAPSHOT - pd.DateOffset(months=36)]
            .groupby(["donor_id", "fund_category"])["donation_amount"].sum()
            .reset_index().sort_values("donation_amount")
            .drop_duplicates("donor_id", keep="last").set_index("donor_id")["fund_category"])


# ---------------------------------------------------------------------------
# 6. Save models, metrics and predictions
# ---------------------------------------------------------------------------
joblib.dump({"model": final_clf, "features": list(X_now.columns), "name": best_name},
            MODEL_DIR / "likelihood_model.joblib")
joblib.dump({"model": final_value, "features": list(X_now.columns), "smearing": final_value.smearing_}, MODEL_DIR / "value_model.joblib")
joblib.dump({"scaler": seg_scaler, "kmeans": kmeans, "columns": seg_cols, "names": names},
            MODEL_DIR / "segment_model.joblib")

metrics = {
    "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "snapshot_date": str(SNAPSHOT.date()),
    "prediction_window": f"{(SNAPSHOT + pd.Timedelta(days=1)).date()} to "
                         f"{(SNAPSHOT + pd.DateOffset(months=12)).date()}",
    "evaluation": {"train_cutoff": str(TRAIN_CUT.date()), "test_cutoff": str(TEST_CUT.date()),
                   "train_donors": len(X_tr), "test_donors": len(X_te),
                   "test_positive_rate": round(float(y_te.mean()), 3)},
    "best_model": best_name,
    "likelihood_comparison": comparison,
    "value_model": value_metrics,
    "segments": {"k": K, "silhouette_by_k": sil, "profile": segment_profile.reset_index().to_dict("records")},
    "global_feature_importance": [{"feature": f, "label": FEATURE_LABELS[f], "mean_abs_shap": round(float(v), 4)}
                                  for f, v in global_importance.items()],
}
(MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

pred = pd.DataFrame({
    "donor_id": X_now.index,
    "predicted_likelihood": likelihood.round(4),
    "likelihood_band": [band(p) for p in likelihood],
    "predicted_amount_12m": expected_amount.round(2),
    "segment": segment.values,
    "top_reasons": [json.dumps(top_reasons(d)) for d in X_now.index],
    # Flag for staff: big historic givers whose chance of giving again has dropped
    "at_risk_high_value": ((X_now["monetary_log"] >= X_now["monetary_log"].quantile(0.75)).values
                           & (likelihood < 0.40)).astype(int),
    "predicted_interest_area": fav_fund.reindex(X_now.index).fillna("Scholarship Bursary").values,
    "scored_at": str(SNAPSHOT.date()),
})

con = sqlite3.connect(DB_PATH)
con.execute("DROP TABLE IF EXISTS ai_predictions")
pred.to_sql("ai_predictions", con, index=False)
con.execute("CREATE UNIQUE INDEX idx_pred_donor ON ai_predictions(donor_id)")
con.commit()
con.close()

print("Likelihood bands:", pred["likelihood_band"].value_counts().to_dict())
print("At-risk high-value donors to contact:", int(pred["at_risk_high_value"].sum()))
print(f"Saved models + metrics to {MODEL_DIR.name}/ and {len(pred):,} predictions to ai_predictions table.")
example = pred.sort_values("predicted_likelihood", ascending=False).iloc[0]
print(f"\nExample - donor {example.donor_id}: {example.predicted_likelihood:.0%} likely, "
      f"segment '{example.segment}'. Why:")
for r in json.loads(example.top_reasons):
    print(f"   {'+' if r['direction'] == 'up' else '-'} {r['text']}")
