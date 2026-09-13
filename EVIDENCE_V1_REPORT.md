# Evidence Object V1 report

Date: 2026-09-10  
Layer: `evidence-object-v1`  
HTTP: `GET /api/v1/projects/{id}/evidence`

This slice adds a **shared, auditable Evidence Object** that Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, and Compliance Engine V1 already write. Later Graph, Document, Image, Geospatial, Citizen, and Milestone engines can use the same envelope.

It does **not** run Risk Fusion and does **not** assign Investigation Priority.

Cost V1.1 scoring, Time V1 scoring, Overlap V1 scoring, and Compliance rule logic were not changed.

---

## Evidence schema

Canonical fields:

| Field | Role |
| --- | --- |
| `evidence_id` | Deterministic public ID: `ev:{engine}:{project_id}:{signal}:{data_mode}:{digest}` |
| `project_id` | SQLite `project.id` |
| `signal_type` | `allocation_cost_anomaly`, `time_anomaly`, `potential_overlap`, `mplads_compliance`, plus reserved future types |
| `finding` | Derived finding text (not a legal conclusion) |
| `severity` | `info` / `watch` / `attention` |
| `score` | Engine 0–100 score when produced; otherwise omitted |
| `confidence` | 0.0–1.0 (engine 0–100 Evidence Confidence ÷ 100) |
| `source_type` | Primary source class |
| `source_ids` | Preserved identifiers (`internal_project_id`, peer/project ids, rule IDs, guideline refs) |
| `evidence_facts` | Observation and derived key/value facts, each with `source` |
| `explanation` | Full WHY FLAGGED / WHY NOT FLAGGED / INCONCLUSIVE / NOT_ASSESSABLE text |
| `engine_name` | `cost` / `time` / `overlap` / `compliance` (later: graph, document, image, geo, citizen, milestone) |
| `engine_version` | Frozen engine version |
| `created_at` | Persist timestamp |
| `data_mode` | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance` | Required source trail; cannot be empty |
| `disposition` | `WHY_FLAGGED` / `WHY_NOT_FLAGGED` / `INCONCLUSIVE` / `NOT_ASSESSABLE` |

Every object distinguishes:

1. **Observation/fact** — recorded values (`fact_kind=OBSERVATION`), e.g. actual allocation  
2. **Derived finding** — `finding` plus `DERIVED` facts  
3. **Score** — optional engine score  
4. **Confidence** — separate from score  
5. **Source/provenance** — `source_type`, `source_ids`, fact `source`, `provenance`

Existing tables `evidence_object` and `evidence_fact` were extended. No duplicate evidence tables. SQLite PK `id` remains the FK used by `evidence_fact.evidence_id`. The public identifier is the string column `evidence_object.evidence_id`.

`init_db()` adds missing V1 columns on an existing database without dropping rows or fabricating evidence.

---

## Lifecycle

```
Engine assessment (frozen scoring / rules)
        ↓
Adapter (Cost / Time / Overlap / Compliance)
        ↓
validate (required fields, provenance, REAL vs SYNTHETIC, no fraud language,
          no scenario-label inputs)
        ↓
persist to evidence_object + evidence_fact
        ↓
