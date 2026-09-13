# FINAL UI/UX REBUILD V2 REPORT

Date: 2026-09-11  
Slice: `final-ui-ux-rebuild-v2`  
Scope: frontend / Next.js App Router only

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph algorithms, Plan → Claim → Evidence, Document/Blueprint, Image Evidence, Image Forensics, Geospatial, Satellite, Need & Impact scoring, Milestone Advisor, Jan-Sakshi storage/privacy, Investigation Copilot retrieval/guardrails, ML Training & Inference, ML Evidence Integration, Contextual Data Enrichment, Lifecycle orchestration, database schemas, demo scenario definitions, API contracts, thresholds, and formulas.

This slice rebuilds information architecture, workflow clarity, visual hierarchy, form UX, and discoverability so existing SARVSAKSHI functionality is visible. It does not add engines, invent statistics, or change stored scores.

---

## 1. Product vision

SARVSAKSHI is presented as a **public-project intelligence, evidence, investigation, verification, and decision-support** platform for MPLADS works.

The first screen is the operational dashboard. A first-time visitor, officer, technical reviewer, SIH judge, or Jan-Sakshi citizen should be able to answer:

- What is this system?
- What can I do here?
- What projects exist?
- What has the system found?
- What evidence supports it?
- What is unknown?
- What should happen next?

The product is not a marketing landing page, CRUD admin, dark security console, or generic AI SaaS template.

Governance language remains: **AI recommends. Authorized officers decide.** Investigation Priority is a review ranking. ML anomaly score is not a fraud probability and is not Evidence Confidence.

---

## 2. New information architecture

Operational routes:

| Route | Role |
| --- | --- |
| `/` | Officer dashboard / project landscape |
| `/search` | Unified Projects & Search |
| `/projects/[id]` | Project Digital Passport |
| `/projects/[id]/investigate` | Investigation Workspace |
| `/projects/[id]/graph` | Relationship Graph |
| `/investigate` | Workspace entry (select a project) |
| `/evidence` | Evidence & Verification hub |
| `/geospatial` | Geospatial Verification hub |
| `/satellite` | Satellite hub |
| `/jan-sakshi` | Citizen field evidence |
| `/intelligence` | Intelligence Center |
| `/ml` | ML Signals |
| `/context` | Contextual Intelligence |
| `/need-impact` | Project Prioritization |
| `/milestones` | Milestone & Funding Review |
| `/copilot` | Investigation Copilot |
| `/assess-new-project` | Assess a new project wizard |
| `/demo` | Demo Center |
| `/demo/[caseId]` | Guided demo journey |

Project-specific pages keep contextual sub-navigation (Passport, Workspace, Graph, Milestones, Copilot, Geospatial, Evidence).

---

## 3. Navigation

Sidebar groups:

- **Overview** — Dashboard
- **Projects** — Projects & Search
- **Investigation** — Investigation Workspace
- **Evidence & verification** — Evidence & Verification, Geospatial Verification, Satellite, Jan-Sakshi
- **Intelligence** — Intelligence Center, Project Prioritization, ML Signals, Contextual Intelligence
- **Decisions** — Milestones & Funding Review
- **Assistance** — Investigation Copilot
- **Assessment** — Assess New Project
- **Demo** — Demo Center

Removed from the shell:

- SIH26102 from sidebar
- “AI-Assisted…” marketing line
- Global navbar search
- Visible API status button (status remains screen-reader only)

Top bar keeps product layer, Andhra Pradesh pilot, REAL / HYBRID switch, and officer login.

A global **✦ Copilot** control opens a drawer. On investigation pages Copilot is also docked in the right column.

---

## 4. Light theme / design system

Dark/near-black page, sidebar, and topbar are rejected.

Tokens in `frontend/src/app/globals.css`:

| Token | Role |
| --- | --- |
| `--bg` `#f3f1eb` | Warm light page background |
| `--shell` `#fbfaf6` | Sidebar / topbar |
| `--surface` white | Primary panels |
| `--surface-2` `#f0f4f6` | Tinted secondary surfaces |
| `--ink` / `--navy` | Charcoal / navy typography |
| `--signal` cyan | Intelligence / analytics |
| `--violet` | ML / AI |
| `--saffron` amber | Attention / HYBRID / caution |
| `--success` emerald | Consistent / verified |
| `--danger` coral | Mismatch / critical |
| `--indigo` | Geospatial / context |

