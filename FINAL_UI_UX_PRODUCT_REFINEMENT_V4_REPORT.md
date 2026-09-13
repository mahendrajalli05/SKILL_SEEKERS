# FINAL UI/UX PRODUCT REFINEMENT V4 REPORT

Date: 2026-09-11  
Slice: `final-ui-ux-product-refinement-v4`  
Scope: frontend / Next.js App Router only

Frozen and unchanged: backend, database schema, real project data, synthetic datasets, API contracts, Cost V1.1, Time V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2, Relationship Graph algorithms, Plan → Claim → Evidence, Documents/Blueprint, Image Evidence, Image Forensics, Geospatial logic, Satellite logic, Need & Impact scoring, Milestone Advisor, Jan-Sakshi backend, Investigation Copilot backend, ML Training & Inference, ML Evidence Integration, Contextual Data Enrichment, Lifecycle orchestration, demo logic, scoring formulas, thresholds, and governance rules.

This slice is the final major frontend product refinement. It fixes information architecture so major capabilities are no longer grouped under one Intelligence section, and it makes existing engineering visible as a light, premium, investigation-focused product.

---

## 1. Information architecture

The product is organized around **user tasks**, not a single Intelligence dump.

| Primary section | User task | Routes |
| --- | --- | --- |
| OVERVIEW | See the operational picture | `/` |
| PROJECTS | Search, browse, and open works | `/search`, `/projects/[id]` |
| INVESTIGATION | Investigate a selected work | `/investigate`, `/projects/[id]/investigate` |
| EVIDENCE | Review stored evidence | `/evidence`, `/evidence/documents`, `/evidence/images` |
| VERIFICATION | Check field and location evidence | `/verification`, `/geospatial`, `/satellite`, `/jan-sakshi` |
| ANALYTICS | Read cost/time/overlap/compliance | `/analytics`, `/analytics/cost`, `/analytics/time`, `/analytics/overlap`, `/analytics/compliance` |
| PLANNING | Compare and prioritize proposals | `/planning`, `/need-impact`, `/planning/need-impact` |
| LIFECYCLE | Stage and funding review | `/lifecycle`, `/milestones` |
| AI & MODELS | ML signals and Copilot | `/ml`, `/copilot` |
| CONTEXT | External public indicators | `/context` |
| ASSESSMENT | Assess a proposed work | `/assess-new-project` |
| DEMO | Guided SIH cases | `/demo`, `/demo/[caseId]` |

`/intelligence` redirects to `/analytics`. It is not a navigation destination.

Search is not a second navigation concept. `/search` is the Projects page.

---

## 2. Navigation changes

The sidebar is a light, collapsible accordion.

- Each primary section has an icon and a section label.
- Children appear only when that section is expanded.
- The section matching the current route opens automatically.
- Duplicate labels are not repeated across sections.
- Copilot lives under **AI & MODELS**, not as a second top-level copy of the same idea.
- Evidence is not mixed with Geospatial / Satellite / Jan-Sakshi.
- Analytics is not mixed with ML, Context, or Prioritization.

Top bar is minimal:

- SARVSAKSHI (sidebar; compact on small screens)
- Current Pilot
- REAL / HYBRID indicator
- Officer login

Removed from the top bar: marketing layer line, repeated global search, visible API status.

Global **✦ COPILOT** remains as a floating control.

---

## 3. Dashboard

`/` remains the operational homepage.

Header: **SARVSAKSHI** / MPLADS Intelligence & Investigation / Andhra Pradesh Pilot.

Then:

