# SARVSAKSHI

MPLADS Project Integrity & Investigation Layer · SIH 2026 · SIH26102

AI recommends. Authorized officers decide. The system outputs **investigation priority** and **evidence confidence**. It does not produce a legal fraud finding, does not sanction works, and does not release PFMS funds.

This repository is a **modular monolith**: Next.js + FastAPI + SQLite.

## Current slice

Project foundation only:

- Frontend route skeleton
- FastAPI health and empty project list
- Nullable-first SQLite schema (no seed data)
- Logging and error handlers
- Tests for health, SQLite, and schema nullability

Not in this slice: ML engines, Copilot, relationship graph UI, Jan-Sakshi, milestone advisor, satellite/geospatial CV, payments, or datasets.

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

SQLite is created on API startup at `data/processed/sarvsakshi.db`. The project table stays empty until a real public MPLADS extract is ingested.

## Tests

```powershell
cd backend
pytest
```

## Governance reminders

- Do not invent government fields or values.
- Label every synthetic demo/test row `SYNTHETIC`.
- Compliance explanations are rule-trace, not SHAP.
- Copilot will use templates first; `SARVSAKSHI_LLM_ENABLED` stays false until isolated LLM work is approved.
- Need & Impact stays partial until external census/infra sources exist.
- Jan-Sakshi and milestone UI wait until the P0 four-case demo path works.

## Layout

See `ARCHITECTURE.md` and `AGENTS.md`.
