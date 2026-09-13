# Relationship Graph V1 report

Date: 2026-09-10  
Engine: `relationship-graph-v1`  
HTTP: `GET /api/v1/projects/{id}/graph`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID layer: `data/synthetic/` only, labelled HYBRID/TEST

This engine builds a **project relationship graph** from observed MPLADS fields and Overlap Intelligence V1 similarity. It produces Evidence Objects with `signal_type=RELATIONSHIP_GRAPH`.

It does **not** conclude that a relationship is fraudulent. It does **not** modify Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 scoring, or Risk Fusion V1.1. Graph findings are **not** added to Investigation Priority in this slice.

---

## Dual mode

| Mode | Inputs | What is graphed |
| --- | --- | --- |
| **REAL** | MP name, work description, category, state, constituency, IDA, allocation, recommendation date | No GPS node or edge type. Chamber labels such as `Sitting Rajya Sabha` are not geographic constituency nodes. |
| **HYBRID_TEST** | Same observed fields. Synthetic GPS may support Overlap `SIMILAR_TO` scoring only | GPS is not a REAL graph field. Outputs are labelled HYBRID/TEST. |

The real extract has **no** official work ID, verified district, vendor, verified expenditure, GPS, sanction date, or completion date. Those fields are never invented.

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, and `coordinate_source` are excluded from graph inputs. Held-out labels are attached only after scoring.

---

## Graph schema

NetworkX `MultiDiGraph` of an **ego neighborhood** around one subject work. The engine does not construct a fully connected 56,138-node graph.

### Node types

| Type | Identity | Source |
| --- | --- | --- |
| `PROJECT` | `PROJECT:{project.id}` | SQLite work |
| `MP` | `MP:{normalized mp_name}` | `project.mp_name` when non-blank |
| `CONSTITUENCY` | `CONSTITUENCY:{normalized constituency}` | Geographic constituency only |
| `CATEGORY` | `CATEGORY:{normalized category}` | Observed category |
| `IDA` | `IDA:{normalized ida}` | Implementing district authority text |
| `STATE` | `STATE:{normalized state}` | Observed state/UT |

### Edge types

| Edge | Meaning | When created |
| --- | --- | --- |
| `PROJECT → RECOMMENDED_BY → MP` | Recorded MP name | `mp_name` present |
| `PROJECT → LOCATED_IN_CONSTITUENCY → CONSTITUENCY` | Geographic constituency | Constituency usable as geography |
| `PROJECT → HAS_CATEGORY → CATEGORY` | Observed category | Category present |
| `PROJECT → ASSOCIATED_WITH_IDA → IDA` | Recorded IDA | IDA present |
| `PROJECT → IN_STATE → STATE` | Observed state | State present |
| `PROJECT → SIMILAR_TO → PROJECT` | Overlap Intelligence match | Potential Overlap / Potential Duplicate |

No vendor, district, GPS, or official-work-ID edges.

### Relationship attributes on `SIMILAR_TO`

- similarity score (Overlap overall 0–100)  
- semantic similarity  
- same constituency  
- same category  
- same IDA  
- similar allocation (≥ 0.80 relative amount similarity)  
- close recommendation dates (≤ 60 days)  
- overlap outcome  
- `gps_distance_m` only in HYBRID_TEST when Overlap scored GPS  

---

## Candidate-generation strategy

Do not compare every work to every other work.

1. **Entity edges** come from the subject’s observed fields (and from neighborhood peers). Sharing a category or state is a star through an entity node, not an all-pairs project graph.  
2. **Cluster peers** (cap 40): same **geographic** constituency + same category + same IDA. If constituency is not geographic, the key is IDA + category. Same-category-only groups are not used (`Normal/Others` would explode).  
3. **`SIMILAR_TO`** reuses Overlap Intelligence V1 blocking and scoring (`OverlapIndex`, embeddings, `score_pair`). At most 50 similar edges are kept. Embeddings are not independently reimplemented.

Candidate strategy label is returned on the API.

---

## Relationship scoring

Entity edges have strength `1.0` (observed binary link).

`SIMILAR_TO` strength = Overlap overlap score / 100.

A separate **graph score** (0–100, optional) summarises pattern strength for the Evidence Object. It is **not** Investigation Priority.

Evidence Confidence is separate (REAL cap 64, HYBRID cap 70). Isolated or missing-field cases score lower.

---

## Meaningful vs normal connectivity

A large number of connections is **not** automatically a pattern of interest. IDA volume (an implementing authority associated with many works) is reported as context only.

