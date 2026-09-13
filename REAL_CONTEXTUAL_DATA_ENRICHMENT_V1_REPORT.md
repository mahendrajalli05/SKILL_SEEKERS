# Real Contextual Data Enrichment V1 report

Date: 2026-09-11  
Engine: `contextual-data-enrichment-v1`  
HTTP:

- `GET  /api/v2/projects/{id}/context`
- `POST /api/v2/projects/{id}/context/refresh`
- `GET  /api/v2/context/sources`
- `POST /api/v2/projects/assess` includes `contextual_v1` labelled `NEW_PROJECT_ASSESSMENT` (not persisted)

Frozen and unchanged: Cost Intelligence V1.1, Need & Impact V1 formula, Risk Fusion V1.1, Risk Fusion V2, Investigation Priority, original MPLADS `project` rows, `data/raw/`.

This module adds a **separate, provenance-first external contextual data layer**.

```
REAL MPLADS project data
        +
VERIFIED EXTERNAL PUBLIC DATA
        ↓
contextual evidence (supporting context only)
```

It does **not** overwrite MPLADS records, fabricate missing values, create another synthetic dataset, change Cost V1.1 scoring, change Need & Impact weights, change Risk Fusion weights, or produce a supervised fraud model.

---

## Inspection (before implementation)

Inspected Need & Impact V1 (constituency-first; REAL population/infrastructure/beneficiary components unavailable → INCONCLUSIVE, not zero), Evidence Object V1, `project` schema (no district/expenditure), sidecar provenance, and existing external adapters.

No verified public reference-data adapters existed. Time Intelligence has a delay-context hook for recorded codes only. Need & Impact HYBRID enrichment is labelled TEST/SYNTHETIC and is not a public dataset.

Files added (conceptual):

- `data/external/sources/registry.json` — source registry
- `data/external/snapshots/` — verified public extract (MoHFW Table-21)
- `data/external/fixtures/` — small labelled HYBRID/TEST rates only
- `backend/app/engines/context/` — registry, adapters, geography, time match, quality, cache
- `backend/app/models/context.py` — `external_source`, `external_context_snapshot`, `external_context_observation`
- `backend/app/evidence/adapters/context.py` — Evidence Object V1
- `backend/app/api/routes/context.py`
- Passport / Investigation Workspace / new-project assessment UI section
- Copilot `EXTERNAL_CONTEXT` retrieval

`data/raw/` and original project rows were not modified.

---

## 1. Sources integrated

| source_id | Mode | Status |
| --- | --- | --- |
| `mohfw_ncp_population_projections_2011_2036` | REAL | **Integrated** as a transcribed public table snapshot |
| `hybrid_reference_cost_test` | HYBRID / SYNTHETIC only | Small labelled test fixture (not official SoR) |
| `cpwd_delhi_schedule_of_rates` | — | Documented **UNAVAILABLE** |
| `ap_pwd_schedule_of_rates` | — | Documented **UNAVAILABLE** |
| `data_gov_in_ckan_api` | — | **SOURCE_UNAVAILABLE_REQUIRES_CONFIGURATION** (no API key) |
| `nfhs5_state_household_amenities` | — | Documented **UNAVAILABLE** (PDF factsheets; no verified structured extract) |
| `census_2011_pca_district` | — | Documented **UNSUPPORTED_GEOGRAPHY** (no reliable district on MPLADS extract) |

---

## 2. Why each source was selected

**MoHFW / National Commission on Population, Population Projections 2011–2036 (July 2020), TABLE-21.**  
Official Government of India statistical publication. State-level projected population as on 1 March. Public PDF. Machine-usable after an explicit, documented unit conversion (published thousands → persons). Matches the only reliable geographic identifier on the cleaned MPLADS extract (`state`).

**HYBRID reference-cost fixture.**  
Not a government source. Used only so HYBRID tests can exercise unit-rate handling without inventing an official Schedule of Rates. REAL mode must not consume it.

**CPWD Delhi SoR / AP PWD SoR.**  
Authoritative class of material/reference cost. Selected as the correct *class*, then recorded as unavailable because no verified public machine-readable bulk extract was obtained.

**data.gov.in CKAN API.**  
Legitimate government open-data gateway. Requires a registered API key. No key is stored in source code.

**NFHS-5 state fact sheets.**  
Official household amenity indicators (electricity, water, sanitation). Selected as the correct *class* for infrastructure context. Not transcribed from PDFs without a verified structured extract.

**Census 2011 PCA (district).**  
Official district population. Not used: the cleaned MPLADS extract has no verified district field, and district is not fabricated from IDA or constituency text.

---

## 3. Source provenance

