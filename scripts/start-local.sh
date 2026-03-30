#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
echo "Starting local services from $ROOT_DIR"

# Start blockchain-sim on 7001
echo "Starting blockchain-sim on 7001..."
PORT=7001 node "$ROOT_DIR/blockchain-sim/server.js" &>/tmp/sp-blockchain.log & echo $! > /tmp/sp-blockchain.pid
sleep 0.4
tail -n 20 /tmp/sp-blockchain.log || true

# Start ai-service using venv if available
echo "Starting ai-service on 8000..."
if [ -x "$ROOT_DIR/ai-service/.venv/bin/uvicorn" ]; then
  (cd "$ROOT_DIR/ai-service" && "$ROOT_DIR/ai-service/.venv/bin/uvicorn" main:app --host 127.0.0.1 --port 8000 &>/tmp/sp-ai.log & echo $! > /tmp/sp-ai.pid)
else
  echo "No venv uvicorn found. Attempting to run 'uvicorn' from PATH"
  (cd "$ROOT_DIR/ai-service" && uvicorn main:app --host 127.0.0.1 --port 8000 &>/tmp/sp-ai.log & echo $! > /tmp/sp-ai.pid)
fi
sleep 0.6
tail -n 40 /tmp/sp-ai.log || true

# Start backend pointing to local ai and blockchain
echo "Starting backend on 5001..."
AI_URL=http://127.0.0.1:8000 BLOCKCHAIN_URL=http://127.0.0.1:7001 PORT=5001 node "$ROOT_DIR/backend/server.js" &>/tmp/sp-backend.log & echo $! > /tmp/sp-backend.pid
sleep 0.4
tail -n 40 /tmp/sp-backend.log || true

echo "All services started. Check /tmp/sp-*.log for logs."
