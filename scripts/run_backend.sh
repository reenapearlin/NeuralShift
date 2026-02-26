#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Missing .env. Run: cp .env.example .env"
  exit 1
fi

exec "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir "$ROOT_DIR/backend"
