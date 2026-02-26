# Legal 138 AI - Full Local Setup

## Prerequisites
- Docker + Docker Compose
- Python 3.11 (recommended)
- Node.js 18+
- npm

## One-time Setup
```bash
make setup
```

## Start Infrastructure
```bash
make infra-up
make ollama-pull-models
```

## Run DB Migrations
```bash
make migrate
```

## Run Application
Use two terminals:

Terminal 1:
```bash
make backend
```

Terminal 2:
```bash
make frontend
```

## Endpoints
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Ollama API: `http://localhost:11434`

## Stop Infrastructure
```bash
make infra-down
```
