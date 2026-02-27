#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

host="$(grep -E '^POSTGRES_HOST=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
port="$(grep -E '^POSTGRES_PORT=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
user="$(grep -E '^POSTGRES_USER=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
db="$(grep -E '^POSTGRES_DB=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
password="$(grep -E '^POSTGRES_PASSWORD=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"

host="${host:-localhost}"
port="${port:-5434}"
user="${user:-postgres}"
db="${db:-neuralshift}"
password="${password:-postgres}"

echo "Waiting for PostgreSQL at ${host}:${port}..."
for _ in {1..30}; do
  if PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" >/dev/null 2>&1; then
    echo "PostgreSQL is ready."
    exit 0
  fi
  sleep 2
done

echo "PostgreSQL did not become ready in time."
exit 1
