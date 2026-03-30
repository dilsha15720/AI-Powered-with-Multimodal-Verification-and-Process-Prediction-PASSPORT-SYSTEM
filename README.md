# Smart Passport System — Quick start (Docker Compose)

This repository contains a research prototype for an AI-powered passport application system with a React frontend, Node/Express backend, Python AI service (FastAPI), and a lightweight blockchain hashing simulation. Docker Compose is provided to run the full stack locally.

Quick steps (tested for local development):

1) Build and start the full stack with Docker Compose

```bash
# from repository root
docker compose up --build
```

This will build and run these services:
- frontend (React) — exposed on port 3000
- backend (Node/Express) — exposed on port 5000
- ai-service (FastAPI) — exposes port 8000 to other services (not bound to host by default)
- blockchain-sim — lightweight hashing simulator (internal)

2) Environment & overrides
- To expose ai-service or blockchain on the host or change ports, edit `docker-compose.yml`.
- For local development without Docker, use the per-service instructions in their folders (install deps, run). Example: `cd ai-service && .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000`.

3) Admin authentication
- The backend issues JWT tokens for admin operations. Provide `ADMIN_PASSWORD` and `ADMIN_JWT_SECRET` via environment variables (compose file can be updated to include them). The default ADMIN_PASSWORD is `pass1234` and default secret is `dev-secret` (development only).

4) Training models
- The AI service includes a training script `ai-service/train_full.py` which writes joblib pipeline artifacts to `ai-service/ai_models/`.
- After saving new models into `ai_models/`, you can tell the running FastAPI service to reload them via `POST /admin/reload`.

5) Database and migrations
- The backend supports a small SQLite database for applications. A migration script is available at `backend/migrations/init_db.js`. Run `npm run migrate` inside `backend` to create the database and tables.

6) Useful local commands (zsh)

```bash
# backend: install deps and run migrations
cd backend
npm install
npm run migrate
npm start

# ai-service: create venv, install, run training (demo) and start server
cd ../ai-service
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python train_full.py --data data/train.csv --out ai_models --class_target risk --hyper
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000

# frontend
cd ../frontend
npm install
npm start
```

Notes
- These defaults are intended for local development only. Do not use default secrets in production. For production, use proper secrets management, stronger JWT secrets, HTTPS, and a production database.

If you'd like, I can run the demo training here and push the generated models to `ai-service/ai_models/`, and run migrations locally. Tell me if you want me to proceed and whether you want to use the included demo CSV or provide your own.
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

