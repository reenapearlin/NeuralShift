#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Missing .env. Run: cp .env.example .env"
  exit 1
fi

llm_model="$(grep -E '^RAG_LLM_MODEL=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
embed_model="$(grep -E '^RAG_EMBEDDING_MODEL=' "$ROOT_DIR/.env" | head -n1 | cut -d'=' -f2-)"
llm_model="${llm_model:-llama3}"
embed_model="${embed_model:-nomic-embed-text}"
docker_bin="$(command -v docker 2>/dev/null || true)"
if [[ -z "$docker_bin" && -x "/Applications/Docker.app/Contents/Resources/bin/docker" ]]; then
  docker_bin="/Applications/Docker.app/Contents/Resources/bin/docker"
fi

if [[ -n "$docker_bin" ]] && "$docker_bin" compose ps ollama --status running >/dev/null 2>&1; then
  echo "Pulling Ollama models in container..."
  "$docker_bin" compose exec -T ollama ollama pull "$llm_model"
  "$docker_bin" compose exec -T ollama ollama pull "$embed_model"
else
  echo "Ollama container not running. Pulling on host..."
  ollama pull "$llm_model"
  ollama pull "$embed_model"
fi

echo "Ollama models ready: $llm_model, $embed_model"
