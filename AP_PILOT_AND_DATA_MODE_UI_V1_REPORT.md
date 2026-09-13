# AP Pilot and Data-Mode UI V1 report

Date: 2026-09-10  
Slice: Andhra Pradesh application scope, State → Constituency search, SARVSAKSHI Scheme ID, REAL / HYBRID DEMO presentation  
Frozen engines: Cost V1.1, Time V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Relationship Graph V1

This slice corrects Search, the Project Digital Passport, and the Investigation Workspace so the officer-facing application matches the current Andhra Pradesh pilot and honestly separates real MPLADS extract fields from existing SYNTHETIC prototype enrichment.

It does **not** rebuild or recalculate Cost, Time, Overlap, Compliance, Evidence, Risk Fusion, or Relationship Graph. It does **not** create more synthetic data, modify `data/raw/`, modify real project rows, or delete non-Andhra Pradesh records.

---

## 1. AP scope behaviour

SARVSAKSHI remains one SQLite master database (`data/processed/sarvsakshi.db`) with every currently loaded state (56,138 cleaned works).

The **user-facing application scope** defaults to Andhra Pradesh:

- Header / Search: `Current Pilot: Andhra Pradesh`
- `GET /api/v1/projects` without an explicit state uses the current pilot
- Live check: default search total **3,640** Andhra Pradesh works; `apply_pilot_scope=false` still returns **56,138**

Scope is configurable with `SARVSAKSHI_PILOT_STATE`. No second AP-only database was created.

`GET /api/v1/scope` returns the current pilot, default data mode (HYBRID), and an explicit note that the database retains all states.

---

## 2. State → Constituency logic

Search filters are ordered:

1. State  
2. Constituency  
3. Category  
4. Status  
5. Text Search  

Behaviour:

| State selected | Constituency selector |
| --- | --- |
| No | Disabled; placeholder **Select state first**; options list is empty |
| Yes | Distinct **observed** constituencies for that state only |

Constituency options are **not** a hard-coded Election Commission list. They are derived from SQLite values for the selected state.

Geographic validation uses `app.geo.constituency.is_geographic_constituency`, wrapping the existing conservative classifier (same rules as Cost V1.1). Chamber labels such as `Sitting Rajya Sabha` and `Nominated Rajya Sabha` are excluded from geographic filtering. The original source value remains on the project record and is not replaced.

Live check on Andhra Pradesh options: 22 geographic constituencies; `Sitting Rajya Sabha` listed only under `excluded_non_geographic_constituencies`. Maharashtra options include `AKOLA` / `BARAMATI` and do not include `KURNOOL`.

If a non-geographic value is passed as `constituency=`, the API does not apply it as a geographic filter (`constituency_filter_applied=false`).

District, vendor, expenditure, GPS, sanction date, and completion date remain unavailable as filters.

---

## 3. Scheme ID design

The real MPLADS extract has no official work ID. `internal_project_id` remains the database key and is unchanged on `project` rows.

The application adds a computed **internal SARVSAKSHI Scheme ID**:

```
SVK-{STATE}-{NNNNNN}
```

Example: `SVK-AP-000001`

Properties:

- Deterministic: rank among works that share the same internal state code, ordered by `internal_project_id`
- Unique within the application for a frozen extract
- Stable / reproducible for the same project in the same extract
- Not stored on real project rows
- Labelled: **Internal SARVSAKSHI application identifier — not an official MPLADS Work ID.**

Andhra Pradesh uses internal code `AP`. Blank/unmapped state names use fallback `XX`. These abbreviations are application codes, not official MPLADS identifiers.

Search accepts Scheme ID, `internal_project_id`, work description, and MP name.

---

## 4. REAL vs HYBRID architecture

Two application data modes:

| Mode | Default | What the officer sees |
| --- | --- | --- |
| **HYBRID DEMO** | Yes (user-facing default) | Real extract fields **plus** existing 10,000-row SYNTHETIC enrichment, each synthetic field labelled |
| **REAL DATA** | Opt-in (`mode=real`) | Observed extract fields only. Synthetic enrichment is not returned and not displayed |

HYBRID DEMO is **not** a fully synthetic replacement dataset. Base project identity and recommendation fields remain the real extract. Enrichment is read from `data/synthetic/sarvsakshi_synthetic_enrichment.csv` for display only. Intelligence engines still use their own REAL / HYBRID-TEST inputs; this slice does not duplicate their calculations in the frontend.

Persistent HYBRID notice:

> HYBRID DEMO — Base project data comes from a real MPLADS extract. Fields marked SYNTHETIC are simulated prototype enrichment and are not official MPLADS records.

REAL notice states that synthetic enrichment is not used. Missing real fields render as **Unavailable in current public extract** or **Not assessable**, not as `0`, `0%`, or `N/A`.

---

## 5. Example search

`GET /api/v1/projects?page=1&page_size=3` (default HYBRID, AP scope)

| Field | Example |
| --- | --- |
| Pilot | Current Pilot: Andhra Pradesh |
| Total | 3,640 |
| Scheme ID | `SVK-AP-002021` |
| State | Andhra Pradesh |
| Data mode (row without enrichment) | REAL |
| Data mode (row with enrichment) | HYBRID + HYBRID badge |

Results columns: Scheme ID, work description, constituency, category, status, allocation, recommendation date, data mode.

`mode=real` forces every result `data_mode=REAL` even when a HYBRID enrichment row exists.

---

## 6. Example Passport

Real AP work without enrichment (`GET /api/v1/projects/234?mode=real`):

