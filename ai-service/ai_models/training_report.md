# Training Report

**Data:** data/train.csv

## Features
Numeric: completeness, face_score, doc_score, liveness_score

Categorical: doc_quality, risk, created_at

## Classification Models
### random_forest
Accuracy: 1.0

Confusion Matrix:
```
[[230, 0, 0], [0, 3, 0], [0, 0, 167]]
```

### logistic_regression
Accuracy: 1.0

Confusion Matrix:
```
[[230, 0, 0], [0, 3, 0], [0, 0, 167]]
```

## Hyperparameter Search
Best params: {'clf__max_depth': None, 'clf__n_estimators': 50}
Best CV score: 1.0
