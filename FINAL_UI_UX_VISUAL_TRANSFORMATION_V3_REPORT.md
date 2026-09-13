# FINAL UI/UX VISUAL TRANSFORMATION V3 REPORT

Date: 2026-09-11  
Slice: `final-ui-ux-visual-transformation-v3`  
Scope: frontend / Next.js App Router only

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph algorithms, Plan → Claim → Evidence, Document/Blueprint, Image Evidence, Image Forensics, Geospatial, Satellite, Need & Impact scoring, Milestone Advisor, Jan-Sakshi storage/privacy, Investigation Copilot retrieval/guardrails, ML Training & Inference, ML Evidence Integration, Contextual Data Enrichment, Lifecycle orchestration, database schemas, demo scenario definitions, API contracts, thresholds, and formulas.

This slice transforms the existing V2 interface into a data-rich public-project intelligence console. It does not add engines, invent statistics, or change stored scores.

---

## 1. Information architecture

Primary sidebar hubs (only):

| Hub | Route |
| --- | --- |
| Dashboard | `/` |
| Projects | `/search` |
| Investigation | `/investigate` |
| Evidence & Verification | `/evidence` |
| Intelligence | `/intelligence` |
| Decisions | `/milestones` |
| Copilot | `/copilot` |
| Assess New Project | `/assess-new-project` |
| Demo Center | `/demo` |

Low-level capabilities are shown inside hubs, not as top-level items:

- Evidence hub: GEO, SATELLITE, CITIZEN, ML, documents, images, forensics, PCE
- Intelligence hub: COST, TIME, OVERLAP, COMPLIANCE, ML, CONTEXT, GEO, SATELLITE, EVIDENCE, CITIZEN, MILESTONE, plus Prioritization / ML Signals / Context links
- Project pages keep Passport, Workspace, Graph, Milestones, Copilot, Geospatial, Evidence sub-navigation

---

## 2. Visual design

Light premium identity on a warm ivory canvas with a faint evidence-lattice grid.

| Token | Role |
| --- | --- |
| `--bg` `#f4f0e6` | Warm light page |
| `--shell` `#fbf8f1` | Sidebar / topbar |
| `--surface` white | Panels |
| `--ink` / `--navy` | Charcoal / navy type |
| `--signal` cyan | Intelligence / data |
| `--violet` | ML / AI |
| `--saffron` amber | Attention / review |
| `--success` emerald | Verified / consistent |
| `--danger` coral | Mismatch / critical |
| `--indigo` | Geo / context |

Typography: Source Serif 4 for titles, IBM Plex Sans for body, IBM Plex Mono for identifiers.

Cards use a left-edge semantic accent, not rainbow fills. Color is never the only status cue.

Data environment is a compact expandable chip:

- REAL DATA · Andhra Pradesh Pilot
- HYBRID DEMO · Controlled prototype

Expanding reveals full provenance. Provenance is not removed.

---

## 3. Dashboard

`/` is the operational command center.

Header: SARVSAKSHI / MPLADS Intelligence & Investigation / Andhra Pradesh Pilot, then the compact environment chip.

PROJECT LANDSCAPE uses large metric blocks from search totals: TOTAL PROJECTS, FUTURE, ONGOING, COMPLETED, UNKNOWN, plus a lifecycle distribution bar. Values come from the existing search APIs. Unavailable remains Unavailable.

OPERATIONAL OVERVIEW cards: FIND PROJECT, INVESTIGATE, ASSESS NEW PROJECT, PRIORITIZE PROJECTS, VERIFY FIELD EVIDENCE, REVIEW MILESTONE, ASK COPILOT.

INTELLIGENCE SYSTEM is a semantic tile grid with Available status only — no invented coverage percentages.

SYSTEM FLOW: DISCOVER → UNDERSTAND → VERIFY → ANALYSE → ASSESS → DECIDE, each with icon and one-line description.

DISCOVERABLE PROJECTS is a compact table of sample AP works. Click opens Passport.

Honest Unavailable tiles remain for fleet-wide Investigation Priority, Evidence Confidence, review queues, and insufficient-evidence counts.

---

## 4. Projects

`/search` is project discovery.

Compact header plus SEARCH COMMAND. Results heading: RESULTS — N PROJECTS.

Table columns: Scheme ID, Project, Constituency, Category, Amount, Lifecycle, Status, Signals.

Status uses badges. Rows remain clickable. URL state, pagination, State → Constituency cascade, and empty states are unchanged.

---

## 5. Passport

`/projects/[id]` opens as PROJECT OVERVIEW.

Top strip: Scheme ID, title, constituency, category, amount, lifecycle, status.

Side-by-side Review Priority and Evidence Confidence.

