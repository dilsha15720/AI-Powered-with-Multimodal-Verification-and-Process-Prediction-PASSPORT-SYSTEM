"""Comprehensive training script for research demonstration.

Usage examples:
  python train_full.py --data data/real_data.csv --out models/

The script will:
 - load CSV
 - clean and auto-select features (or use provided feature lists)
 - build preprocessing pipeline
 - train classification models (RandomForest, LogisticRegression)
 - optionally train a regression model (if --reg_target provided)
 - evaluate metrics and save models using joblib
"""
import argparse
import os
import json
import pandas as pd
from models.training_utils import (
    load_csv, basic_clean, auto_select_features, build_preprocessor,
    train_classifiers, train_regressor, print_classification_results, print_regression_results
)
from models.model_evaluation import evaluate_classification, evaluate_regression, explain_prediction_simple
from sklearn.model_selection import GridSearchCV
import joblib


def map_to_workflow(df: pd.DataFrame) -> pd.DataFrame:
    """Map arbitrary dataset columns to workflow features used in the prototype.

    Heuristic: if expected columns exist, keep them. Otherwise pick top numeric columns
    and rename them to the four expected numeric features.
    Expected features: completeness, face_score, doc_score, liveness_score, doc_quality
    """
    df = df.copy()
    expected = ['completeness', 'face_score', 'doc_score', 'liveness_score', 'doc_quality']
    missing = [c for c in expected if c not in df.columns]
    if not missing:
        return df

    # auto-map: choose up to 4 numeric columns to fill completeness/face/doc/liveness
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    used = {}
    for i, name in enumerate(['completeness', 'face_score', 'doc_score', 'liveness_score']):
        if i < len(numeric_cols):
            used[name] = numeric_cols[i]
        else:
            # if not enough numeric columns, create a default constant
            df[name] = 0.0
    # Create a doc_quality column from first categorical or fallback 'Good'
    if 'doc_quality' not in df.columns:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if len(cat_cols) > 0:
            df['doc_quality'] = df[cat_cols[0]].fillna('Unknown').astype(str)
        else:
            df['doc_quality'] = 'Good'

    # rename chosen numeric columns to expected names
    for k, v in used.items():
        if v != k:
            df[k] = df[v]

    return df


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', '-d', required=True, help='Path to CSV file')
    parser.add_argument('--out', '-o', default='ai_models', help='Output folder for saved models')
    parser.add_argument('--class_target', '-c', default='risk', help='Column name to use as classification target')
    parser.add_argument('--reg_target', '-r', default=None, help='Column name to use as regression target (processing time)')
    parser.add_argument('--features', nargs='+', default=None, help='Explicit list of feature columns to use (overrides auto-select)')
    parser.add_argument('--hyper', action='store_true', help='Run a small GridSearchCV hyperparameter search')
    args = parser.parse_args(argv)

    print('Loading data from', args.data)
    df = load_csv(args.data)
    df = basic_clean(df)

    # Map dataset into expected workflow features heuristically
    df = map_to_workflow(df)

    # Determine features
    if args.features:
        features = args.features
        cat_cols = [c for c in features if df[c].dtype == 'object']
        num_cols = [c for c in features if c not in cat_cols]
    else:
        num_cols, cat_cols = auto_select_features(df, n_numeric=4)

    print('Numeric features:', num_cols)
    print('Categorical features:', cat_cols)

    # Ensure classification target exists
    if args.class_target not in df.columns:
        raise SystemExit(f"Classification target '{args.class_target}' not found in data columns: {df.columns.tolist()}")

    X = df[num_cols + cat_cols]
    y_class = df[args.class_target]

    preprocessor = build_preprocessor(num_cols, cat_cols)

    os.makedirs(args.out, exist_ok=True)

    # Train classification models
    print('\nTraining classification models...')
    clf_results = train_classifiers(X, y_class, preprocessor, args.out, prefix='workflow')
    # run evaluation and explainability for each trained classifier
    X_test = clf_results.get('_X_test')
    y_test = clf_results.get('_y_test')
    eval_summaries = {}
    if X_test is not None and y_test is not None:
        for name, info in [(k, v) for k, v in clf_results.items() if not k.startswith('_')]:
            try:
                print(f"Evaluating {name} ...")
                model = info.get('model')
                ev = evaluate_classification(model, X_test, y_test, args.out, name_prefix=f'workflow_{name}')
                eval_summaries[name] = ev
            except Exception as e:
                print('Evaluation failed for', name, e)
    # optional hyperparameter search
    hyper_info = None
    if getattr(args, 'hyper', False):
        print('\nRunning small GridSearchCV for RandomForest (this may take some time)...')
        rf_pipe = joblib.load(os.path.join(args.out, 'workflow_random_forest.joblib')) if os.path.exists(os.path.join(args.out, 'workflow_random_forest.joblib')) else None
        if rf_pipe is not None:
            param_grid = {'clf__n_estimators': [50, 100], 'clf__max_depth': [None, 10]}
            gs = GridSearchCV(rf_pipe, param_grid, cv=3, scoring='accuracy')
            gs.fit(X, y_class)
            print('GridSearch best params:', gs.best_params_)
            hyper_info = {'best_params': gs.best_params_, 'best_score': float(gs.best_score_)}
            # save best estimator
            joblib.dump(gs.best_estimator_, os.path.join(args.out, 'workflow_random_forest_grid_best.joblib'))
    print('\nClassification evaluation:')
    print_classification_results(clf_results)
    # append evaluation summary to report

    # write a human-readable training report (markdown)
    report_path = os.path.join(args.out, 'training_report.md')
    with open(report_path, 'w') as fh:
        fh.write('# Training Report\n\n')
        fh.write(f'**Data:** {args.data}\n\n')
        fh.write('## Features\n')
        fh.write('Numeric: ' + ', '.join(num_cols) + '\n\n')
        fh.write('Categorical: ' + ', '.join(cat_cols) + '\n\n')
        fh.write('## Classification Models\n')
        for name, info in clf_results.items():
            if str(name).startswith('_'):
                continue
            fh.write(f'### {name}\n')
            fh.write(f"Accuracy: {info['metrics'].get('accuracy')}\n\n")
            fh.write('Confusion Matrix:\n')
            fh.write("```\n")
            fh.write(str(info['metrics'].get('confusion')) + "\n")
            fh.write("```\n\n")
            # include evaluation file reference if present
            ev = eval_summaries.get(name)
            if ev:
                fh.write('Feature importance plot: ' + (ev.get('feature_importance_plot') or 'none') + '\n\n')
        if hyper_info:
            fh.write('## Hyperparameter Search\n')
            fh.write('Best params: ' + str(hyper_info['best_params']) + '\n')
            fh.write('Best CV score: ' + str(hyper_info['best_score']) + '\n')
    print('Wrote training report to', report_path)

    # Optionally train regression model
    if args.reg_target:
        if args.reg_target not in df.columns:
            print(f"Regression target '{args.reg_target}' not found; skipping regression.")
        else:
            y_reg = df[args.reg_target]
            print('\nTraining regression model...')
            reg_info = train_regressor(X, y_reg, preprocessor, args.out, prefix='workflow')
            print('\nRegression evaluation:')
            print_regression_results(reg_info)

    print('\nAll done. Models saved in', os.path.abspath(args.out))


if __name__ == '__main__':
    main()
