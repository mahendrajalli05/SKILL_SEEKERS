# Relationship Graph Visualization V1 report

Date: 2026-09-10  
Slice: officer Relationship Graph visualization  
HTTP consumed: `GET /api/v1/projects/{id}/graph`  
Route: `/projects/{id}/graph`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Relationship Graph V1 engine, Search / AP pilot / Scheme ID, Plan → Claim → Evidence, Document / Blueprint, Image Evidence, Image Forensics, Geospatial Consistency, Satellite / Remote-Sensing, Need & Impact, Milestone Advisor, Jan-Sakshi, Investigation Copilot.

This slice adds an **officer-facing visualization** of the stored Relationship Graph V1 ego-neighborhood. It does **not** recalculate nodes, edges, strengths, or findings in the browser. It does **not** modify Investigation Priority. It does **not** conclude that a project is fraudulent.

---

## What was built

### 1. Data source

The UI calls the existing graph API only:

`GET /api/v1/projects/{id}/graph` with `mode=real` or `mode=hybrid-test`.

Node types, edge types, relationship attributes, graph findings, and graph evidence are rendered from that response. No frontend graph intelligence was added.

### 2. Visualization

A deterministic SVG neighborhood (no new graph library) around the selected work:

| Ring | Content |
| --- | --- |
| Center | Subject `PROJECT` |
| Inner | API entity nodes: `MP`, `CONSTITUENCY`, `CATEGORY`, `IDA`, `STATE` |
| Outer | `SIMILAR_TO` projects, ranked by API strength |
| Optional | Cluster-peer `PROJECT` nodes, collapsed until expanded |

Officer interactions:

- click node → node / relationship details
- click or hover a relationship → edge type, strength, supporting attributes
- zoom (scroll)
- pan (drag)
- Reset
- Show more / fewer similar projects
- Expand / collapse cluster peers

Avoided force-directed animation and avoided rendering the 56,138-work graph.

Visible similar projects default to **12** (page size 12, hard cap 36). Cluster peers default to **0** visible (page size 8, hard cap 16). The API neighborhood is already an ego-graph (`MAX_DISPLAY_NODES` / `MAX_DISPLAY_RELATIONSHIPS` on the engine). The UI further limits what is drawn.

### 3. Relationship details

Selected `SIMILAR_TO` edges show API attributes, for example:

- edge type `SIMILAR_TO`
- related project/node
- relationship strength
- Similarity
- Same constituency: YES / NO
- Same category: YES / NO
- Same IDA: YES / NO
- Recommendation gap: N days
- overlap outcome
- `gps_distance_m` only when the API returned it (HYBRID)

Entity edges show type, related node, and strength `1.00`. Relationships that are not in the API are not invented.

### 4. Graph findings

Findings are displayed exactly as returned:

- `NORMAL_CONNECTIVITY`
- `HIGH_CONNECTIVITY`
- `POTENTIAL_PATTERN_OF_INTEREST`
- `INSUFFICIENT_EVIDENCE`

They are not remapped into a legal conclusion. Isolated neighborhoods (no connected nodes) and `INSUFFICIENT_EVIDENCE` are explicit empty states.

### 5. Evidence

The panel shows:

- `graph_evidence` / `graph_findings` from the graph API (summary, details, provenance notes)
- stored Graph Evidence Objects (`engine_name=graph` / `signal_type=relationship_graph`) with source and provenance

Example text is passed through from the engine, such as highly similar works in the same constituency sharing IDA and close recommendation dates.

### 6. Investigation Workspace

`RELATIONSHIP GRAPH` is a section on the existing Investigation Workspace. It shows the visualization, finding, related projects, relationship details, and evidence. Risk Fusion V1.1 remains the only Investigation Priority source. The graph panel states that it does not modify Investigation Priority.

### 7. Project Digital Passport

The passport relationship summary is compact:

- Connected nodes
- Similar projects
- Graph finding
- **Open Relationship Graph** → `/projects/{id}/graph`