1. **PROJECT LANDSCAPE** — Total, Future, Ongoing, Completed, Unknown from actual search totals, plus a lifecycle distribution chart. Unavailable remains Unavailable.
2. **KEY WORKFLOWS** — Find a Project, Investigate a Project, Assess a New Project, Prioritize Projects, Verify Field Evidence, Review Project Stage, Ask Copilot. Each has icon, one-line explanation, and CTA.
3. **INTELLIGENCE SYSTEM** — visual grid of Cost, Time, Overlap, Compliance, ML, Context, Evidence, Geospatial, Satellite, Citizen, Milestone. Each tile has icon, Available status, one-line explanation, and a link to the **correct** section. No invented coverage percentages.
4. **SYSTEM FLOW** — DISCOVER → UNDERSTAND → VERIFY → ANALYSE → ASSESS → DECIDE.
5. **DISCOVERABLE PROJECTS** — sample AP works from the search API.

Honest Unavailable tiles remain for fleet-wide Investigation Priority, Evidence Confidence, review queues, and insufficient-evidence counts.

---

## 4. Projects

`/search` is titled **PROJECTS**.

Subtitle: “Search, explore, and investigate MPLADS works in the current pilot.”

One search/filter area: Scheme ID, Internal Project ID, Work description / MP, State, Constituency, Category, Status. State → Constituency cascade is preserved.

Results heading: **RESULTS — N PROJECTS**.

Columns: Scheme ID, Project, Constituency, Category, Amount, Lifecycle, Status, Signals, Action.

Rows remain clickable. Actions: **View Passport** and **Investigate**.

There is no separate Search navigation item.

---

## 5. Investigation

`/projects/[id]/investigate` remains the flagship console.

- **Left:** project identity plus investigation navigation (Why reviewed, Evidence, Signals, Relationships, Plan → Claim → Evidence, Copilot).
- **Center:** why this project is being reviewed, what we know / don’t know, evidence, signals, relationships, Plan → Claim → Evidence, officer decision.
- **Right:** Review Priority, Evidence Confidence, recommendation, docked Copilot.

Visual flow: QUESTION → EVIDENCE → SIGNALS → RELATIONSHIPS → ASSESSMENT → DECISION.

Investigation Priority remains a review ranking. The UI does not call a project fraud.

---

## 6. Evidence

`/evidence` is **EVIDENCE CENTER**, a first-class section.

Subpages:

- Documents & Blueprint — `/evidence/documents`
- Images & Forensics — `/evidence/images`

Filters remain: All, Cost, Time, Overlap, Compliance, Document, Image, Forensics, Geo, Satellite, Citizen, ML, Milestone, PCE, Context.

Cards show type, status, source, data mode, confidence, timestamp, and explanation.

An evidence timeline is shown on the hub. Geospatial / Satellite / Citizen are no longer evidence-hub tiles; they belong to Verification.

---

## 7. Verification

`/verification` is **VERIFICATION CENTER**.

Subsections:

- Geospatial Verification
- Satellite Verification
- Jan-Sakshi

Each card states its purpose. Sidebar children go directly to those pages.

---

## 8. Analytics

`/analytics` is **ANALYTICS CENTER**.

Pages:

- Cost Intelligence
- Time Intelligence
- Overlap Detection
- Compliance

Each page: purpose, project selection, visual result from existing APIs, explanation, limitations. Cost/time/overlap/compliance are no longer hidden inside Intelligence.

---

## 9. Planning

`/planning` is **PLANNING CENTER**.

- **Project Prioritization** (`/need-impact`) — Find → Compare → Budget → Prioritize. Candidate-ID textarea remains only under Advanced ID entry.
- **Need & Impact** (`/planning/need-impact`) — separate Need, Impact, Urgency, and Priority displays for a selected project.

Ranking comparison no longer treats priority class as urgency. Ranking payload has no urgency score, so the Urgency column shows **UNAVAILABLE**.

Copy: “Decision support, not an official sanction formula.”

---

## 10. Lifecycle

`/lifecycle` is **PROJECT LIFECYCLE**.

Visual track: FUTURE → PLANNING → ONGOING → MILESTONES → COMPLETED → FINAL REVIEW.

Stored states remain FUTURE, ONGOING, COMPLETED, or UNKNOWN. UNKNOWN remains UNKNOWN. Planning / milestones / final review are workflow labels, not invented stored states.

