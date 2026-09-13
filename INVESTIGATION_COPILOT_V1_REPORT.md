# Investigation Copilot V1 report

Date: 2026-09-10  
Layer: `investigation-copilot-v1`  
HTTP:

- `POST /api/v1/projects/{id}/copilot/chat`
- `GET  /api/v1/projects/{id}/copilot/context`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, AP pilot / State → Constituency, Scheme ID, Digital Passport, Investigation Workspace (except the new Copilot panel), Plan → Claim → Evidence, Document / Blueprint, Image Evidence, Image Forensics, Geospatial Consistency, Satellite / Remote-Sensing V1, Need & Impact, Milestone Advisor, Jan-Sakshi.

This slice adds an **evidence-grounded Investigation Assistant** for authorized officers. It explains stored SARVSAKSHI project data and Evidence Objects. It is **not** a general chatbot. It does **not** recalculate intelligence scores, change Investigation Priority, determine fraud, sanction a project, or release funds.

---

## Architecture

```
Officer question
        ↓
Intent / query parsing (deterministic)
        ↓
Structured retrieval of stored project / evidence / fusion / PCE / field layers
        ↓
Optional lexical retrieval over document text, citizen observations, explanations
        ↓
Evidence context construction
  observed facts | derived findings | missing | data mode
        ↓
LLM provider abstraction
  default: deterministic grounded templates
  optional local model if configured
  optional external model only if explicitly allowed
        ↓
Grounding validation + guardrails
        ↓
ANSWER / WHY / EVIDENCE / MISSING / RECOMMENDED ACTION
+ evidence IDs + REAL/HYBRID/SYNTHETIC notice
```

The Copilot reads existing APIs and stored rows. It does not implement a second Cost, Time, Overlap, Compliance, or Risk Fusion engine.

Risk Fusion V1.1 is explained only. Chat never writes `fusion_score`.

---

## Retrieval flow

Prefer structured database retrieval:

| Tool | Source | Side effects |
| --- | --- | --- |
| Project fields / Scheme ID | `project` + Scheme ID helper | none |
| Evidence Objects | `list_project_evidence` | none |
| Risk / contributing signals | stored `fusion_score` if mode matches; otherwise `assess_project_risk(..., persist=False)` | none |
| Cost comparables | stored Cost evidence `comparables` | none |
| Overlap matches | stored Overlap evidence `comparables` | none |
| Plan → Claim → Evidence | `verify_project(..., persist=False)` | none |
| Documents | document rows; filesystem paths stripped | none |
| Images | `project_image_summary` | none |
| Citizen reports | `list_project_reports(..., include_location=False)` | GPS omitted |
| Milestones | `list_project_milestones` | read-only |
| Graph / geo / satellite / need / forensics | stored Evidence Objects for those engines | none |

Semantic retrieval is lexical token overlap over a small in-project corpus (evidence explanations, document extracts, citizen observation text). The whole database is not vectorized.

If a requested layer has no stored object, the Copilot says:

`That information is not available in the current evidence.`

It does not guess.

---

## Grounding rules

- Only cite evidence IDs, Scheme IDs, internal project IDs, and rule IDs that appear in the retrieved context.
- Preserve `NOT_ASSESSABLE` and `INCONCLUSIVE`. Do not convert them into low-risk claims.
- Distinguish observed project fields from derived engine findings.
- REAL answers never consume synthetic enrichment.
- HYBRID / SYNTHETIC status is always shown in `data_mode_notice`.
- Fabricated citations, invented scores, or unsupported guideline IDs fail validation and fall back to the deterministic answer.

---

## Provider abstraction

Configured with `SARVSAKSHI_` settings. No provider is hard-coded.

| Provider | When used |
| --- | --- |
| `deterministic` | Default. `SARVSAKSHI_LLM_ENABLED=false` (default). No API key required. |
| `local` | Only if LLM is enabled and `SARVSAKSHI_LLM_PROVIDER=local` with `SARVSAKSHI_LLM_BASE_URL`. |
| `external` | Only if LLM is enabled **and** `SARVSAKSHI_LLM_EXTERNAL_ALLOWED=true` **and** a key, model, and base URL are set. |

Sensitive project data is **not** sent externally by default. The application remains functional with no API key. If a local/external call fails, returns unstructured text, fails grounding, or violates guardrails, the deterministic template is used.

Prompts and full answers are not written to application logs. Logs record `project_id`, intent, provider, evidence count, and whether an LLM was used.

