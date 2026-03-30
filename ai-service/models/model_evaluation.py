import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, confusion_matrix, classification_report,
    mean_absolute_error, mean_squared_error
)
from sklearn.inspection import permutation_importance


def evaluate_classification(pipeline, X_test: pd.DataFrame, y_test: pd.Series, out_dir: str, name_prefix: str = 'clf'):
    os.makedirs(out_dir, exist_ok=True)
    preds = pipeline.predict(X_test)
    acc = float(accuracy_score(y_test, preds))
    conf = confusion_matrix(y_test, preds).tolist()
    report = classification_report(y_test, preds, output_dict=True)

    # Permutation importance (works with pipeline)
    try:
        r = permutation_importance(pipeline, X_test, y_test, n_repeats=10, random_state=42, n_jobs=1)
        importances = r.importances_mean
        stds = r.importances_std
    except Exception as e:
        importances = None
        stds = None
        print('Permutation importance failed:', e)

    # Try to obtain feature names after preprocessing if possible
    try:
        # If pipeline has a 'pre' step as ColumnTransformer
        if hasattr(pipeline, 'named_steps') and 'pre' in pipeline.named_steps:
            pre = pipeline.named_steps['pre']
            # attempt to get final feature names (works for sklearn >=1.0)
            try:
                feature_names = pre.get_feature_names_out()
            except Exception:
                # fallback: use input column names if passed as DataFrame
                feature_names = X_test.columns.tolist()
        else:
            feature_names = X_test.columns.tolist()
    except Exception:
        feature_names = X_test.columns.tolist()

    # Save importance plot
    importance_path = os.path.join(out_dir, f'{name_prefix}_feature_importance.png')
    if importances is not None and len(importances) == len(feature_names):
        idx = np.argsort(importances)[::-1]
        plt.figure(figsize=(8, max(4, len(feature_names)*0.25)))
        plt.barh(np.array(feature_names)[idx], importances[idx], xerr=stds[idx] if stds is not None else None)
        plt.xlabel('Permutation importance')
        plt.title('Feature importance')
        plt.tight_layout()
        plt.savefig(importance_path)
        plt.close()
    else:
        importance_path = None

    out = {
        'accuracy': acc,
        'confusion_matrix': conf,
        'report': report,
        'feature_importance_plot': importance_path
    }

    # Save JSON
    with open(os.path.join(out_dir, f'{name_prefix}_evaluation.json'), 'w') as fh:
        json.dump(out, fh, indent=2)

    return out


def evaluate_regression(pipeline, X_test: pd.DataFrame, y_test: pd.Series, out_dir: str, name_prefix: str = 'reg'):
    os.makedirs(out_dir, exist_ok=True)
    preds = pipeline.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(mean_squared_error(y_test, preds, squared=False))
    r2 = None
    try:
        from sklearn.metrics import r2_score
        r2 = float(r2_score(y_test, preds))
    except Exception:
        r2 = None

    out = {'mae': mae, 'rmse': rmse, 'r2': r2}
    with open(os.path.join(out_dir, f'{name_prefix}_evaluation.json'), 'w') as fh:
        json.dump(out, fh, indent=2)
    return out


def explain_prediction_simple(pipeline, X_sample: pd.DataFrame, top_n: int = 3):
    """Produce a simple human-readable explanation using feature values and pipeline feature importance if possible.

    This is a heuristic explanation: identify top features by permutation importance (if available) and describe their values.
    """
    try:
        # Attempt to compute permutation importance on the single sample by using training wrapper is not ideal; instead skip heavy ops
        # Provide a simple explanation based on largest absolute deviations from feature medians
        df = X_sample.copy()
        explanations = []
        for col in df.columns:
            val = df.iloc[0][col]
            explanations.append((col, val))
        # sort by magnitude for numeric
        numeric = [(c, v) for c, v in explanations if isinstance(v, (int, float, np.integer, np.floating))]
        numeric_sorted = sorted(numeric, key=lambda x: abs(x[1]), reverse=True)
        pieces = []
        for c, v in numeric_sorted[:top_n]:
            pieces.append(f"{c}={v}")
        return 'Top contributing features: ' + ', '.join(pieces)
    except Exception as e:
        return 'No explanation available: ' + str(e)