---

## 11. AI & Models

Separate primary section.

- ML Signals — `/ml`
- Investigation Copilot — `/copilot`

These are not analytics pages and are not buried under Intelligence.

---

## 12. Context

`/context` is **CONTEXTUAL INTELLIGENCE**.

Kicker is Context, not Intelligence. Existing PROJECT OBSERVATION / EXTERNAL CONTEXT / DERIVED COMPARISON presentation is preserved, including: “Regional statistic; not a project-specific beneficiary count.”

---

## 13. Assess New Project

Four steps: PROJECT → PROPOSAL → CONTEXT → ASSESS.

During assessment the pipeline still shows INPUT → COST → ML → OVERLAP → COMPLIANCE → CONTEXT → ASSESSMENT.

Result order: project header, Cost, ML, Overlap, Compliance, Context, Need & Impact (UNAVAILABLE when the assess API does not return it), Data availability, then **ASSESSMENT SUMMARY** at the bottom.

NEW PROJECT ASSESSMENT is explicit. No historical evidence exists yet. No fake Investigation Priority is invented; Risk Fusion V2 unavailability is shown as returned.

---

## 14. Jan-Sakshi

Citizen-focused service.

Title: **JAN-SAKSHI**  
Subtitle: “Help us understand what is happening on the ground.”

Workflow: 01 FIND PROJECT → 02 SUBMIT EVIDENCE → 03 VERIFY LOCATION → 04 SUBMIT.

Find by Scheme ID or constituency / type / status using styled dropdowns. Selected project shows Scheme ID, work, constituency, status, amount.

Upload PROJECT PHOTO, Use Current Location, 1–5 stars, issue category dropdown, observation.

Success: Evidence submitted successfully. Recorded against Scheme ID.

---

## 15. Geospatial

Title: **GEOSPATIAL VERIFICATION**

One-line: checks whether reported project and image locations are geographically consistent.

Shows project location, reported image location, distance, 500 m prototype threshold, and result. SVG map when coordinates exist. Otherwise: **INCONCLUSIVE** — “Verified coordinates are unavailable.”

The 500 m rule remains labelled as a SARVSAKSHI prototype verification rule, not an official MPLADS guideline.

---

## 16. Satellite

Title: **SATELLITE VERIFICATION**

Shows Provider, Availability, Imagery date, Result, Limitations.

Unavailable state: **SATELLITE UNAVAILABLE** — “Live imagery is not currently configured for this project.”

No fake imagery. HYBRID TEST provider controls are behind **Advanced TEST controls**, so they are not part of the primary citizen/officer path.

---

## 17. Milestone / Funding Review

`/milestones` is **MILESTONE & FUNDING REVIEW** under Lifecycle.

Shows Current Stage, Evidence Readiness, supporting / missing evidence.

AI Recommendation (PROCEED / HOLD / INSPECT / NEED MORE INFORMATION / INCONCLUSIVE) is visually separate from Officer Decision (PROCEED / HOLD / INSPECT / NEED MORE INFORMATION).

Copy: “No automatic fund release or payment is performed.”

---

## 18. Copilot

Investigation Copilot is a distinct AI & Models feature.

Global floating control: **✦ COPILOT**.

Drawer copy: evidence-grounded assistance for project investigation.

Suggested questions include: What evidence exists?, Why is this being reviewed?, What is the main anomaly?, Which model generated the ML score?, What evidence is missing?, What external context is available?, Is the ML score a fraud probability?

AI answers and **Source evidence** are visually distinct. The backend is unchanged. The UI does not invent facts.

---

## 19. Demo Center

Title: **SARVSAKSHI DEMO CENTER**

“Follow a project from discovery to investigation and officer decision.”

Four case cards: GHOST, OVER-BILL, STUCK, CLEAN. Each labelled CONTROLLED HYBRID DEMO. Button: START INVESTIGATION →.