Typography: Source Serif 4 for titles, IBM Plex Sans for body, IBM Plex Mono for identifiers.

Status always includes a label (and badge/icon treatment). Color is never the only cue. REAL, HYBRID, and SYNTHETIC remain distinct.

---

## 5. Dashboard

`/` is the operational dashboard.

It shows:

- SARVSAKSHI / MPLADS Intelligence & Investigation / Andhra Pradesh Pilot
- **PROJECT LANDSCAPE** from actual search totals: Total, FUTURE, ONGOING, COMPLETED, UNKNOWN
- Workflow entry points (Find, Investigate, Assess, Prioritize, Verify, Milestone, Copilot)
- **INTELLIGENCE COVERAGE** with title, one-line explanation, and Available status — no invented coverage percentages
- **SYSTEM FLOW**: DISCOVER → UNDERSTAND → VERIFY → ANALYSE → ASSESS → DECIDE
- Sample AP projects from the search API
- Honest **Unavailable** tiles for fleet-wide Investigation Priority, Evidence Confidence, review queues, and insufficient-evidence counts

No giant hero, marketing CTA, fake statistics, or fleet-wide risk index.

---

## 6. Projects & Search

`/search` is the single discovery surface.

Filters: Scheme ID, Internal Project ID, Work description / MP, State, Constituency, Category, Status.

State → Constituency cascade is preserved. Results are a data-rich table with Scheme ID, work, constituency, category, amount, lifecycle, status, data mode. Rows are clickable. Result count, pagination, clear filters, URL state, and keyboard-friendly search remain.

Search is not duplicated in the global navbar.

---

## 7. Passport

`/projects/[id]` is the project’s central page.

It answers identity, current state, known facts, evidence, signals, uncertainty, and next officer action.

Sections include:

- PROJECT IDENTITY (Scheme ID, Internal ID, MP, state, constituency, category, amount, lifecycle, status, data mode)
- PROJECT STORY from observed fields
- REVIEW SUMMARY: **Review Priority** and **Evidence Confidence** (not fraud risk)
- INTELLIGENCE signals with explanations
- Evidence timeline, Plan → Claim → Evidence, documents, images, geospatial, satellite, Jan-Sakshi, milestones, need & impact, contextual intelligence, lifecycle, comparables, data availability

Heavy modules stay behind progressive disclosure.

---

## 8. Investigation Workspace

Asymmetric console:

- **Main:** identity, lifecycle, why-flagged, evidence, signals, Plan → Claim → Evidence, documents, images, forensics, geo, satellite, citizen, graph, need, context, officer decision
- **Right:** Investigation Priority, Evidence Confidence, recommendation, docked Copilot

Visual sequence: QUESTION → EVIDENCE → SIGNALS → RELATIONSHIPS → ASSESSMENT → DECISION.

Copilot is integrated, not a hidden extra page.

---

## 9. Evidence Center

`/evidence` plus passport/workspace evidence sections.

Filters: ALL, COST, TIME, OVERLAP, COMPLIANCE, DOCUMENT, IMAGE, FORENSICS, GEO, SATELLITE, CITIZEN, ML, MILESTONE, PCE, CONTEXT.

Each item shows type, status, source, data mode, confidence, timestamp, explanation, and score when returned.

Items are labelled **OBSERVATION**, **DERIVED FINDING**, or **SCORE** so ML anomaly score is not confused with Evidence Confidence.

---

## 10. Geospatial

Title: **GEOSPATIAL VERIFICATION**  
Explanation: checks whether reported project and image locations are geographically consistent.

Shows project location, image location, distance, prototype 500 m threshold, and result.

Where coordinates exist, an SVG map visualization is shown. Where unavailable: **INCONCLUSIVE** — verified coordinates are unavailable.

The 500 m rule is labelled as a SARVSAKSHI prototype verification rule, not an official MPLADS guideline. Coordinates are not fabricated.

