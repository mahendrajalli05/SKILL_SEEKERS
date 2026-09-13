# SARVSAKSHI

MPLADS Project Integrity & Investigation Layer · SIH 2026 · SIH26102

AI recommends. Authorized officers decide. The system outputs **investigation priority** and **evidence confidence**. It does not produce a legal fraud finding, does not sanction works, and does not release PFMS funds.

This repository is a **modular monolith**: Next.js + FastAPI + SQLite.

## Current slice

Phase 1 foundation plus Phase 2 profiling, work-level cleaning, and SQLite load:

- Frontend route skeleton
- FastAPI health and project count
- SQLite master schema from the cleaned extract (`data/processed/sarvsakshi.db`)
- Logging and error handlers
- Tests for health, SQLite, schema, raw-file profiling, work-level cleaning, and database load
- Read-only profiling of `data/raw/` into `DATA_PROFILING_REPORT.md` and `DATA_DICTIONARY.md`
- Cleaning of the primary GitHub work-level extract into `data/processed/mplads_works_cleaned.csv` (internal surrogate IDs; OpenCity files not merged)
- Load of every cleaned work into SQLite with provenance preserved

Not in this slice: ML engines, Copilot, relationship graph UI, Jan-Sakshi, milestone advisor, satellite/geospatial CV, or payments.

## Prerequisites

- Python 3.11+ (3.14 is acceptable if packages install)
- Node.js 20+
- Windows PowerShell or a Unix shell

## Setup

From the repository root:

```powershell
copy .env.example .env
copy frontend\.env.example frontend\.env.local
```

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

```powershell
cd frontend
npm install
```

## Run

Terminal 1 — API (from `backend/`):

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — UI (from `frontend/`):

```powershell
npm run dev
```

- API: http://127.0.0.1:8000/api/v1/health
- UI: http://localhost:3000

SQLite is created at `data/processed/sarvsakshi.db`. Initialise schema and load the cleaned extract with:

```powershell
cd backend
python -m app.pipeline.db_load_run
```

`GET /api/v1/projects` returns the loaded work count. Item listing waits for Search. `internal_project_id` is an internal surrogate, not an official MPLADS ID.

## Tests

```powershell
cd backend
pytest
python -m app.pipeline.run
python -m app.pipeline.clean_run
python -m app.pipeline.db_load_run
```

Profiling writes `DATA_PROFILING_REPORT.md` and `DATA_DICTIONARY.md` from files in `data/raw/` without modifying those files.

Cleaning reads only `github_vonter_india-mplads-works_MPLADS.csv`, writes `data/processed/mplads_works_cleaned.csv`, and documents limitations in `DATA_CLEANING_REPORT.md`. `internal_project_id` is an internal surrogate, not an official MPLADS ID.

SQLite load reads that cleaned CSV into `data/processed/sarvsakshi.db` and checks that the project row count matches the CSV. Schema: `DATABASE_SCHEMA.md`.

## Governance reminders

- Do not invent government fields or values.
- Label every synthetic demo/test row `SYNTHETIC`.
- Compliance explanations are rule-trace, not SHAP.
- Copilot will use templates first; `SARVSAKSHI_LLM_ENABLED` stays false until isolated LLM work is approved.
- Need & Impact stays partial until external census/infra sources exist.
- Jan-Sakshi and milestone UI wait until the P0 four-case demo path works.

## Layout

See `ARCHITECTURE.md` and `AGENTS.md`.