Journey 01 PROJECT … 09 SUMMARY is unchanged. Outcomes are not forced.

---

## 20. Visual system

Light theme retained.

| Token | Role |
| --- | --- |
| Warm ivory canvas | Page |
| White surfaces | Panels |
| Navy typography | Titles / body |
| Cyan | Analytics / data |
| Violet | ML / AI |
| Amber | Attention / review |
| Emerald | Verified / consistent |
| Coral | Mismatch / critical |
| Indigo | Context / geospatial |

No dark theme. Color is never the only status cue.

Data mode remains compact chips:

- REAL DATA · Andhra Pradesh Pilot
- HYBRID DEMO · Controlled prototype
- SYNTHETIC · Test only

Expandable “About this data” / environment details remain.

---

## 21. Data visualization

Used where values actually exist:

- Lifecycle distribution on the dashboard
- Score bars and anomaly scales
- Peer allocation range from returned cost comparables (not an invented percentile)
- Overlap comparison cards with similarity bars
- Compliance rule cards grouped TRIGGERED / NOT_TRIGGERED / NOT_ASSESSABLE
- Need / Impact / Urgency / Priority meters
- Evidence timeline
- Geospatial SVG map
- Assessment analysis pipeline
- System flow arrows

Percentile is shown as UNAVAILABLE when the Cost V1.1 payload does not return it. Duration/progress is UNAVAILABLE unless the time API returns it.

---

## 22. Forms

Search, Jan-Sakshi, Assess, and Prioritization use section headers, helper text, grouping, and clear actions. Inputs remain spacious. Wizard steps remain for Assess, Jan-Sakshi, and Prioritization.

---

## 23. Dropdowns

Search filters, Jan-Sakshi find-project filters, and issue category use `StyledSelect`:

- Visible menu
- High-contrast white options
- Hover, selected, and focus states
- Chevron
- Accessible combobox/listbox roles

Browser-default unreadable menus are not used on those primary filters.

---

## 24. Animations

Existing premium motion is retained: section reveal, score-bar growth, pipeline pulse, Copilot message in, drawer/sidebar transform.

`prefers-reduced-motion` still disables animation and transition.

No bouncing, particle overload, or slow loops were added.

---

## 25. Responsive

Desktop/laptop remains primary. Sidebar slides on small screens. Investigation columns stack. Tables keep the stack pattern. Copilot drawer remains full-width on small viewports. Styled select menus remain in-flow and readable.

---

## 26. Accessibility

Skip link, landmarks, headings, labelled controls, combobox/listbox selects, keyboard-openable sidebar sections, status labels plus badges, star rating radiogroup, reduced-motion support.

---

## 27. Performance

Dashboard still loads search totals and a small sample, not every heavy visualization.

Evidence documents/images, analytics engines, geospatial, satellite, graph, and Copilot remain on their own routes or behind workspace tabs / lazy disclosure.

---

## 28. Browser validation

**Live Chrome screenshot pass: not captured.**

No Cursor browser automation / screenshot tools were available in this session.

Validation used:

- Source review of the actually rendered App Router pages and shell
- Vitest coverage of navigation, hubs, dashboard, Projects filters, Passport, Investigation, Jan-Sakshi, Copilot, styled dropdowns, and unavailable/inconclusive states
- Next.js production build of the operational routes

The developer should still inspect in Chrome:

`/`, `/search`, `/projects/[real-id]`, `/projects/[real-id]/investigate`, `/evidence`, `/geospatial`, `/jan-sakshi`, `/analytics`, `/need-impact`, `/milestones`, `/ml`, `/context`, `/copilot`, `/assess-new-project`, `/demo`, `/demo/[caseId]`.

---

## 29. Tests

`npm test` (Vitest): **43 files, 124 passed.**

Existing tests were updated, not deleted. Added `frontend/src/components/__tests__/uiProductRefinementV4.test.tsx`.