GET /api/v1/projects/{id}/evidence
```

Re-running an engine replaces that engine’s evidence for the project. The `evidence_id` is stable for the same engine, version, project, signal, and data mode.

This layer does not write `fusion_score`.

---

## Provenance model

Provenance is required and is stored as JSON on the evidence row. It is also copied onto each fact via `source`.

REAL:

- `source_type=mplads_project_record`
- `enrichment_used=false`
- cites cleaned extract dataset / snapshot URL when available
- must never use `SYNTHETIC` as `data_mode` or `source_type`

HYBRID:

- `source_type=hybrid_enrichment`
- `enrichment_used=true`
- cites `data/synthetic/sarvsakshi_synthetic_enrichment.csv`
- notes that synthetic fields are not official MPLADS values

SYNTHETIC:

- unit-test / placeholder `project.is_synthetic=true` rows only
- notes must state SYNTHETIC
- not presented as a government project

`source_ids` always includes the subject `internal_project_id`. REAL evidence without a dataset or source URL is rejected.

Held-out columns are **not** evidence inputs and are rejected if present as fact keys:

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, `coordinate_source`, and related label columns.

Evidence text may not claim fraud.

---

## Engine integration

Adapters convert existing engine results. Analytical functions were not modified.

| Engine | Signal | Score field | REAL | HYBRID |
| --- | --- | --- | --- | --- |
| Cost `cost-peer-v1.1` | `allocation_cost_anomaly` | `cost_anomaly_score` | observed allocation vs peers | Cost V1.1 does not use enrichment as inputs; synthetic test rows are `SYNTHETIC` |
| Time `time-peer-v1` | `time_anomaly` | `time_anomaly_score` when produced | recommendation date + status only → `NOT_ASSESSABLE` | synthetic dates/progress; labelled HYBRID |
| Overlap `overlap-multi-v1` | `potential_overlap` | `overlap_score` | work text / category / constituency / amount / date / place | GPS only in HYBRID_TEST |
| Compliance `compliance-rules-v1` | `mplads_compliance` | none (rule-trace, not a 0–100 anomaly score) | missing sanction/expenditure fields stay `NOT_ASSESSABLE` on those rules | spend/timeline rules may trigger |

Disposition mapping (evidence layer only):

| Disposition | Typical engine outcome |
| --- | --- |
| `WHY_FLAGGED` | Cost anomaly; Time anomaly; Potential Overlap/Duplicate; rules triggered |
| `WHY_NOT_FLAGGED` | Within peer/schedule range; not linked; assessable rules not triggered |
| `INCONCLUSIVE` | Cost insufficient peers; Overlap insufficient candidates |
| `NOT_ASSESSABLE` | Invalid/zero allocation; Time REAL missing execution dates; invalid dates; all compliance rules not assessable |

HTTP retrieval: `GET /api/v1/projects/{id}/evidence` with optional `engine`, `data_mode`, `signal_type`. Engine routes are unchanged.

---

## Example REAL evidence

Illustrative Cost object (in-memory peers; same frozen Cost V1.1 mapping). Observation vs derived:

- FACT: `Actual allocation = 500,000` (`project.allocation_amount`)  
- DERIVED FINDING: `Allocation is 0.5% above peer median`  
- SCORE: `5`  
- CONFIDENCE: `0.82`  
- SOURCE: real MPLADS project records  

```json
{
  "evidence_id": "ev:cost:3715:allocation_cost_anomaly:REAL:54b16a9d36a46007",
  "project_id": 3715,
  "signal_type": "allocation_cost_anomaly",
  "finding": "Allocation is 0.5% above peer median",
  "disposition": "WHY_NOT_FLAGGED",
  "severity": "info",
  "score": 5,
  "confidence": 0.82,
  "source_type": "mplads_project_record",
  "engine_name": "cost",
  "engine_version": "cost-peer-v1.1",
  "data_mode": "REAL",
  "provenance": {
    "enrichment_used": false,
    "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
    "notes": "real MPLADS project records from the cleaned work-level extract."
  }
}
```

Time REAL (execution dates absent; duration not fabricated):

```json
{
  "evidence_id": "ev:time:217:time_anomaly:REAL:f5e01001a773dcc0",
  "signal_type": "time_anomaly",
  "finding": "Time Anomaly is not assessable: the real extract has recommendation date and status only. Execution duration is not fabricated.",
  "disposition": "NOT_ASSESSABLE",
  "score": null,
  "confidence": 0.12,
  "source_type": "mplads_project_record",
  "data_mode": "REAL",
  "engine_version": "time-peer-v1"
}
```

Overlap REAL (identical observed titles with supporting signals — review queue, not a legal duplicate finding):

```json
{
  "signal_type": "potential_overlap",
  "finding": "Potential Duplicate: high semantic similarity with supporting signals",
  "disposition": "WHY_FLAGGED",
  "score": 100,
  "confidence": 0.66,
  "source_type": "mplads_project_record",
  "data_mode": "REAL",
  "engine_version": "overlap-multi-v1"
}
```

Compliance REAL (IDA present so R015 is assessable; sanction/expenditure rules remain not assessable):

```json
{
  "signal_type": "mplads_compliance",
  "finding": "Assessable guideline rules were not triggered",
  "disposition": "WHY_NOT_FLAGGED",
  "score": null,
  "source_type": "mplads_project_record",
  "data_mode": "REAL",
  "engine_version": "compliance-rules-v1"
}
```

Rule IDs and guideline references are stored on the object. Missing government fields are not invented.

---

## Example HYBRID evidence

HYBRID Time (synthetic schedule/progress; not a real MPLADS delay statistic):

```json
{
  "evidence_id": "ev:time:52862:time_anomaly:HYBRID:830dd5434e8fc827",
  "signal_type": "time_anomaly",
  "finding": "Schedule is behind plan: 135.9% of planned time consumed versus 12% physical progress",
  "disposition": "WHY_FLAGGED",
  "score": 100,
  "confidence": 0.56,
  "source_type": "hybrid_enrichment",
  "data_mode": "HYBRID",
  "provenance": {
    "enrichment_used": true,
    "enrichment_path": "data/synthetic/sarvsakshi_synthetic_enrichment.csv",
    "notes": "HYBRID/TEST: observed MPLADS fields plus synthetic enrichment. Synthetic fields are not official MPLADS values."
  }
}
```

HYBRID Compliance (synthetic expenditure above sanctioned; held-out `OVERBILL` was not a rule input):

```json
{
  "signal_type": "mplads_compliance",
  "finding": "Guideline rules triggered for review: R004",
  "disposition": "WHY_FLAGGED",
  "score": null,
  "source_type": "hybrid_enrichment",
  "data_mode": "HYBRID",
  "source_ids": ["internal:ex:comp:22177", "R004"]
}
```

REAL and HYBRID remain distinguishable (`data_mode`, `source_type`, `enrichment_used`). REAL objects cannot be marked SYNTHETIC.

---

## Tests

**299** backend tests passed (0 failed), including prior Cost/Time/Overlap/Compliance suites plus Evidence V1:

- schema and required fields  
- provenance required and preserved  
- REAL vs HYBRID vs SYNTHETIC  
- deterministic `evidence_id`  
- source reference preservation  
- WHY_FLAGGED / WHY_NOT_FLAGGED / INCONCLUSIVE / NOT_ASSESSABLE  
- invalid evidence rejection  
- no-fraud-claim guard  
- synthetic scenario labels excluded from operational evidence inputs  
- compatibility with Cost / Time / Overlap / Compliance outputs  
- `GET /api/v1/projects/{id}/evidence`  

```powershell
cd backend
python -m pytest
```

---

## Limitations

- This layer stores and retrieves evidence. It does not fuse Investigation Priority.  
- Confidence for Compliance is a completeness mapping of assessable vs total rules, not a new ML score and not fused Evidence Confidence.  
- Cost V1.1 has no HYBRID-TEST mode; HYBRID labels stay held-out. Synthetic SQLite test rows are `SYNTHETIC`.  
- Time REAL cannot produce a Time Anomaly score; duration is not fabricated.  
- Overlap REAL has no GPS.  
- Compliance REAL cannot assess rules that need unverified sanction, expenditure, district, GPS, or amount unit.  
- Generic repeated work titles can still produce Potential Duplicate evidence; that is a source-text limitation, not a legal finding.  
- Graph, document, image, geospatial, citizen, and milestone engines are not implemented; their `signal_type` values are reserved only.

STOP. Risk Fusion, Relationship Graph, Copilot, and frontend were not built in this slice.
