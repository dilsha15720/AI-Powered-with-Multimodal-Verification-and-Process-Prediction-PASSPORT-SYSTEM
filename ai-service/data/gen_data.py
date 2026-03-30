"""Generate synthetic dataset for training the CRA (claim/risk) model.

Produces a CSV with features that simulate multimodal verification scores and a risk label.
"""
import csv
import random
from datetime import datetime

OUT = 'data/train.csv'

def quality_to_score(q):
    return 0.9 if q=='Good' else 0.4

def synth_row(i):
    # simulate document quality and completeness
    doc_quality = random.choices(['Good','Poor'], weights=[0.7,0.3])[0]
    completeness = round(random.uniform(0.4,1.0),2)
    face_score = round(random.uniform(0.4,0.99) * quality_to_score(doc_quality),2)
    doc_score = round(random.uniform(0.3,0.98) * quality_to_score(doc_quality),2)
    liveness_score = round(random.uniform(0.4,0.99),2)

    # heuristic risk: low when scores high and completeness high
    score_mean = (face_score+doc_score+liveness_score)/3
    if score_mean > 0.8 and completeness > 0.85:
        risk = 'Low'
    elif score_mean > 0.6:
        risk = 'Medium'
    else:
        risk = 'High'

    return {
        'id': i,
        'doc_quality': doc_quality,
        'completeness': completeness,
        'face_score': face_score,
        'doc_score': doc_score,
        'liveness_score': liveness_score,
        'risk': risk,
        'created_at': datetime.utcnow().isoformat()
    }

def generate(n=2000):
    rows = [synth_row(i) for i in range(1, n+1)]
    with open(OUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} rows to {OUT}')

if __name__ == '__main__':
    generate(2000)