Coverage updates include:

- New navigation structure and section expansion
- Dashboard KEY WORKFLOWS
- Projects styled dropdowns
- Passport ANALYTICS / SIGNAL MATRIX
- Need & Impact separate visual scores
- Styled selects (search, Jan-Sakshi, issue category)
- Lifecycle UNKNOWN state
- Analytics hub tiles

---

## 30. Build

`npm run build` in `frontend/`: **Passed.** Next.js 15.5.25 production build compiled, type-checked, and generated the operational routes including `/analytics/*`, `/verification`, `/planning`, `/lifecycle`, `/evidence/documents`, and `/evidence/images`.

`python -m pytest` from `backend/`: **761 passed**, 1 warning (Starlette/httpx deprecation in the test client).

No backend files were modified.

---

## 31. Known limitations

- Live Chrome click-through still needs the developer.
- Geospatial map remains an SVG schematic from returned coordinates.
- Cost percentile is UNAVAILABLE because Cost V1.1 does not return a percentile field.
- Time duration/progress is UNAVAILABLE on REAL records without execution dates.
- Ranking Urgency is UNAVAILABLE because the rank API does not return `urgency_score`.
- New-project assessment does not return Need & Impact; that card is UNAVAILABLE.
- Satellite live imagery remains unavailable unless a provider is configured.
- Fleet-wide Investigation Priority / Evidence Confidence distributions remain unavailable.
- Candidate IDs remain behind Advanced ID entry so ranking tests still work.
- Relationship Graph algorithms and all scoring formulas are unchanged.

---

## Visual acceptance gate

| Check | Result |
| --- | --- |
| 1. No dark dominant background | Yes |
| 2. Sidebar is light and clean | Yes |
| 3. Major features are not buried under one Intelligence section | Yes |
| 4. Dashboard shows actual project information | Yes — search totals and sample rows |
| 5. Projects is the unified discovery experience | Yes — `/search` |
| 6. Investigation is separate from browsing | Yes |
| 7. Evidence is first-class | Yes |
| 8. Verification is first-class | Yes |
| 9. Analytics is separate from Evidence/Verification | Yes |
| 10. Planning is clearly separate | Yes |
| 11. Lifecycle is clearly separate | Yes |
| 12. AI & Models is clearly separate | Yes |
| 13. Context is clearly separate | Yes |
| 14. Assess New Project is prominent | Yes — Assessment section + dashboard CTA |
| 15. Demo Center is easy to understand | Yes |
| 16. Jan-Sakshi is citizen-friendly | Yes |
| 17. Geospatial is discoverable | Yes — Verification |
| 18. Copilot is discoverable | Yes — AI & Models + floating control |
| 19. Milestone/Funding Review is discoverable | Yes — Lifecycle |
| 20. Need & Impact clearly compares Need/Impact/Urgency/Priority | Yes — separate meters; ranking urgency unavailable when not returned |
| 21. One-line explanations | Yes |
| 22. Forms are not cramped | Yes |
| 23. Dropdowns are readable | Yes — StyledSelect |
| 24. Data presented visually where useful | Yes |
| 25. No fake data | Yes |
| 26. No fraud claims | Yes |
| 27–30. Original, premium, light, investigation-focused | Frontend IA now matches those product goals; live Chrome confirmation remains with the developer |

---

## Governance audit

UI does **not** display: Fraud detected, Fraud probability, Fraud risk percentage, Corrupt project, Confirmed wrongdoing.

UI uses: Anomaly signal, Review priority, Evidence mismatch, Potential overlap, Needs review, Inconclusive, Insufficient evidence, Unavailable.

ML anomaly score is not a fraud probability. Investigation Priority is a review ranking. Evidence Confidence is separate.

REAL = observed/verified data. HYBRID = real base plus labelled synthetic enrichment. SYNTHETIC = test only.

No automatic fund release or payment is performed. No deployment was started.
