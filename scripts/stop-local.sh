#!/usr/bin/env bash
set -euo pipefail

echo "Stopping local services (if running)"
for p in sp-backend sp-ai sp-blockchain; do
  pidfile="/tmp/${p}.pid"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "Killing $pid from $pidfile"
      kill "$pid" || true
      rm -f "$pidfile"
    else
      rm -f "$pidfile" || true
    fi
  fi
done
echo "Stopped. Logs are in /tmp/sp-*.log"