| Finding | Meaning |
| --- | --- |
| **NORMAL CONNECTIVITY** | Expected entity links (MP, constituency, category, IDA, state). Similar works absent, or present below the pattern threshold. |
| **HIGH CONNECTIVITY** | Many similar works (≥ 5) or a large constituency/category/IDA cluster with at least one similar work. Volume for review, not a legal finding. |
| **POTENTIAL PATTERN OF INTEREST** | Multiple independent signals: similar works in the same constituency, sharing IDA, and close recommendation dates — or the documented example shape (6+ similar, 5+ same constituency, 4+ same IDA). |
| **INSUFFICIENT EVIDENCE** | No usable entity fields and no similar works. |

Independent relationship signals counted among similar peers:

- semantic similarity  
- same constituency  
- same category  
- same IDA  
- similar allocation  
- close recommendation dates  

Example finding text:

> Project has 6 highly similar works in the same constituency, with 5 sharing the same IDA and 4 recommended within 60 days.

That is **Potential Pattern of Interest**, not a legal conclusion.

---

## Architecture

The engine lives under `backend/app/engines/graph/` and is independent of Cost, Time, Overlap scoring internals (it **calls** Overlap functions), Compliance, and Risk Fusion.

Flow:

1. Load observed `GraphRecord` rows (no GPS, no scenario labels).  
2. Build entity nodes/edges from observed fields.  
3. Generate cluster peers by constituency + category + IDA.  
4. Reuse Overlap blocking + scoring for `SIMILAR_TO`.  
5. Assemble a NetworkX ego graph.  
6. Classify finding. Persist Evidence Object + `graph_edge` (`SIMILAR_TO` only).  

HTTP: `GET /api/v1/projects/{id}/graph` (`mode=real` or `hybrid-test`).

Response includes: project node, connected nodes, relationships, relationship strengths, graph findings, graph evidence. No frontend visualization in this slice.

---

## Tests

**360** backend tests passed (0 failed), including frozen Cost/Time/Overlap/Compliance/Evidence/Fusion suites plus Relationship Graph V1:

1. basic project-node creation  
2. MP relationships  
3. constituency relationships  
4. category relationships  
5. IDA relationships  
6. state relationships  
7. project-to-project similarity relationships  
8. graph determinism  
9. no fabricated fields  
10. no invalid geography relationships  
11. missing-field handling  
12. isolated project  
13. highly connected project  
14. multiple independent relationship signals  
15. false-positive connectivity  
16. synthetic label leakage  
17. evidence-object generation  
18. REAL vs HYBRID separation  

```powershell
cd backend
python -m pytest
python -m app.engines.graph.evaluate_run
```

---

## 10 real-project examples

GPS is absent on every real row. 846 is `Sitting Rajya Sabha` (not geographic), so same-constituency count is 0.

| Project | Case | Connected | Same const. | Same cat. | Same IDA | Similar | Strongest relationship | Finding | Conf. | Mode |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| 846 | water tankers | 35 | 0 | 35 | 7 | 50 | SIMILAR_TO 855 (DUPLICATE, 0.75) | HIGH_CONNECTIVITY | 64 | REAL |
| 232 | Hindupur roads | 45 | 45 | 45 | 45 | 29 | SIMILAR_TO 3703 (DUPLICATE, 0.88) | PATTERN OF INTEREST | 64 | REAL |
| 217 | Hindupur crematorium | 40 | 40 | 40 | 40 | 3 | SIMILAR_TO 8552 (DUPLICATE, 0.81) | PATTERN OF INTEREST | 64 | REAL |
| 3348 | Srikakulam halls | 36 | 36 | 1 | 36 | 35 | SIMILAR_TO 8129 (DUPLICATE, 0.78) | PATTERN OF INTEREST | 64 | REAL |
| 3715 | Kurnool school rooms | 40 | 40 | 40 | 40 | 0 | ASSOCIATED_WITH_IDA Kurnool | NORMAL_CONNECTIVITY | 36 | REAL |
| 21769 | Eluru water tanks | 2 | 2 | 2 | 2 | 1 | SIMILAR_TO 22458 (DUPLICATE, 0.81) | NORMAL_CONNECTIVITY | 64 | REAL |
| 5263 | Ongole roads | 75 | 75 | 75 | 75 | 50 | SIMILAR_TO 5267 (DUPLICATE, 1.00) | PATTERN OF INTEREST | 64 | REAL |
| 21192 | Araku sanitation | 60 | 60 | 60 | 60 | 20 | SIMILAR_TO 21189 (DUPLICATE, 0.97) | PATTERN OF INTEREST | 64 | REAL |
| 233 | Anakapalle borewells | 40 | 40 | 40 | 40 | 5 | SIMILAR_TO 3169 (DUPLICATE, 0.79) | PATTERN OF INTEREST | 64 | REAL |
| 234 | Anakapalle multi-gym | 40 | 40 | 40 | 40 | 0 | ASSOCIATED_WITH_IDA Anakapalli | NORMAL_CONNECTIVITY | 36 | REAL |

