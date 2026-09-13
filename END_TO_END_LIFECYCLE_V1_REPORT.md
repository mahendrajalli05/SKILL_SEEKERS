# End-to-End Project Lifecycle Orchestration V1 report

Date: 2026-09-10  
Layer: `lifecycle-orchestration-v1`  
HTTP:

- `GET  /api/v2/projects/{id}/lifecycle`
- `POST /api/v2/projects/{id}/lifecycle/decision`

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph V1, Image Evidence V1, Image Forensics V1, Geospatial V1, Satellite V1, Document/Blueprint V1, Plan→Claim→Evidence V1, Milestone Advisor V1, Jan-Sakshi V1, Need & Impact V1 scoring, Investigation Copilot V1 architecture (retrieval/intent/templates only extended for lifecycle context).

This slice adds an **application-level workflow** that connects already-built modules into three complete project lifecycle paths: FUTURE / PROPOSED, ONGOING, and COMPLETED. It does **not** rewrite intelligence engines, does not add Risk Fusion V2 weights, does not create duplicate Evidence Objects, does not sanction a project, and does not release funds.

---

## Architecture

```
Observed project.lifecycle_stage (FUTURE / ONGOING / COMPLETED / UNKNOWN from STATUS)
        +
Stored Evidence Objects, Need & Impact, PCE, Milestones, Risk Fusion V2,
citizen / geo / satellite / document / image / graph summaries
        +
Officer planning decisions (FUTURE) and investigation / milestone decisions
        ↓
Deterministic SARVSAKSHI workflow state machine
        ↓
GET /api/v2/projects/{id}/lifecycle
        ↓
Digital Passport + Investigation Workspace LIFECYCLE section
        ↓
Copilot can answer where the work is, what remains, and last milestone decision
```

The orchestration layer **reads** existing services with `persist=False` where those services would otherwise write. It does not recalculate Cost, Time, Overlap, Compliance, or the Risk Fusion V2 formula.

Risk Fusion V1.1 remains at `GET /api/v1/projects/{id}/risk`.  
Risk Fusion V2 remains at `GET /api/v2/projects/{id}/risk`.

---

## 1. Future workflow

Flow:

Proposed project → Need & Impact → Priority recommendation → Officer planning decision

Displayed:

- project, constituency, category, requested amount
- Need Score, Impact Score, Priority, Evidence Confidence
- unavailable inputs
- recommendation rationale

Administrative workflow states (SARVSAKSHI only, not official MPLADS status):

- `PLANNING` (default)
- `PRIORITIZED`
- `DEFERRED`
- `NEEDS_MORE_INFORMATION`

`POST /api/v2/projects/{id}/lifecycle/decision` accepts `PRIORITIZE`, `DEFER`, `NEED_MORE_INFORMATION`, `RETURN_TO_PLANNING`. These actions are audited and **do not sanction**. `automatic_sanction` is always `false`.

Risk Fusion V2 is **not** the primary FUTURE workflow. Need & Impact is.

---

## 2. Ongoing workflow

Flow:

Project → Plan → Claim → Evidence → Milestone → Risk Fusion V2 → Investigation → Officer decision → next milestone

Integrated by reading existing modules:

Cost, Time, Overlap, Compliance, Documents, Images, Image Forensics, Geospatial, Satellite (when actually available), Jan-Sakshi, Milestones, Relationship Graph, PCE, Risk Fusion V2, Copilot.

Current stage is the first incomplete node: PLAN, then CLAIM, then EVIDENCE, then MILESTONE if recorded, then RISK_FUSION / INVESTIGATION / OFFICER_DECISION.

Milestone PROCEED / HOLD / INSPECT / NEED MORE INFORMATION remain on Milestone Advisor. Investigation CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION remain on the existing officer-decision API. Scores are unchanged.

---

## 3. Completed workflow

Flow:

Completed project → final claim / evidence / documents / images / geospatial / satellite if available / citizen evidence → Risk Fusion V2 → Investigation Workspace → officer decision → final case summary

If stored evidence is insufficient, the final case result is **INCONCLUSIVE**.

Completion dates and expenditure are **not invented**. Those fields are returned as `null` with an explicit note.

---

## 4. State machine

Two labels are always distinct:

| Label | Source | Values |
| --- | --- | --- |
| **SARVSAKSHI workflow state** | `project.lifecycle_stage` derived from observed STATUS | FUTURE / ONGOING / COMPLETED / UNKNOWN |
| **Source status** | `project.status` | observed extract STATUS text |

Officer planning decisions do **not** change `project.lifecycle_stage`.

`current_stage` is a finer workflow node (PRIORITIZATION, PLAN, CLAIM, EVIDENCE, MILESTONE, RISK_FUSION, FINAL_INVESTIGATION, …).

---

## 5. Timeline

Reusable order:

FUTURE → PRIORITIZATION → ONGOING → PLAN → CLAIM → EVIDENCE → MILESTONE → RISK_FUSION → INVESTIGATION → OFFICER_DECISION → COMPLETION → FINAL_INVESTIGATION

Not every project contains every node. Missing steps are `NOT AVAILABLE` or `INCONCLUSIVE`. Unavailable is not treated as suspicious.

---

