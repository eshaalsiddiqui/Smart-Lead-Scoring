import json
import os

import joblib
import numpy as np
import pandas as pd
import streamlit as st
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

st.set_page_config(page_title="Smart Lead Scoring", layout="wide")
st.title("Smart Lead Scoring Dashboard")


def next_best_action(prob):
    if prob >= 0.7:
        return "Call"
    elif prob >= 0.4:
        return "Email"
    else:
        return "Nurture"


@st.cache_data
def load_sample():
    # keep_default_na=False prevents pandas from silently treating the
    # literal region code "NA" (North America) as a missing value.
    return pd.read_csv("data/sample_leads.csv", keep_default_na=False, na_values=[])


# Load data
uploaded = st.file_uploader("Upload your leads CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    df = load_sample()
st.write("Preview:", df.head())

# Train/test split
X = df.drop(columns=["converted"])
y = df["converted"]
cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
num_cols = [c for c in X.columns if c not in cat_cols]

preprocess = ColumnTransformer(
    [
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", StandardScaler(with_mean=False), num_cols),
    ]
)

try:
    clf = xgb.XGBClassifier(eval_metric="logloss", random_state=42)
except:
    clf = GradientBoostingClassifier(random_state=42)

pipe = Pipeline([("pre", preprocess), ("clf", clf)])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

pipe.fit(X_train, y_train)
proba = pipe.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, proba)
st.metric("ROC AUC", f"{auc:.3f}")

# Score all leads
scores = pipe.predict_proba(X)[:, 1]
df["conversion_prob"] = scores
df["revenue_potential"] = df["conversion_prob"] * df["deal_size_estimate"]
df["next_best_action"] = df["conversion_prob"].apply(next_best_action)

st.subheader("Ranked Leads")
st.dataframe(df.sort_values("revenue_potential", ascending=False).head(20))

# Save model
os.makedirs("models", exist_ok=True)
joblib.dump(pipe, "models/model.joblib")
json.dump({"columns": X.columns.tolist()}, open("models/metadata.json", "w"))
