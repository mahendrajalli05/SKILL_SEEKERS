# SARVSAKSHI Architecture

Frozen for the MVP: **modular monolith** · Next.js + FastAPI + SQLite.
Master `project` columns follow the cleaned work-level extract. Absent
government fields are not stored.

## High-level flow

REAL MPLADS DATA
        ↓
DATA INGESTION
        ↓
DATA CLEANING / VALIDATION
        ↓
MASTER PROJECT DATABASE
        ↓
┌─────────────────────────────────────┐
│        INTELLIGENCE ENGINES         │
│                                     │
│ Cost                                │
│ Time                                │
│ Overlap / Similarity                │
│ Compliance                          │
│ Relationship Graph                  │
│ Evidence Intelligence               │
└─────────────────┬───────────────────┘
                  ↓
            EVIDENCE OBJECTS
                  ↓
             RISK FUSION
                  ↓
        Investigation Priority
        Evidence Confidence
                  ↓
        Project Digital Passport
                  ↓
         Investigation Workspace
                  ↓
          Human Officer Review
                  ↓
       Decision + Audit Trail

Future:
Need & Impact
Pre-sanction assessment

Ongoing:
Milestone + evidence verification

Completed:
Final integrity assessment

## Approved MVP decisions

- One FastAPI process owns data, engines, and HTTP. Next.js is a thin client.
- Outputs: investigation priority and evidence confidence. Never a legal fraud probability.
- No supervised fraud classifier. SHAP is not an MVP dependency. Compliance uses rule-trace.
- Copilot: deterministic evidence-grounded templates first; LLM optional, isolated, default off.
- Need & Impact: partial until census/infra/SC-ST sources are actually available.
- Jan-Sakshi and milestone UI are deferred until the P0 four-case demo path works.
- Do not invent government fields or values. Synthetic rows must be labelled `SYNTHETIC`.
- Isolation Forest may be added later as an optional unsupervised residual; not in this slice.

## Runtime

| Layer | Choice |
| --- | --- |
| Frontend | Next.js App Router + Tailwind |
| Backend | FastAPI |
| Database | SQLite at `data/processed/sarvsakshi.db` |
| Config | `.env` with `SARVSAKSHI_` prefix |

## API (foundation)

- `GET /api/v1/health` — process + SQLite connectivity
- `GET /api/v1/projects` — work count from SQLite; item listing waits for Search
- `GET /api/v1/projects/{id}` — SQLite primary key lookup after ingest (`id` is not an official MPLADS work number)

Intelligence, Copilot, graph, citizen, and milestone routes are not registered yet.

## Schema principle

`project` stores observed cleaned fields plus `source_*` originals and
`internal_project_id` (a SARVSAKSHI surrogate, not an official work ID).
District, vendor, GPS, expenditure, sanction date, and completion date are
absent from the extract and are not columns. Empty tables remain for later
evidence, fusion, graph, citizen, claim/milestone, and review rows.
`fusion_score` stores `investigation_priority` and `evidence_confidence` only.

See `DATABASE_SCHEMA.md`.
