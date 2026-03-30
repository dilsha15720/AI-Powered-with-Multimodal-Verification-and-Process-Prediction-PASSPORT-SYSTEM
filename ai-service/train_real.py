"""Train using a real dataset file placed at `data/real_data.csv`.

The CSV must include columns: completeness, face_score, doc_score, liveness_score, doc_quality, risk
"""
from models.tabular_model import TabularModel
import os

DATA = 'data/real_data.csv'
MODEL_OUT = 'model_real.pkl'

if __name__ == '__main__':
    if not os.path.exists(DATA):
        raise SystemExit(f"Place your real CSV at {DATA} with required columns. See docs.")
    m = TabularModel(model_path=MODEL_OUT)
    m.train(DATA, save=True)
    print('Training complete.')
