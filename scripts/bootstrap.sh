#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/5] Preparing environment file..."
if [[ ! -f "$ROOT_DIR/.env" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created .env from .env.example"
else
  echo ".env already exists, keeping current values"
fi

echo "[2/5] Creating Python virtual environment..."
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi

echo "[3/5] Installing backend dependencies..."
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/python" -m pip install -r "$ROOT_DIR/backend/requirements.txt"

echo "[4/5] Installing frontend dependencies..."
npm --prefix "$ROOT_DIR/frontend" ci

echo "[5/5] Ensuring backend storage directories..."
mkdir -p "$ROOT_DIR/backend/storage/casefiles" "$ROOT_DIR/backend/storage/faiss"

echo "Bootstrap complete."
echo "Next: run 'make infra-up', then 'make ollama-pull-models', then 'make dev'."