Every registry record stores: `source_id`, `source_name`, `publisher`, `source_type`, URL/identifier, `retrieval_date` (2026-09-11), `dataset_version` where known, geographic level, unit, update frequency, license/usage note, transformation notes, limitations, active/inactive.

Application code loads metadata from `data/external/sources/registry.json`. Publisher URLs are not hard-coded in adapters.

MoHFW snapshot additional provenance:

- Report title: *Population Projections for India and States, 2011-2036*
- Table: TABLE-21 Projected Total Population As on 1st March
- Publication: July 2020
- URL: `https://main.mohfw.gov.in/sites/default/files/Population%20Projection%20Report%202011-2036%20-%20upload_compressed_0.pdf`
- Alternate: NHM copy of the same report

---

## 4. Geographic coverage

| Level | Support |
| --- | --- |
| STATE | Matched when `project.state` is present. MoHFW snapshot is STATE only. |
| DISTRICT | Never assumed equal to constituency or IDA. Returns INCONCLUSIVE / UNSUPPORTED_GEOGRAPHY. |
| CONSTITUENCY | Identifier may exist on the project; no verified external constituency indicator is bundled. |
| BLOCK / LOCALITY | City / village / ward / block are not promoted to another level. |

Missing state → population **UNAVAILABLE** (value remains null, not zero).  
Rajya Sabha / nominated constituency tokens are not treated as a place.

---

## 5. Time coverage

MoHFW series years: 2011, 2016, 2021, 2026, 2031, 2036 (as on 1 March).

Documented nearest-year rule: if the project recommendation year is within **2 years** of a published projection year, that year may be used with an explicit note that it is **not exact contemporaneous equivalence**. Larger gaps are INCONCLUSIVE for time matching. Absence of a recommendation date is not treated as a 2026 (or any) contemporaneous match.

Example: a 2023 recommendation uses 2021 with `nearest_published_year` and reduced confidence.

---

## 6. Units

| Indicator | Unit |
| --- | --- |
| State population | `persons` (from published thousands × 1000) |
| MPLADS allocation | `unspecified_allocation_amount` (extract does not give a unit) |
| MPLADS expenditure | `project_expenditure` — UNAVAILABLE in the extract |
| HYBRID test rate | `INR_per_sqm` (labelled fixture) |

Incompatible units are not mixed. Total allocation vs unit rate → **INCONCLUSIVE** (`INCOMPATIBLE_UNIT`).

---

## 7. Transformations

1. Population: `persons = persons_thousands × 1000`. This is a published-table unit conversion, not a modelled estimate.
2. Andhra Pradesh and Telangana 2011 values are reconstituted successor-state populations as published after bifurcation, not undivided Census 2011 Andhra Pradesh.
3. Table-21 “Uttaranchal” is stored as Uttarakhand with an alias in the matcher.
4. National (INDIA) totals are omitted; project matching is not performed at NATIONAL level.
5. No unofficial SoR scraping or PDF-to-rate invention.

---

## 8. Material / reference cost context

Distinguishes:

- **MPLADS allocation** — PROJECT-SPECIFIC FACT when present
- **MPLADS expenditure** — UNAVAILABLE (not treated as zero; not replaced by a reference rate)
- **External reference cost** — official CPWD / AP PWD **UNAVAILABLE**; HYBRID fixture only in HYBRID/SYNTHETIC
- **Derived comparison** — INCONCLUSIVE when units/geography/quantity are incompatible

Cost Intelligence V1.1 remains the authoritative peer-based allocation anomaly. External reference context does not modify `cost_anomaly_score`.

---

## 9. Development-need context

Need & Impact V1 formula is **frozen**. REAL mode still does not invent:

- project beneficiaries from state population
- constituency deprivation from a state total
- zero for a missing need component

When state is present, **OBSERVED EXTERNAL INDICATOR** `state_population` is attached as supporting context. It is not written into Need Score components. Missing Need & Impact inputs remain INCONCLUSIVE rather than zero.

---

## 10. Infrastructure context

Household electricity, improved drinking water, improved sanitation, and generic infrastructure availability are **UNAVAILABLE**. Census district population is **UNSUPPORTED_GEOGRAPHY**. Values were not invented.

---

## 11. Data modes

| Mode | Behaviour |
| --- | --- |
| REAL | MoHFW snapshot only for population. HYBRID fixture blocked. Synthetic labels never promoted to REAL. |
| HYBRID | Real project record + labelled test enrichment (reference-cost fixture). |
| SYNTHETIC | Test project; `data_mode=SYNTHETIC` even if the caller sends REAL. External figures remain cited as external. |

`SYNTHETIC → REAL` and `HYBRID → REAL` conversions are forbidden. Every observation exposes `data_mode`.

---

## 12. Evidence Object integration

