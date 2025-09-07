from fastapi import FastAPI
import joblib, json
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Lead Scoring API")

model = joblib.load("models/model.joblib")
meta = json.load(open("models/metadata.json"))
columns = meta["columns"]

class Leads(BaseModel):
    records: List[Dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(leads: Leads):
    df = pd.DataFrame(leads.records)
    for c in columns:
        if c not in df.columns:
            df[c] = None
    df = df[columns]
    proba = model.predict_proba(df)[:,1]
    return {"conversion_prob": proba.tolist()}