SIGNAL OVERVIEW: Cost, Time, Overlap, Compliance, ML, Context, Geo, Satellite, Citizen.

Then Evidence Timeline, PLAN → CLAIM → EVIDENCE → RESULT, Related Projects, then detailed identity / finance / intelligence / evidence / documents / images / geo / satellite / milestones / citizen / graph / need / context / lifecycle / data availability.

---

## 6. Investigation

Flagship three-column console:

- Left: project identity
- Center: why this project is being reviewed, evidence story, WHAT WE KNOW / WHAT WE DON'T KNOW / WHAT NEEDS VERIFICATION, recommended next step, then existing workspace tabs
- Right sticky: Review Priority, Evidence Confidence, recommendation, docked Copilot

Language remains review ranking. The UI does not call a project fraud.

---

## 7. Evidence

Evidence Center filters remain: ALL, COST, TIME, OVERLAP, COMPLIANCE, DOCUMENT, IMAGE, FORENSICS, GEO, SATELLITE, CITIZEN, ML, MILESTONE, PCE, CONTEXT.

Passport/workspace use a timeline plus typed cards. Hub page adds GEO / SATELLITE / CITIZEN / ML tiles.

---

## 8. ML

ML ANOMALY SIGNAL shows a large score, model, version, feature schema, training hash, data mode, Typical ←→ Unusual scale, and feature contribution bars when the API returns contributions.

Copy: “ML anomaly score is not a fraud probability.”

---

## 9. Geospatial

PROJECT LOCATION / IMAGE LOCATION / distance / 500 m threshold / CONSISTENT or MISMATCH, plus SVG map when coordinates exist.

Unavailable state: INCONCLUSIVE — verified coordinates are unavailable. The 500 m rule remains labelled as a prototype.

---

## 10. Satellite

Image-analysis style panel: Provider, Imagery status, Date, Result.

SATELLITE UNAVAILABLE is a designed empty state: “Live imagery is not currently configured for this project.” No fake imagery.

---

## 11. Jan-Sakshi

Citizen 4-step process:

01 FIND PROJECT  
02 SUBMIT EVIDENCE  
03 VERIFY LOCATION  
04 SUBMIT

Find by Scheme ID or constituency / type / status. Selected project shows Scheme ID, name, constituency, status, amount.

Upload zone remains UPLOAD PROJECT PHOTO. Success shows a checkmark and “Recorded against: Scheme ID”.

---

## 12. Prioritization

`/need-impact` is PROJECT PRIORITIZATION.

Candidate project IDs textarea is removed from the primary experience and placed under Advanced ID entry so existing ranking tests can still submit IDs.

Workflow: FIND PROJECTS → COMPARE table → BUDGET meters → ranked cards with WHY THIS RANK.

Disclaimer: Decision support, not an official sanction formula.

---

## 13. Milestone Review

CURRENT STAGE, Evidence Readiness, and AI RECOMMENDATION are separate from OFFICER DECISION.

Copy: “No automatic fund release or payment is performed.”

---

## 14. Assess New Project

4-stage stepper: PROJECT / PROPOSAL / CONTEXT / ASSESS.

RUN ASSESSMENT shows INPUT → COST → ML → OVERLAP → COMPLIANCE → CONTEXT → ASSESSMENT.

Result screen: project summary, Cost Intelligence, ML Anomaly Signal, Overlap, Compliance, Context, data availability, Assessment Summary.

NEW PROJECT ASSESSMENT is explicit. No fake Investigation Priority is shown when Risk Fusion V2 is unavailable.

---

## 15. Copilot

Global floating control: ✦ COPILOT.

Investigation page keeps the docked right-side assistant.

Suggested questions include: What evidence exists?, Why is this being reviewed?, What is the main anomaly?, Which model generated the ML score?, What evidence is missing?, What external context is available?, Is the ML score a fraud probability?

Answers remain backend-grounded.

---

## 16. Demo

SARVSAKSHI DEMO CENTER — follow a project from discovery to investigation and officer decision.

Four case cards: GHOST, OVER-BILL, STUCK, CLEAN. Each shows scenario, lifecycle, primary concern, and that evidence is recorded on the journey (no invented evidence count). CONTROLLED HYBRID DEMO. Button: START INVESTIGATION →.

Journey progress: 01 PROJECT … 09 SUMMARY. Current step dominates. Each screen states WHAT THIS STEP DEMONSTRATES.

---

## 17. Animation

Purposeful motion: section reveal, score-bar growth, pipeline pulse, analysis stage, hover lift.

`prefers-reduced-motion` disables animation and transition.

---

## 18. Responsive