### 8. Dedicated page layout

`/projects/{id}/graph`:

- Top: Project / Scheme ID
- Middle: interactive neighborhood
- Side: relationship details
- Graph finding
- Evidence
- Actions: Open related project, Open Evidence, Return to Investigation Workspace

The rest of the site chrome is unchanged. Current application scope remains Andhra Pradesh (existing search/pilot filters were not modified). Non-AP records were not deleted.

### 9. REAL / HYBRID / SYNTHETIC

`graph_mode` / `dataset_type` (and synthetic project rows) are labelled:

- **REAL** — observed MPLADS fields and Overlap `SIMILAR_TO` only
- **HYBRID** / **SYNTHETIC** — prototype evaluation output, **not official MPLADS findings**

HYBRID GPS, when `gps_used` is true, is described as Overlap scoring only, not a REAL graph node type.

---

## Files

Created:

- `frontend/src/lib/graphView.ts`
- `frontend/src/components/RelationshipGraphView.tsx`
- `frontend/src/components/RelationshipGraphPanel.tsx`
- `frontend/src/app/projects/[id]/graph/page.tsx`
- `frontend/src/test/graphFixtures.ts`
- `frontend/src/lib/__tests__/graphView.test.ts`
- `frontend/src/components/__tests__/RelationshipGraphPanel.test.tsx`
- `frontend/src/components/__tests__/RelationshipSummary.test.tsx`
- `frontend/src/app/projects/[id]/graph/__tests__/page.test.tsx`

Changed:

- `frontend/src/lib/types.ts` — graph API types for nodes, relationships, findings, evidence
- `frontend/src/components/RelationshipSummary.tsx` — compact counts + Open Relationship Graph
- `frontend/src/app/projects/[id]/page.tsx` — passport link to the visualization
- `frontend/src/app/projects/[id]/investigate/page.tsx` — RELATIONSHIP GRAPH section
- `ROADMAP.md` — Graph Visualization V1 only

Backend graph engine, fusion, evidence validation, and other intelligence engines were not modified.

---

## Tests and verification

Frontend: **72** Vitest tests passed, including graph visualization coverage:

- graph loads; central `PROJECT` appears
- node types and edge types from the API
- relationship details (`SIMILAR_TO`, strength, same constituency/category, recommendation gap)
- related-project navigation
- graph finding display
- REAL / HYBRID distinction and non-official HYBRID notice
- empty / isolated graph
- `INSUFFICIENT_EVIDENCE`
- graph API failure
- loading state
- large neighborhood limiting and expansion
- no-fraud wording
- Investigation Priority unchanged notice
- Passport compact summary + Open Relationship Graph
- Investigation Workspace panel and dedicated `/projects/{id}/graph` page

Backend: **616** tests passed (0 failed). Frozen Cost / Time / Overlap / Compliance / Evidence / Fusion / Graph engine suites were not edited.

```powershell
cd frontend
npm test
npm run build

cd ..\backend
python -m pytest
```

`next build` succeeded. Registered route: `ƒ /projects/[id]/graph`.

Interactive click-through in a live browser was not available in this environment. Component tests exercise load, click-to-details, related-project links, expand, REAL/HYBRID, empty/error/loading, and workspace/passport copy. Live API checks against a running officer session were not performed here.

---

## Limitations

- The drawing is an ego-neighborhood, not a statewide graph.
- Similar and cluster-peer nodes are capped in the browser on top of the engine display caps.
- Generic repeated work titles can still produce many `SIMILAR_TO` edges via Overlap V1; the UI shows that engine output and does not relabel it as duplicated government works.
- Graph findings remain investigation aids. They are not fused into Investigation Priority in this slice.
- No new graph intelligence, synthetic dataset, PFMS, or Risk Fusion V2.

STOP. Relationship Graph V1 calculations, Risk Fusion V1.1, and the other frozen modules were not changed.