---

## 11. Satellite

Shows provider, availability, imagery date, result, and limitations.

When the backend returns unavailable:

**SATELLITE UNAVAILABLE**  
“Live imagery is not currently configured for this project.”

No fake imagery is displayed. HYBRID TEST mocks remain labelled not-official.

---

## 12. Images / Forensics

Workflow: UPLOAD IMAGE → image evidence (metadata, timestamp, GPS, camera) → duplicate/reuse → forensics (manipulation, AI-generation, quality).

When the AI detector is unavailable the UI stays **INCONCLUSIVE / UNAVAILABLE**. Perfect authenticity detection is not claimed.

---

## 13. Documents

Upload, document type, extracted fields, source/page, confidence, plan relationship, evidence relationship, and conflict state use existing backend behaviour. PLAN DATA CONFLICT remains visible. No invented extraction.

---

## 14. Jan-Sakshi

Citizen-facing copy: **JAN-SAKSHI** — “Help us understand what is happening on the ground.”

STEP 1 — FIND YOUR PROJECT

- Option A: I know the Scheme ID
- Option B: Find my project (constituency, project type, status)

Matching projects show Scheme ID, name, constituency, status, and amount. The citizen selects one.

STEP 2 — SUBMIT FIELD EVIDENCE

- Large **UPLOAD PROJECT PHOTO** zone (JPG / PNG / WEBP) with preview
- LOCATION — Use Current Location (not published)
- SATISFACTION stars
- Issue category dropdown
- Observation textarea
- **Submit Field Evidence**

After success: “Evidence submitted successfully.” plus selected Scheme ID.

Raw citizen GPS is not exposed publicly. The prototype 500 m rule is explained. Existing storage and privacy behaviour is unchanged.

---

## 15. Project Prioritization

`/need-impact` is displayed as **PROJECT PRIORITIZATION**.

Description: compare proposed projects and identify which works should be considered first under the available budget and evidence.

Workflow:

1. SELECT PROJECTS (multi-select plus candidate IDs for existing tests)
2. COMPARISON PREP / COMPARISON table
3. BUDGET (available budget, compared count, within-budget count)
4. PRIORITIZATION with rank, identity, region, type, budget, need, impact, urgency/priority, and why ranked

Explicit: “This is decision support, not an official sanction formula.” Values come from the ranking API. Missing scores stay INCONCLUSIVE.

---

## 16. Milestone / Funding Review

Title: **MILESTONE & FUNDING REVIEW**  
Explanation: assesses whether available evidence supports proceeding to the next project stage.

Shows current stage, evidence readiness, supporting / missing evidence, and advisor recommendation (PROCEED / HOLD / INSPECT / NEED MORE INFORMATION / INCONCLUSIVE).

**AI RECOMMENDATION** is separate from **OFFICER DECISION**.

Message: “No automatic fund release or payment is performed.” No fake payment UI and no PFMS claim.

---

## 17. Assess New Project

Flagship wizard at `/assess-new-project`.

1. PROJECT IDENTITY (supported fields only)
2. PROJECT PROPOSAL
3. CONTEXT
4. RUN ASSESSMENT

While running, the analysis flow is INPUT → COST → ML → OVERLAP → COMPLIANCE → CONTEXT → ASSESSMENT.

Results separate Cost Intelligence, ML Anomaly Signal (model, version, schema, hash, data mode, feature availability, explanation, limitations), Overlap, Compliance, Contextual Intelligence, and data availability.

Explicit: “ML anomaly score is not a fraud probability.”

A truly new project does not show historical evidence or a fake Investigation Priority when Risk Fusion V2 is unavailable.

---

## 18. ML presentation

Dedicated ML Signals hub and passport/workspace ML panel.

Visible fields when returned: score / 100, model `cost-anomaly-v1`, version, feature schema, training data hash, data mode, feature availability, explanation, limitations.

**“ML anomaly score is not a fraud probability.”**

No fake confidence percentages. ML is not fused into Investigation Priority in the UI because the backend does not fuse it.

---

## 19. Contextual Intelligence

Visual separation:

