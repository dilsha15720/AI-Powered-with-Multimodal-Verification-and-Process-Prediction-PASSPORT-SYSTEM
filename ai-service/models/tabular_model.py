import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

class TabularModel:
    def __init__(self, model_path='model_real.pkl'):
        self.model_path = model_path
        self.clf = None

    def featurize(self, df):
        X = df[['completeness','face_score','doc_score','liveness_score']].copy()
        X['doc_quality_good'] = (df['doc_quality']=='Good').astype(int)
        return X

    def train(self, csv_path, save=True):
        df = pd.read_csv(csv_path)
        # Expect column 'risk'
        X = self.featurize(df)
        y = df['risk']
        X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        print(classification_report(y_test, preds))
        self.clf = clf
        if save:
            joblib.dump(clf, self.model_path)
            print(f"Saved model to {self.model_path}")

    def load(self):
        if os.path.exists(self.model_path):
            self.clf = joblib.load(self.model_path)
            return True
        return False

    def predict(self, data_dict):
        if self.clf is None:
            raise RuntimeError('Model not loaded')
        df = pd.DataFrame([data_dict])
        X = self.featurize(df)
        pred = self.clf.predict(X)[0]
        probs = self.clf.predict_proba(X)[0]
        classes = self.clf.classes_
        prob = None
        for i,c in enumerate(classes):
            if c==pred:
                prob = float(probs[i])
        return pred, round(prob,2)