## 6. Common evidence layer

All paths use existing Evidence Object V1 records. Lifecycle does not insert duplicate evidence. Summaries list stored `evidence_ids` by engine.

---

## 7. Risk Fusion V2

Used when the work is ONGOING or COMPLETED (or UNKNOWN with investigation evidence).

The V2 formula is not changed. Lifecycle asserts frozen weights:

| Group | Weight |
| --- | ---: |
| cost | 0.14 |
| time | 0.10 |
| overlap | 0.10 |
| compliance | 0.10 |
| graph | 0.08 |
| document | 0.06 |
| image | 0.06 |
| forensics | 0.05 |
| geospatial | 0.08 |
| satellite | 0.07 |
| citizen | 0.06 |
| milestone | 0.05 |
| pce | 0.05 |
| need | 0.00 |

If a V2 row is already stored for the data mode, lifecycle displays it. Otherwise it calls `assess_project_risk_v2(..., persist=False)`.

---

## 8. REAL / HYBRID / SYNTHETIC

- REAL: observed extract only. Synthetic enrichment is not consumed.
- HYBRID: real project plus clearly labelled synthetic enrichment.
- SYNTHETIC: test-only. Never presented as a government finding.

The lifecycle payload always includes `data_mode`. Explanation text discloses HYBRID/SYNTHETIC. Andhra Pradesh remains the current pilot. Non-AP rows are not deleted.

---

## 9. Officer decision points

| Path | Actions | Where recorded |
| --- | --- | --- |
| FUTURE | PRIORITIZE / DEFER / NEED MORE INFORMATION | `lifecycle_decision` + audit |
| ONGOING milestone | PROCEED / HOLD / INSPECT / NEED MORE INFORMATION | Milestone Advisor |
| Investigation | CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION | `officer_decision` |
| COMPLETED | same investigation actions; INCONCLUSIVE if evidence is insufficient | Investigation Workspace |

None of these overwrite Investigation Priority or Evidence Confidence. None are automatic sanctions or payments. None conclude legal fraud.

---

## 10. Project status summary

Unified summary includes only fields that exist for the project, from:

Lifecycle state, Investigation Priority, Evidence Confidence, Need & Impact, milestone status, citizen evidence, geospatial, satellite, documents, images, compliance, relationship graph.

---

## 11. Frontend

Digital Passport and Investigation Workspace gained a **LIFECYCLE** section (`ProjectLifecyclePanel`).

It highlights Future / Ongoing / Completed, shows the timeline, status summary, FUTURE Need & Impact block, Risk Fusion V2 when appropriate, final case summary when completed, and navigation into the relevant module. The rest of the application layout is unchanged.

---

## 12. Copilot

Copilot was not rebuilt. Minimal context:

| Question | Intent |
| --- | --- |
| Where is this project in its lifecycle? | `LIFECYCLE_WHERE` |
| What remains to be verified? | `LIFECYCLE_REMAINING` |
| What was the last milestone decision? | `LIFECYCLE_LAST_MILESTONE` |
| What evidence is missing? | existing `MISSING_INFORMATION` (now includes pending lifecycle stages) |

---

## 13. Demo cases (controlled fixtures, no new dataset)

| Case | Path | Data mode | What it shows |
| --- | --- | --- | --- |
| A. FUTURE DEMO | Unsanctioned work | REAL or HYBRID | Need & Impact + planning states. HYBRID enrichment labelled. Not a sanction. |
| B. ONGOING DEMO | Plan + claim + milestone + Risk Fusion V2 | REAL / HYBRID | Current stage walks Plan → Claim → Evidence → Milestone → Risk. |
| C. COMPLETED DEMO | Completed STATUS, little or no field evidence | REAL | Final case **INCONCLUSIVE**. No invented completion date or expenditure. |

---

## 14. V1.1 / V2 compatibility

| Endpoint | Role |
| --- | --- |
| `GET /api/v1/projects/{id}/risk` | Risk Fusion V1.1 unchanged |
| `GET /api/v2/projects/{id}/risk` | Risk Fusion V2 unchanged |
| `GET /api/v2/projects/{id}/lifecycle` | Orchestration only |

---

## Limitations

- `lifecycle_stage` is derived from observed STATUS only. There is no official MPLADS lifecycle API.
- REAL Need & Impact remains largely INCONCLUSIVE without census/infra sources.
- REAL GPS, satellite, expenditure, and completion dates stay unavailable when the extract does not contain them.
- Timeline nodes that were never recorded are NOT AVAILABLE; the system does not invent a prior FUTURE record for an ONGOING extract row.
- Planning PRIORITIZED is not a government sanction.
- No labelled investigation dataset; this report does not claim accuracy.

---

## Governance safeguards

- Investigation Priority and Evidence Confidence remain the officer-facing scores.
- No legal fraud finding, fraud probability, automatic sanction, or PFMS/payment.
- Unavailable ≠ zero risk and ≠ suspicious.
- INCONCLUSIVE when completed evidence is insufficient.
- Synthetic/hybrid disclosure is retained.
- Officer and planning actions are audited and do not mutate scores.

---

## Tests run

- Full backend pytest: passed
- Full frontend vitest: 75 passed
- Next.js build: passed
