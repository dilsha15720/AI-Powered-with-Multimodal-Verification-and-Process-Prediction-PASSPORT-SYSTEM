from fastapi import FastAPI
from pydantic import BaseModel
import random
import time
import os
import joblib
import pandas as pd
from typing import Optional

# Try to load any joblib pipelines saved by training (preprocessor + estimator)
JOBLIB_DIR = os.path.join(os.path.dirname(__file__), 'ai_models')
JOB_CLASSIFIER: Optional[object] = None
JOB_REGRESSOR: Optional[object] = None
def load_joblib_models():
    """Load joblib pipelines from the ai_models directory into globals.

    Returns a dict with paths and whether loaded.
    """
    global JOB_CLASSIFIER, JOB_REGRESSOR
    status = {'classifier': None, 'regressor': None, 'loaded': False}
    try:
        clf_path = os.path.join(JOBLIB_DIR, 'workflow_random_forest.joblib')
        if os.path.exists(clf_path):
            JOB_CLASSIFIER = joblib.load(clf_path)
            status['classifier'] = clf_path
            print('Loaded joblib classifier from', clf_path)
        else:
            JOB_CLASSIFIER = None
        reg_path = os.path.join(JOBLIB_DIR, 'workflow_random_forest_regressor.joblib')
        if os.path.exists(reg_path):
            JOB_REGRESSOR = joblib.load(reg_path)
            status['regressor'] = reg_path
            print('Loaded joblib regressor from', reg_path)
        else:
            JOB_REGRESSOR = None
        status['loaded'] = (JOB_CLASSIFIER is not None)
    except Exception as e:
        print('Joblib model load error', e)
    return status

# initial load
JOB_STATUS = load_joblib_models()

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
        # Prefer joblib classifier pipeline if available
        payload = {
            'completeness': float(getattr(data,'completeness',1.0) or 1.0),
            'face_score': float(getattr(data,'face_score',0.8) or 0.8),
            'doc_score': float(getattr(data,'doc_score',0.8) or 0.8),
            'liveness_score': float(getattr(data,'liveness_score',0.8) or 0.8),
            'doc_quality': getattr(data,'document_quality',None) or 'Good'
        }
        df = pd.DataFrame([payload])
        if JOB_CLASSIFIER is not None:
            try:
                pred = JOB_CLASSIFIER.predict(df)[0]
                prob = None
                try:
                    probs = JOB_CLASSIFIER.predict_proba(df)[0]
                    classes = JOB_CLASSIFIER.classes_
                    for i,c in enumerate(classes):
                        if c==pred:
                            prob = round(float(probs[i]),2)
                except Exception:
                    prob = None
                processing_time = None
                if JOB_REGRESSOR is not None:
                    try:
                        processing_time = float(JOB_REGRESSOR.predict(df)[0])
                    except Exception:
                        processing_time = round(random.uniform(0.5,2.5),2)
                else:
                    processing_time = round(random.uniform(0.5,2.5),2)
                return {'risk': pred, 'confidence': prob, 'processing_time': processing_time}
            except Exception as e:
                print('Joblib classifier predict error', e)

        # Prefer the real-trained tabular model if available
        if TAB_MODEL_LOADED:
            # build feature dict compatible with TabularModel
            tpayload = {
                'completeness': payload['completeness'],
                'face_score': payload['face_score'],
                'doc_score': payload['doc_score'],
                'liveness_score': payload['liveness_score'],
                'doc_quality': payload['doc_quality']
            }
            pred, prob = TAB_MODEL.predict(tpayload)
            return {'risk': pred, 'confidence': prob, 'processing_time': round(random.uniform(0.5,2.5),2)}

        # fallback to older model.pkl behavior
        if os.path.exists(model_path):
            clf = joblib.load(model_path)
            df2 = pd.DataFrame([{
                'completeness': payload['completeness'],
                'face_score': payload['face_score'],
                'doc_score': payload['doc_score'],
                'liveness_score': payload['liveness_score'],
                'doc_quality_good': 1 if payload['doc_quality']=='Good' else 0
            }])
            try:
                pred = clf.predict(df2)[0]
                probs = clf.predict_proba(df2)[0]
                classes = clf.classes_
                prob = None
                for i,c in enumerate(classes):
                    if c==pred:
                        prob = round(float(probs[i]),2)
                return {'risk': pred, 'confidence': prob, 'processing_time': round(random.uniform(0.5,2.5),2)}
            except Exception as e:
                print('legacy model predict error', e)
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


@app.get('/admin/models')
def admin_models():
    """Return current model load status and file paths."""
    return {
        'classifier': JOB_STATUS.get('classifier'),
        'regressor': JOB_STATUS.get('regressor'),
        'loaded': JOB_STATUS.get('loaded', False)
    }


@app.post('/admin/reload')
def admin_reload():
    """Reload joblib models from disk without restarting the server."""
    global JOB_STATUS
    JOB_STATUS = load_joblib_models()
    return {'ok': True, 'status': JOB_STATUS}