846 explanation: chamber constituency is excluded from geography. Many similar tanker titles still produce High Connectivity. That is **not** a legal finding.

3715 / 234 explanation (why not flagged): Overlap V1 did not keep a Potential Overlap/Duplicate match. Sharing Kurnool or Anakapalle IDA/constituency is Normal Connectivity.

232 explanation: 29 similar Hindupur roads, all same IDA and within 60 days → Potential Pattern of Interest for review. Generic repeated titles are a source-text limitation.

---

## 10 HYBRID evaluation examples

HYBRID `scenario_type` / `demo_case_id` were attached **after** scoring. Coordinates are SYNTHETIC and are not graph node types.

| Project | Case | Connected | Same const. | Same cat. | Same IDA | Similar | Strongest relationship | Finding | Conf. | Mode |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| 23028 | overlap group A | 72 | 72 | 72 | 46 | 50 | SIMILAR_TO 23081 (0.91) | PATTERN OF INTEREST | 70 | HYBRID |
| 9982 | overlap group B | 75 | 75 | 75 | 75 | 50 | SIMILAR_TO 9979 (0.92) | PATTERN OF INTEREST | 70 | HYBRID |
| 26946 | DEMO_CLEAN | 42 | 42 | 42 | 42 | 2 | SIMILAR_TO 47354 (0.80) | HIGH_CONNECTIVITY | 70 | HYBRID |
| 22177 | DEMO_OVERBILL | 0 | 0 | 0 | 0 | 0 | ASSOCIATED_WITH_IDA Eluru | NORMAL_CONNECTIVITY | 36 | HYBRID |
| 52862 | DEMO_STUCK | 48 | 48 | 48 | 48 | 8 | SIMILAR_TO 31694 (0.73) | PATTERN OF INTEREST | 70 | HYBRID |
| 53637 | DEMO_GHOST | 40 | 40 | 40 | 40 | 0 | ASSOCIATED_WITH_IDA Vizianagaram | NORMAL_CONNECTIVITY | 36 | HYBRID |
| 46124 | NORMAL | 75 | 75 | 75 | 75 | 39 | SIMILAR_TO 46126 (1.00) | PATTERN OF INTEREST | 70 | HYBRID |
| 15149 | overlap GPS 119 m | 48 | 48 | 48 | 48 | 22 | SIMILAR_TO 15133 (0.91) | PATTERN OF INTEREST | 70 | HYBRID |
| 16180 | MIXED overlap+cost | 74 | 74 | 74 | 45 | 50 | SIMILAR_TO 16181 (0.93) | PATTERN OF INTEREST | 70 | HYBRID |
| 25533 | COST_ANOMALY | 68 | 68 | 68 | 68 | 28 | SIMILAR_TO 25598 (0.93) | PATTERN OF INTEREST | 70 | HYBRID |

22177 explanation: Repair and Renovation in Eluru has no blocked similar peers and a cluster size of 1. Isolated neighborhood. Held-out OVERBILL was not a graph input.

26946 explanation: CLEAN has only 2 similar works but a large constituency/category/IDA cluster (110), so High Connectivity. Held-out CLEAN is not a model input.

53637 explanation: DEMO_GHOST has no Overlap SIMILAR_TO matches. Sharing Vizianagaram IDA with many works is Normal Connectivity. Offshore GPS is not a graph node.

---

## Limitations

- Generic repeated titles (`NA - Construction of roads…`) produce many `SIMILAR_TO` edges via Overlap V1. That is a **source-text limitation**, not proof of duplicated government works.  
- High IDA degree is expected for district collectors and is not a pattern of interest by itself.  
- The example-shape pattern (6+ similar, same constituency, shared IDA) can fire when dates are **not** concentrated (see DEMO_STUCK: 8 similar / 1 within 60 days). Officers should read the close-date count.  
- REAL has no GPS; HYBRID GPS is SYNTHETIC and only affects Overlap `SIMILAR_TO`.  
- Chamber constituencies are excluded from geography.  
- Ego neighborhood cluster peers are capped at 40; IDA/cluster **counts** still use the full corpus.  
- This slice does not fuse graph weight into Investigation Priority. Risk Fusion V1.1 reserved 5% for relationship graph remains unused.  
- No frontend graph visualization.

STOP. Digital Passport, Plan/Claim/Evidence UI, documents, vision, geospatial UI, Jan-Sakshi, Milestone, Copilot, and frontend graph visualization were not built in this slice.
