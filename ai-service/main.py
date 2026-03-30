from fastapi import FastAPI
from pydantic import BaseModel
import random
import time
import os
import joblib
import pandas as pd

app = FastAPI(title='AI Service (simulated)')

# Try to load the new tabular model (trained on real data) if present
from models.tabular_model import TabularModel
TAB_MODEL = TabularModel(model_path=os.path.join(os.path.dirname(__file__), 'model_real.pkl'))
TAB_MODEL_LOADED = False
try:
    TAB_MODEL_LOADED = TAB_MODEL.load()
    if TAB_MODEL_LOADED:
        print('Loaded tabular real model')
except Exception as e:
    print('Tabular model load error', e)


class AppData(BaseModel):
    id: int | None = None
    name: str | None = None
    country: str | None = None
    document_quality: str | None = None


@app.post('/predict')
def predict(data: AppData):
    # If a trained model exists, use it; otherwise fallback to simulation
    time.sleep(0.2)
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    try:
        # Prefer the real-trained tabular model if available
        if TAB_MODEL_LOADED:
            # build feature dict
            payload = {
                'completeness': float(getattr(data,'completeness',1.0) or 1.0),
                'face_score': float(getattr(data,'face_score',0.8) or 0.8),
                'doc_score': float(getattr(data,'doc_score',0.8) or 0.8),
                'liveness_score': float(getattr(data,'liveness_score',0.8) or 0.8),
                'doc_quality': getattr(data,'document_quality',None) or 'Good'
            }
            pred, prob = TAB_MODEL.predict(payload)
            return {'risk': pred, 'confidence': prob, 'processing_time': round(random.uniform(0.5,2.5),2)}

        if os.path.exists(model_path):
            clf = joblib.load(model_path)
            # build feature vector similar to train.py
            df = pd.DataFrame([{
                'completeness': float(getattr(data,'completeness',1.0) or 1.0),
                'face_score': float(getattr(data,'face_score',0.8) or 0.8),
                'doc_score': float(getattr(data,'doc_score',0.8) or 0.8),
                'liveness_score': float(getattr(data,'liveness_score',0.8) or 0.8),
                'doc_quality_good': 1 if getattr(data,'document_quality',None)=='Good' else 0
            }])
            pred = clf.predict(df)[0]
            probs = clf.predict_proba(df)[0]
            # map classes to probs
            classes = clf.classes_
            prob = None
            for i,c in enumerate(classes):
                if c==pred:
                    prob = round(float(probs[i]),2)
            return {'risk': pred, 'confidence': prob, 'processing_time': round(random.uniform(0.5,2.5),2)}
    except Exception as e:
        # fallback to simulation on error
        print('Model predict error:', e)

    # Simulated prediction output
    return {
        'risk': random.choices(['Low', 'Medium', 'High'], weights=[60,30,10])[0],
        'confidence': round(random.uniform(0.6,0.99),2),
        'processing_time': round(random.uniform(1.0,6.0),2)
    }


@app.post('/verify')
def verify(data: dict):
    # Simulate multimodal verification: face, document, liveness
    face = {'match': random.choice([True, False]), 'score': round(random.uniform(0.5,0.99),2)}
    doc = {'authentic': random.choice([True, False]), 'score': round(random.uniform(0.4,0.98),2)}
    liveness = {'passed': random.choice([True, False]), 'score': round(random.uniform(0.5,0.99),2)}
    overall_confidence = round((face['score'] + doc['score'] + liveness['score'])/3,2)
    verdict = 'Verified' if face['match'] and doc['authentic'] and liveness['passed'] else 'Review'
    return {
        'verdict': verdict,
        'confidence': overall_confidence,
        'details': { 'face': face, 'document': doc, 'liveness': liveness }
    }
