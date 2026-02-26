#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Missing .env. Run: cp .env.example .env"
  exit 1
fi

vite_api_base_url="$(grep -E '^VITE_API_BASE_URL=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
export VITE_API_BASE_URL="${vite_api_base_url:-http://localhost:8000}"

exec npm --prefix "$ROOT_DIR/frontend" run dev -- --host