- PROJECT OBSERVATION
- EXTERNAL CONTEXT
- DERIVED COMPARISON

Copy: “Regional statistic; not a project-specific beneficiary count.”

Regional population is never presented as a project beneficiary count. Cost V1.1 / Need & Impact / Risk Fusion formulas are unchanged.

---

## 20. Copilot

Discoverable via:

- Sidebar → Investigation Copilot
- Dashboard → Ask Copilot
- Global ✦ Copilot drawer
- Docked panel on Investigation Workspace
- Suggested prompts including “Is the ML score a fraud probability?”

Responses stay grounded in the existing backend. Source evidence is shown separately from the answer. The copilot does not invent facts.

---

## 21. Demo Center

Header: **SARVSAKSHI DEMO CENTER** — explore how a project moves from discovery to investigation and officer decision.

Four case cards: GHOST, OVER-BILL, STUCK, CLEAN — each **CONTROLLED HYBRID DEMO**.

Selecting a case opens a step-by-step journey:

01 PROJECT → 02 PASSPORT → 03 LIFECYCLE → 04 INVESTIGATION → 05 EVIDENCE → 06 RISK → 07 COPILOT → 08 DECISION → 09 SUMMARY

Previous / Next and a step indicator. Each step states what it demonstrates. Outcomes are not forced. Cases are not labelled confirmed fraud or guaranteed safe. Live evidence-supported outputs and controlled-demo limitations remain visible.

---

## 22. Lifecycle UX

Lifecycle visualization uses actual states:

- FUTURE: Need & Context → Assessment → Planning
- ONGOING: Plan → Claim → Evidence → Milestone → Review
- COMPLETED: Evidence → Intelligence → Investigation → Summary

UNKNOWN remains UNKNOWN. Missing stages are not fabricated.

---

## 23. Forms / dropdowns

Forms use section titles, helper text, labels, spacious layout, and clear primary/secondary actions.

Reusable `StyledSelect`: visible background, dark readable options, hover/selected/focus, chevron, padding, and separated menu.

Native search selects keep the State → Constituency cascade and use `.svk-select` (white menu, dark option text) so options remain readable.

---

## 24. Animations

Purposeful motion only:

- section stagger
- score-bar growth
- pipeline / wizard progression
- drawer / hover transitions

`prefers-reduced-motion` disables or reduces motion. No constant motion, bounce, or particle effects.

---

## 25. Responsive behaviour

Primary target: desktop SIH presentation.

Sidebar collapses on small screens. Investigation right panel stacks below the main column. Tables wrap. Copilot drawer is full-width on small viewports. Horizontal overflow is constrained on `html`.

---

## 26. Accessibility

Semantic landmarks, skip link, headings, visible focus, labelled controls, combobox/listbox for styled selects, status labels plus badges, and reduced-motion support.

---

## 27. Performance

Heavy graph / forensics / evidence modules are not loaded on dashboard startup. Project hubs use a selector then mount the panel. Passport uses lazy disclosure. No backend polling was added.

Vitest now uses `isolate: true` so API mocks cannot leak across files.

---

## 28. Browser validation

**BROWSER SMOKE TEST = UNAVAILABLE**

Playwright is not in `frontend/package.json`. No Cursor browser automation tools were available in this session. Visual checks were performed through component tests, production route generation, and code review of theme tokens — not live screenshots.

Routes generated by `next build`: `/`, `/search`, `/projects/[id]`, `/projects/[id]/investigate`, `/projects/[id]/graph`, `/need-impact`, `/jan-sakshi`, `/assess-new-project`, `/demo`, `/demo/[caseId]`, `/evidence`, `/geospatial`, `/satellite`, `/intelligence`, `/ml`, `/context`, `/milestones`, `/copilot`, `/investigate`.

---

## 29. Frontend tests

`npm test` (Vitest):

**41 files, 115 passed.**

Coverage includes dashboard, navigation, Projects & Search, Passport, Investigation Workspace, evidence, geospatial, satellite, Jan-Sakshi, Project Prioritization, Milestone Review, Copilot, Assess New Project, Demo Center, contextual intelligence, ML presentation, data-mode badges, styled select, form flows, project finder, photo submission, unavailable/inconclusive/loading states, and governance wording.

