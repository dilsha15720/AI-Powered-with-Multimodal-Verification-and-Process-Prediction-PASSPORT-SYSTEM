# AI-Powered Multimodal Verification & Process Prediction (Research Prototype)

This repository contains a prototype for a final-year research project: "AI-Powered with Multimodal Verification and Process Prediction for Application Processing with blockchain concept".

Services:
- frontend: React dashboard (port 3000)
- backend: Node + Express API (port 5000)
- ai-service: Python FastAPI simulated AI endpoints (port 8000)
- blockchain-sim: Node simulated blockchain (port 7000)

Quick start (Docker):

1. Build and run with Docker Compose:

```bash
# from repository root
docker compose up --build
```

2. Open the dashboard:

- http://localhost:3000

Notes:
- This is a research prototype using simulated AI outputs and an in-memory blockchain log. Replace with real ML models and a persistent DB for production.
- The frontend uses mock data and simple visualizations.

Training a model (research)
---------------------------
You can create a simple synthetic dataset and train a tabular model used by the AI service. Steps:

1. Create synthetic data (CSV):

```bash
cd ai-service
python data/gen_data.py
```

2. Install training deps and run training (use the venv as earlier):

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python train.py
```

This writes `ai-service/model.pkl`. The FastAPI `POST /predict` will load this model at startup and use it to score incoming applications. If `model.pkl` is absent the service falls back to the simulated predictor.

Real data training (use your dataset)
------------------------------------
If you have a real CSV dataset, place it at `ai-service/data/real_data.csv`. The CSV must include these columns:

- completeness (float 0-1)
- face_score (float 0-1)
- doc_score (float 0-1)
- liveness_score (float 0-1)
- doc_quality (Good/Poor)
- risk (Low/Medium/High)  <-- target label

Then run the specialized trainer which produces `model_real.pkl`:

```bash
# from ai-service/
. .venv/bin/activate
python train_real.py
```

After training, restart the AI service. The `/predict` endpoint will prefer `model_real.pkl` if present and use it for predictions; otherwise it will fall back to the simulated predictor or `model.pkl`.

Optional: you can dockerize training or use a notebook to iterate on architectures and datasets.

API examples (local):

- List apps: GET http://localhost:5000/api/apps
- Analyze application (calls AI predict + blockchain): POST http://localhost:5000/api/analyze
- Verify multimodal: POST http://localhost:5000/api/verify
- View chain: GET http://localhost:5000/api/blockchain/chain

If you want, I can now:
- Add unit tests for backend and ai-service
- Add React Router and more UI pages
- Add real model hooks (placeholder) and sample image uploads

Local development helper
------------------------
To run the services locally (without Docker) there are small helper scripts. They will start the simulated blockchain, the AI FastAPI service (using the venv if present), and the backend pointing to the local AI and blockchain.

Start locally:

```bash
# install deps first (only required once)
cd backend && npm install
cd ../blockchain-sim && npm install
cd ../ai-service && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt

# from project root
./scripts/start-local.sh
```

Stop locally:

```bash
./scripts/stop-local.sh
```

Notes:
- The backend will use environment variables `AI_URL` and `BLOCKCHAIN_URL` when provided; otherwise it defaults to Docker service names (`http://ai-service:8000`, `http://blockchain-sim:7000`).
- For container runs, `docker compose up --build` will start everything; if Docker daemon isn't running please start Docker Desktop on macOS first.