- Scheme ID `SVK-AP-002021`
- Internal Project ID preserved (`internal:…`)
- Data Mode REAL
- `synthetic_enrichment` is `null`
- Unavailable real fields include district, vendor, expenditure, GPS, sanction date, start date, completion date, physical progress, milestones — each with display **Unavailable in current public extract**

HYBRID AP work (`GET /api/v1/projects/26946?mode=hybrid`):

- Scheme ID `SVK-AP-003286`
- Data Mode HYBRID
- REAL SOURCE / RECOMMENDATION section keeps observed extract fields
- SYNTHETIC panel includes labelled implementing district, vendor, dates, expenditure, GPS, progress, milestones
- Same work with `mode=real` returns `synthetic_enrichment: null`

Passport sections: identifiers, PROJECT IDENTITY, REAL SOURCE / RECOMMENDATION, SYNTHETIC prototype enrichment, INTELLIGENCE (Investigation Priority, Evidence Confidence, Cost, Time, Overlap, Compliance), EVIDENCE, COMPARABLE PROJECTS, RELATIONSHIP SUMMARY, DATA AVAILABILITY.

---

## 7. Example Investigation Workspace

Officer header shows Scheme ID, Internal Project ID, Data Mode, Investigation Priority (0–100 when assessed), and Evidence Confidence (0–100 when assessed).

Workspace groups evidence as:

- WHY FLAGGED
- WHY NOT FLAGGED
- INCONCLUSIVE
- INSUFFICIENT EVIDENCE

Contributing signals: Cost, Time, Overlap, Compliance. Unavailable signals are listed separately and are not shown as assessed zeros.

Officer actions remain:

- CONFIRM CONCERN
- DISMISS
- NEED MORE INFORMATION

Live check on project `26946`: `need_more_info` stored; Investigation Priority and Evidence Confidence unchanged; `fraud_confirmed` rejected HTTP 422. There is no “Fraud Confirmed” button. Decisions do not create a legal finding.

---

## 8. Data integrity safeguards

- `data/raw/` not modified
- Real `project` rows not modified; Scheme ID is computed, not written onto the table
- Non-AP rows remain in SQLite (56,138 total)
- No fabricated official MPLADS Work ID, district, or government field
- Existing 10,000-record HYBRID layer reused; no new synthetic generation
- REAL mode never returns `synthetic_enrichment`
- Intelligence engine routes and scoring files were not rebuilt
- Live smoke: Cost still `cost-peer-v1.1`; risk response has no `fraud_probability`

---

## 9. API additions (backward compatible)

Existing search and project-detail routes remain. Additive query parameters / fields:

- `GET /api/v1/scope`
- `GET /api/v1/projects` — default AP scope, `mode`, `scheme_id`, `apply_pilot_scope`, Scheme ID on items
- `GET /api/v1/projects/options?state=` — cascading constituencies
- `GET /api/v1/projects/{id}?mode=real|hybrid` — Scheme ID, data mode, optional synthetic display payload

Analytical endpoints (`/cost-intelligence`, `/time-intelligence`, `/overlap-intelligence`, `/compliance`, `/evidence`, `/risk`, `/graph`) are unchanged.

---

## 10. Tests and verification

Backend: full pytest suite passed, including new tests for AP default scope, state filter, constituency dependency, non-geographic exclusion, Scheme ID uniqueness/stability, REAL vs HYBRID, and officer scores-unchanged.

Frontend: Vitest passed (search filters, Scheme ID display, REAL/HYBRID warnings, unavailable fields, officer actions, disposition groups).

`next build` succeeded.

Live API checks on the 56,138-row database:

| Check | Result |
| --- | --- |
| AP-only default search | 3,640 Andhra Pradesh works |
| Full database retained | 56,138 with `apply_pilot_scope=false` |
| State → Constituency | AP 22 geographic; Sitting Rajya Sabha excluded; MH list does not include KURNOOL |
| Scheme ID search | `SVK-AP-002021` returns one work |
| REAL mode | `synthetic_enrichment` null; all search `data_mode=REAL` |
| HYBRID mode | project `26946` returns labelled SYNTHETIC fields |
| Real AP project `234` | Scheme ID + unavailable real fields; no synthetic payload |
| Hybrid AP project `26946` | HYBRID notice + SYNTHETIC panel; REAL view hides enrichment |
| Officer decision | stored; scores unchanged; fraud action 422 |
| Frozen engines | Cost V1.1 still served; no fraud probability field |

Frontend routes `/search`, `/projects/234?mode=real`, `/projects/26946?mode=hybrid`, and `/projects/26946/investigate?mode=hybrid` returned HTTP 200. Interactive click-through in a browser automation tool was not used; API and page-load checks were used instead.

---

## 11. Limitations

- Scheme ID ranks are stable for a frozen extract. Reloading a different membership of works in a state can shift later ranks. They are not official MPLADS IDs.
- AP search total (3,640) is the cleaned SQLite count for `state = Andhra Pradesh`, not the earlier raw-file profile count (3,944) before duplicate handling.
- Direct URL lookup of a non-AP project (for example SQLite id `31` in Rajasthan) still works; it is outside the default search universe.
- HYBRID dates, GPS, vendor, district, expenditure, milestones, and progress are prototype enrichment only.
- Time Intelligence remains not assessable in REAL mode because verified execution dates are absent from the extract.
- Graph visualization, Plan/Claim/Evidence upload, documents, image intelligence, satellite, Jan-Sakshi, milestone UI, Need & Impact, and Copilot were not added.

Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, and Relationship Graph V1 remain frozen.