Existing tests were updated, not deleted. Added `frontend/src/components/__tests__/uiRebuildV2.test.tsx`.

---

## 30. Backend regression

`python -m pytest` from `backend/`:

**761 passed**, 1 warning (Starlette/httpx deprecation in the test client).

No backend files were modified for this slice.

---

## 31. Build

`npm run build` in `frontend/`:

**Passed.** Next.js 15.5.25 production build compiled, type-checked, and generated the routes listed in section 28.

---

## 32. Known limitations

- Live browser screenshot pass was not possible in this session.
- Geospatial map is an SVG schematic from returned coordinates, not a tiled map provider.
- Relationship Graph remains the existing SVG ego-neighbourhood; algorithms are unchanged.
- Fleet-wide Investigation Priority / Evidence Confidence distributions are still unavailable (honest Unavailable states).
- Candidate project IDs textarea remains on Project Prioritization so existing ranking tests can submit IDs without a live search.
- Search filters still use native `<select>` for the tested State → Constituency cascade; menus are styled for contrast.
- Assess New Project cannot invent MP as a stored assessment field; the UI states that limitation.
- Satellite live imagery remains unavailable unless a provider is configured.

---

## 33. Screenshots / pages validated

Live screenshots: **not captured** (browser tooling unavailable).

Validated by tests and production build:

- `/` dashboard
- `/search` Projects & Search
- `/projects/[id]` Passport
- `/projects/[id]/investigate` Investigation Workspace
- `/projects/[id]/graph` Relationship Graph
- `/need-impact` Project Prioritization
- `/jan-sakshi`
- `/assess-new-project`
- `/demo` and `/demo/[caseId]`
- `/geospatial`, `/evidence`, `/satellite`, `/ml`, `/context`, `/milestones`, `/copilot`

---

## Visual quality gate

| Question | Result |
| --- | --- |
| 1. Homepage shows real project/system information? | Yes — landscape counts and sample works from APIs |
| 2. Interface explains what SARVSAKSHI does? | Yes — product layer + one-line feature explanations |
| 3. Theme is moderate-to-light? | Yes — warm light page, white surfaces, light shell |
| 4. Feels premium rather than generic? | Intent: original serif/navy investigation product, not a SaaS template |
| 5. Judge can understand the product quickly? | Dashboard workflows + coverage + system flow |
| 6. Citizen can submit evidence without Scheme ID? | Yes — Find my project |
| 7. Officer can find Geospatial Verification? | Sidebar + hub + passport |
| 8. Officer can find Copilot? | Sidebar, drawer, workspace dock |
| 9. Officer can find Milestone/Funding Review? | Sidebar + hub + workspace |
| 10. Project Prioritization understandable? | Multi-select comparison + budget + ranked table |
| 11. ML score understandable? | Model metadata + “not a fraud probability” |
| 12. Investigation Priority understandable? | Labelled Review Priority / review ranking |
| 13. Evidence Confidence understandable? | Separate from ML and priority |
| 14. Assess New Project is a real workflow? | Four-step wizard + analysis flow + results |
| 15. Demo Center tells a coherent story? | Nine-step guided journey |
| 16. Every major feature has a one-line explanation? | `FEATURE_EXPLANATIONS` |
| 17. Unavailable/inconclusive states clear? | PageState kinds + honest copy |
| 18. Dropdown menus readable? | StyledSelect + `.svk-select` white menus |
| 19. Forms user-friendly? | Grouped sections, helpers, large upload |
| 20. Looks like original SARVSAKSHI? | Custom tokens, serif titles, AP pilot identity |

---

## Governance audit

UI does **not** claim: Fraud detected, Fraud probability as a score, Fraud risk percentage, Corrupt project, Confirmed wrongdoing.

UI uses: Anomaly signal, Review priority, Evidence mismatch, Potential overlap, Needs review, Inconclusive, Insufficient evidence, Unavailable.

“Not a fraud probability” appears as a **denial**, not as a produced metric.

REAL / HYBRID / SYNTHETIC remain distinct. Risk Fusion V2 is displayed, not rewritten.