Desktop SIH presentation remains primary. Sidebar collapses on small screens. Investigation columns stack. Tables use the existing stack pattern. Copilot drawer remains full-width on small viewports.

---

## 19. Accessibility

Skip link, landmarks, headings, labelled controls, combobox/listbox for styled selects, status labels plus badges, expandable environment details, reduced-motion support.

---

## 20. Browser validation

**Live Chrome screenshot pass: not captured.**

No Cursor browser automation / screenshot tools were available in this session.

A live Next.js server on `http://127.0.0.1:3000` was fetched. HTML confirmed:

- Hub sidebar (Dashboard, Projects, Investigation, Evidence & Verification, Intelligence, Decisions, Copilot, Assess New Project, Demo Center)
- Compact HYBRID DEMO environment chip
- Dashboard landscape, operational cards, intelligence tiles, system flow
- Projects & Search command area
- ✦ COPILOT control

SSR snapshots showed landscape counts as Unavailable until client fetch completes. That is honest API-dependent rendering, not invented zeros.

**Please inspect these pages in Chrome and send screenshots before treating visual acceptance as final:**

`/`, `/search`, a Passport, an Investigation Workspace, `/evidence`, `/ml`, `/geospatial`, `/satellite`, `/jan-sakshi`, `/need-impact`, `/milestones`, `/assess-new-project`, `/copilot`, `/demo`

---

## 21. Screenshots reviewed

Live screenshots: **not captured**.

HTML/source review of the running site plus component tests and production build were used instead.

---

## 22. Tests

`npm test` (Vitest): **42 files, 118 passed.**

Existing tests were updated, not deleted. Added `frontend/src/components/__tests__/uiVisualV3.test.tsx`.

---

## 23. Build

`npm run build` in `frontend/`: **Passed.** Next.js 15.5.25 production build compiled, type-checked, and generated the operational routes.

---

## 24. Backend regression

`python -m pytest` from `backend/`: **761 passed**, 1 warning (Starlette/httpx deprecation in the test client).

No backend files were modified.

---

## 25. Known limitations

- Live screenshot / click-through Chrome review still needs the developer.
- Geospatial map remains an SVG schematic from returned coordinates.
- Relationship Graph algorithms are unchanged.
- Fleet-wide Investigation Priority / Evidence Confidence distributions remain unavailable.
- Candidate IDs remain behind Advanced ID entry for ranking tests.
- Assess New Project still cannot invent MP as a stored assessment field.
- Satellite live imagery remains unavailable unless a provider is configured.
- Dashboard sample projects depend on the search API being reachable in the browser session.

---

## Visual quality gate

| Check | Result |
| --- | --- |
| 1. Dashboard as intelligence command center | Yes — landscape, workflows, tiles, flow |
| 2. Projects exposes discovery | Yes — search command + results table |
| 3. Passport tells the project story | Yes — overview, scores, signals, timeline, PCE |
| 4. Investigation feels like a console | Yes — three-column workspace |
| 5. Evidence visually central | Timeline + typed cards + hub tiles |
| 6. ML clearly visible | Score, scale, metadata, not-fraud copy |
| 7. Geospatial clearly visible | Location comparison + map/unavailable |
| 8. Copilot clearly visible | Floating ✦ COPILOT + docked panel |
| 9. Milestone review clearly visible | Stage / readiness / AI vs officer |
| 10. Prioritization is a multi-project workflow | Find / compare / budget / rank |
| 11. Jan-Sakshi citizen-friendly | 4-step + selected project + success |
| 12. Assess looks like an AI product | Stepper + pipeline + result panels |
| 13. Demo tells a coherent story | Four cases + 9-step journey |
| 14. Dropdowns professional | StyledSelect + `.svk-select` |
| 15. Forms spacious | Grouped fields, large upload |
| 16. Page hierarchy obvious | Compact headers, section grouping |
| 17. Heading/body/metadata distinct | Serif / sans / mono |
| 18. Color semantics consistent | Signal / violet / amber / emerald / coral / indigo |
| 19. Original SARVSAKSHI identity | Lattice canvas, navy serif, hub mark |
| 20. Not a generic dashboard | Investigation/evidence vocabulary, not KPI wallpaper |

---

## Governance audit

UI does **not** claim: Fraud detected, Fraud probability as a score, Fraud risk percentage, Corrupt project, Confirmed wrongdoing.

UI uses: Anomaly signal, Review priority, Evidence mismatch, Potential overlap, Needs review, Inconclusive, Insufficient evidence, Unavailable.

“Not a fraud probability” appears as a denial, not as a produced metric.

REAL / HYBRID / SYNTHETIC remain distinct. Risk Fusion V2 is displayed, not rewritten.