Existing Evidence Object V1 schema. Neutral signal types added because no compatible existing signal described external context:

- `REFERENCE_COST_CONTEXT`
- `DEVELOPMENT_NEED_CONTEXT`
- `INFRASTRUCTURE_CONTEXT`
- `CONTEXT_UNAVAILABLE`
- `CONTEXT_INCONCLUSIVE`

`engine=context`, `source_type=external_public_dataset` (or `mplads_project_record` / `hybrid_enrichment` / `synthetic_test_record` as appropriate). Findings use observation vs derived vs project-fact language. No fraud / corruption / guilt wording. Not mapped into Risk Fusion V2 `SIGNAL_TYPE_TO_GROUP`.

---

## 13. APIs

`GET /api/v2/projects/{id}/context` and `POST .../context/refresh` return available indicators, source, publisher, retrieval date, geographic level, reference period, unit, values, derived comparison when valid, `data_mode`, confidence/quality, limitations, and unavailable indicators.

`GET /api/v2/context/sources` lists registry metadata without filesystem paths.

New-project `POST /api/v2/projects/assess` computes only indicators derivable from the supplied payload, labelled `NEW_PROJECT_ASSESSMENT`. It does not persist historical Evidence Objects, execution evidence, citizen evidence, expenditure, or beneficiaries.

---

## 14. Caching / snapshot method

Default path reads the local snapshot file. SQLite `external_context_snapshot` stores retrieval timestamp, source version, SHA-256, payload, and processing version. Live HTTP fetch is **off** (`SARVSAKSHI_CONTEXT_LIVE_FETCH=false`) so ordinary project page loads do not hit the network. If live fetch is enabled and times out, the status is **TIMEOUT** with a null value.

---

## 15. Failure handling

Explicit statuses: `AVAILABLE`, `UNAVAILABLE`, `INCONCLUSIVE`.

Codes include: `SOURCE_UNAVAILABLE`, `TIMEOUT`, `MALFORMED_SOURCE`, `UNSUPPORTED_GEOGRAPHY`, `MISSING_GEOGRAPHY`, `MISSING_VALUE`, `INCOMPATIBLE_UNIT`, `STALE_DATASET`, `AMBIGUOUS_SOURCE_VERSION`, `INVALID_TRANSFORMATION`, `UNAVAILABLE_INDICATOR`, `SOURCE_UNAVAILABLE_REQUIRES_CONFIGURATION`.

Absence is never converted to zero. No silent substitute.

---

## 16. Tests

Backend: registry metadata; REAL Andhra Pradesh population 52,787,000 (2021) as OBSERVED EXTERNAL INDICATOR not beneficiaries; missing state; district request; reference cost vs expenditure; HYBRID fixture isolation; data.gov.in configuration; malformed snapshot; timeout; stale quality control; year-gap INCONCLUSIVE; NEW_PROJECT_ASSESSMENT not persisted; Evidence Object provenance; Copilot EXTERNAL_CONTEXT; Cost V1.1 / Need & Impact / Risk Fusion V1.1 and V2 unchanged.

Frontend: Contextual Intelligence panel distinguishes PROJECT OBSERVATION vs EXTERNAL CONTEXT.

No 10,000-row synthetic dataset was added. The only extra rows are the small HYBRID rate fixture.

---

## 17. Limitations

- State population is not a beneficiary count and is not a constituency/locality statistic.
- Official unit rates were not integrated.
- NFHS-5 / Census district amenities were not integrated.
- data.gov.in was not queried without a configured key.
- Contextual evidence is not fused into Investigation Priority.
- Live remote refresh is disabled by default.

---

## 18. Sources that could NOT be integrated, and why

| Candidate | Why not integrated |
| --- | --- |
| CPWD Delhi Schedule of Rates | Official PDFs; no verified public machine-readable bulk extract was obtained. Rates were not transcribed or scraped. |
| AP PWD Schedule of Rates | Same: no legally attributable structured snapshot was bundled. |
| data.gov.in CKAN | Requires `SARVSAKSHI_DATA_GOV_IN_API_KEY`. None is configured. Reported as `SOURCE_UNAVAILABLE_REQUIRES_CONFIGURATION`. |
| NFHS-5 fact sheets | Official PDFs; percentages were not silently typed in from screenshots. |
| Census 2011 district PCA | Authoritative, but MPLADS extract has no verified district identifier. Constituency ≠ district. IDA text is not a district code. |
| Live SoR / market price APIs | Would require credentials or unofficial scraping. Not used. |

Truthfulness and provenance were preferred over maximizing displayed indicators.

---

## Governance

External context is supporting context only. AI recommends. Authorized officers decide. Investigation Priority and Evidence Confidence are unchanged by this module. No legal fraud finding is produced.
