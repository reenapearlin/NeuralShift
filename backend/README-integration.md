# Backend Integration Guide

This file standardizes local backend setup for all team members.

## 1) Install dependencies

```powershell
cd backend
pip install -r requirements.txt
```

## 2) Configure environment

1. Copy `.env.example` to `.env`
2. Set valid local values for:
   - `DATABASE_URL` (or PG split config)
   - `SECRET_KEY`
   - `CASEFILES_ROOT_DIR`

## 3) Prepare local storage

```powershell
mkdir storage\casefiles
```

`backend/storage/` is intentionally not tracked with real files.

## 4) Run backend

```powershell
uvicorn app.main:app --reload
```

Open docs at: `http://127.0.0.1:8000/docs`

## 5) Auth sanity check

1. `POST /api/v1/auth/signup` (lawyer)
2. `POST /api/v1/auth/login`
3. Use Authorize flow (`/api/v1/auth/token`) for protected endpoints

## 6) Optional local PDF import

```powershell
python -m app.utils.import_casefiles --source-dir "D:\path\to\pdfs" --uploaded-by-email admin@neuralshift.ai
```

This copies PDFs into `backend/storage/casefiles` and inserts DB rows with relative paths.
