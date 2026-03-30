"""Training utilities: data loading, preprocessing, model building and evaluation.

This module provides reusable functions to load CSVs, preprocess features (impute, encode, scale),
train classification and regression models, evaluate them, and save models with joblib.
"""
from typing import Tuple, List, Optional, Dict
import os
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score, classification_report
)
import joblib


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Remove duplicate rows and strip column names
    df = df.copy()
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def auto_select_features(df: pd.DataFrame, n_numeric: int = 4) -> Tuple[List[str], List[str]]:
    # Pick top numeric columns as features and remaining categoricals
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # drop id-like columns from numeric features
    numeric_cols = [c for c in numeric_cols if str(c).lower() not in ('id', 'index')]
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    # Prefer columns that look like scores or amounts
    if len(numeric_cols) >= n_numeric:
        selected_numeric = numeric_cols[:n_numeric]
    else:
        selected_numeric = numeric_cols
    return selected_numeric, cat_cols


def build_preprocessor(numeric_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    # numeric pipeline: impute median + scale
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # categorical pipeline: impute constant + one-hot
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ], remainder='drop'
    )
    return preprocessor


def train_classifiers(X: pd.DataFrame, y: pd.Series, preprocessor: ColumnTransformer,
                      out_dir: str, prefix: str = 'clf') -> Dict[str, Dict]:
    os.makedirs(out_dir, exist_ok=True)
    results = {}
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Random Forest
    rf_pipeline = Pipeline(steps=[('pre', preprocessor), ('clf', RandomForestClassifier(n_estimators=200, random_state=42))])
    rf_pipeline.fit(X_train, y_train)
    preds = rf_pipeline.predict(X_test)
    prob = None
    try:
        prob = rf_pipeline.predict_proba(X_test)
    except Exception:
        prob = None
    rfp = {
        'model': rf_pipeline,
        'metrics': {
            'accuracy': float(accuracy_score(y_test, preds)),
            'report': classification_report(y_test, preds, output_dict=True),
            'confusion': confusion_matrix(y_test, preds).tolist()
        }
    }
    joblib.dump(rf_pipeline, os.path.join(out_dir, f"{prefix}_random_forest.joblib"))
    results['random_forest'] = rfp

    # Logistic Regression (with simple solver)
    lr_pipeline = Pipeline(steps=[('pre', preprocessor), ('clf', LogisticRegression(max_iter=1000))])
    lr_pipeline.fit(X_train, y_train)
    preds_lr = lr_pipeline.predict(X_test)
    rlp = {
        'model': lr_pipeline,
        'metrics': {
            'accuracy': float(accuracy_score(y_test, preds_lr)),
            'report': classification_report(y_test, preds_lr, output_dict=True),
            'confusion': confusion_matrix(y_test, preds_lr).tolist()
        }
    }
    joblib.dump(lr_pipeline, os.path.join(out_dir, f"{prefix}_logistic_regression.joblib"))
    results['logistic_regression'] = rlp

    return results


def train_regressor(X: pd.DataFrame, y: pd.Series, preprocessor: ColumnTransformer,
                    out_dir: str, prefix: str = 'reg') -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    rf_pipeline = Pipeline(steps=[('pre', preprocessor), ('reg', RandomForestRegressor(n_estimators=200, random_state=42))])
    rf_pipeline.fit(X_train, y_train)
    preds = rf_pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)
    r2 = r2_score(y_test, preds)
    joblib.dump(rf_pipeline, os.path.join(out_dir, f"{prefix}_random_forest_regressor.joblib"))
    return {'model': rf_pipeline, 'metrics': {'mae': float(mae), 'rmse': float(rmse), 'r2': float(r2)}}


def print_classification_results(results: Dict):
    for name, info in results.items():
        print(f"=== {name} ===")
        metrics = info['metrics']
        print(f"Accuracy: {metrics.get('accuracy')}")
        print("Confusion Matrix:")
        print(metrics.get('confusion'))
        print("Classification report:")
        print(pd.DataFrame(metrics.get('report')))


def print_regression_results(info: Dict):
    print("=== Regression Results ===")
    for k, v in info['metrics'].items():
        print(f"{k}: {v}")