---

## Guardrails

Explicit checks reject:

- fabricated facts or citations
- unsupported causal claims that cite unknown IDs
- legal fraud claims (`this is fraud`, `fraud has been established`)
- unsupported government-rule IDs
- synthetic data presented as official MPLADS records
- hidden data-mode switching
- filesystem paths, API keys, and citizen GPS
- recommendations of automatic sanction, payment, PFMS release, or legal action

Allowed recommendations only:

- MONITOR
- REVIEW
- INSPECT
- NEED MORE INFORMATION

When uncertain:

`I don't have enough evidence to answer that confidently.`

---

## Conversation memory

Turns are stored on `copilot_turn` with a project-scoped `session_id`. At most eight recent turns are kept for that session. This is investigation-session memory, not unrestricted personal memory. Citizen GPS, filesystem paths, and LLM prompt payloads are not stored.

---

## API

`POST /api/v1/projects/{id}/copilot/chat`

Request: `{ question, session_id?, data_mode? }`

Response includes:

- `answer` (structured text)
- `sections` (ANSWER / WHY / EVIDENCE / MISSING / RECOMMENDED ACTION)
- `evidence_ids`
- `source_refs`
- `data_mode` / `data_mode_notice`
- `limitations`
- `recommended_action`
- `insufficient_evidence`
- `observed_facts` / `derived_findings` / `unavailable`
- `provider` / `used_llm`

`GET /api/v1/projects/{id}/copilot/context` returns suggested questions, data-mode notice, engines present, and recent session turns.

---

## Frontend

INVESTIGATION COPILOT is a panel on the existing Investigation Workspace. It adds chat input, history, suggested questions, source references (evidence IDs link to `#evidence-{id}`), REAL/HYBRID notice, loading state, and an insufficient-evidence state. The rest of the site layout is unchanged.

Suggested questions:

- Why is this project flagged?
- What evidence is strongest?
- Why is Time Intelligence inconclusive?
- Show comparable projects.
- What should I inspect next?
- Summarize Plan → Claim → Evidence.

---

## Example questions and answers

**Why is this project flagged?**

ANSWER: Investigation Priority is elevated.  
WHY: Stored Cost and Overlap Evidence Objects have disposition WHY_FLAGGED.  
EVIDENCE: Cost score = 67. Overlap score = 81. Citations use stored `ev:…` IDs.  
MISSING: layers with no Evidence Object, plus REAL unavailable fields when in REAL mode.  
RECOMMENDED ACTION: REVIEW or INSPECT from the stored fusion recommendation, mapped away from legal/payment language.

**Why is Time Intelligence inconclusive? (REAL)**

ANSWER: Time Intelligence cannot determine actual delay because verified execution dates are unavailable in the current real dataset.  
WHY: REAL mode uses recommendation date and observed status only.  
EVIDENCE: stored Time object if present, otherwise the REAL limitation.  
The Copilot preserves `NOT_ASSESSABLE`.

**Is this fraud?**

ANSWER: SARVSAKSHI does not determine legal fraud. Investigation Priority and Evidence Confidence are review rankings only. Authorized officers decide.

---

## LLM unavailable behaviour

If no LLM is configured, the local endpoint is down, the external allow-flag is off, or the model output fails grounding/guardrails, the officer still receives a structured, cited, template answer from stored evidence. `used_llm` is false and `provider` is `deterministic`.

---

## Limitations

- The Copilot explains stored outputs. It does not recompute Cost / Time / Overlap / Compliance / Risk Fusion.
- Satellite, GPS, vendor, expenditure, and verified execution dates remain unavailable in the current REAL extract unless a stored Evidence Object exists.
- Citizen GPS is never returned.
- Document filesystem paths are stripped.
- One citizen report is never treated as truth.
- Recommendations are investigation actions only, not administrative or legal decisions.
- Optional LLMs are off by default and must not be assumed to be running in demo environments.

---

## Tests

Controlled fixtures only. Covered: why flagged / why not flagged, supporting evidence, missing information, time inconclusive, comparables, PCE summary, inspect-next, missing evidence, conflicting evidence, REAL, HYBRID, unavailable satellite, unavailable GPS, citizen / milestone / graph evidence, hallucination prevention, source-reference preservation, no-fraud wording, no unsupported rule claims, deterministic retrieval, LLM unavailable fallback, Risk Fusion scores unchanged after chat.
