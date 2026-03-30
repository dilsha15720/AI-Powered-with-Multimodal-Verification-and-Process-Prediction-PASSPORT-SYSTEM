"""Training script for the AI predict model.

This script expects a CSV at `data/train.csv` (see gen_data.py).
It trains a RandomForestClassifier and writes `model.pkl`.
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

DATA = 'data/train.csv'
MODEL_OUT = 'model.pkl'

def load_data(path=DATA):
    df = pd.read_csv(path)
    return df

def featurize(df):
    X = df[['completeness','face_score','doc_score','liveness_score']].copy()
    # encode doc_quality
    X['doc_quality_good'] = (df['doc_quality']=='Good').astype(int)
    y = df['risk']
    return X, y

def train():
    if not os.path.exists(DATA):
        raise SystemExit(f"Data not found: {DATA}. Run gen_data.py to create synthetic data.")
    df = load_data()
    X, y = featurize(df)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print(classification_report(y_test, preds))
    joblib.dump(clf, MODEL_OUT)
    print(f"Saved model to {MODEL_OUT}")

if __name__ == '__main__':
    train()
