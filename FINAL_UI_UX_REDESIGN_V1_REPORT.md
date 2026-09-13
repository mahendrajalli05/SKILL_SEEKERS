# FINAL UI/UX REDESIGN V1 REPORT

Date: 2026-09-11  
Slice: `final-ui-ux-redesign-v1`  
Scope: frontend / Next.js App Router only

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph logic, Plan → Claim → Evidence, Document/Blueprint, Image Evidence, Image Forensics, Geospatial, Satellite, Need & Impact, Milestone Advisor, Jan-Sakshi, Investigation Copilot retrieval/guardrails, ML Training & Inference, ML Evidence Integration, Contextual Data Enrichment, Lifecycle orchestration, database schemas, demo scenario definitions, API response semantics, thresholds, and formulas.

This slice redesigns the officer-facing product so it reads as an investigation and intelligence console. It does not add engines, invent statistics, or change stored scores.

---

## 1. Design direction

SARVSAKSHI is presented as an **AI-assisted public-project intelligence, evidence, investigation, monitoring, and decision-support platform**.

Visual intent:

- professional government-tech console
- dense but readable
- high-contrast dark surfaces
- restrained gold/signal accents
- no generic SaaS dashboard look
- no cartoon colour, no glassmorphism, no oversized risk meters

Product line used in the shell:

**AI-Assisted MPLADS Intelligence & Investigation Platform**

The officer path is:

DISCOVER → UNDERSTAND → INVESTIGATE → VERIFY → ASSESS → DECIDE

---

## 2. Visual system

New tokens live in `frontend/src/app/globals.css`.

| Token | Role |
| --- | --- |
| `--bg` / `--shell` | Deep console background |
| `--surface` / `--surface-2` | Elevated panels |
| `--navy` | Primary text / headings |
| `--navy-fill` | Selected navigation and filled controls |
| `--signal` | Intelligence accent |
| `--accent` / `--saffron` | HYBRID / caution |
| `--danger` | SYNTHETIC distinction |
| `--success` | CONSISTENT / PROCEED |

Typography: IBM Plex Sans + IBM Plex Mono via `next/font`.

Existing `bg-white` card classes are remapped to `--surface` through an exact class selector so `bg-white/10` overlays remain usable.

REAL, HYBRID, and SYNTHETIC badges use different tones. SYNTHETIC is not styled like REAL.

---

## 3. Navigation changes

The global header is now a persistent sidebar + top bar.

Grouped navigation:

| Group | Routes |
| --- | --- |
| Overview | Dashboard `/`, Search `/search` |
| Project intelligence | Projects / Investigation → `/search` (project pages remain ID-scoped) |
| Evidence & verification | Jan-Sakshi `/jan-sakshi` |
| Intelligence | Need & Impact `/need-impact` |
| Assessment | Assess New Project `/assess-new-project` |
| Demo | Demo Center `/demo` |

Project-scoped sub-nav is unchanged in meaning:

- Digital Passport
- Investigation Workspace
- Relationship Graph
- Milestones
- Copilot

Reviews remains a shell page and is not in primary nav.

The top bar includes:

- SARVSAKSHI identity
- SIH26102
- command search
- AP pilot label
- REAL DATA / HYBRID DEMO switch
- API status
- Officer login

---

## 4. Shared components

Added under `frontend/src/components/system/`:

- `PageHeader`
- `SectionHeader`
- `FeatureExplanation`
- `ScoreDisplay` / `ConfidenceDisplay` / `ScoreBar`
- `MetricCard`
- `LoadingSkeleton`
- `SystemPipeline` / `PceChain` / `InvestigationFlow`
- `GovernanceStrip`
- `SourceBadge`
- `EvidenceTimeline`

Existing primitives were restyled, not replaced:

- `StatusBadge`
- `PageState`
- `SectionCard`
- `LazyDisclosure`
- `WorkspaceTabs`
- `EvidenceCard`
- `SignalCard`
- `RiskScoreCard`
- `RiskFusionV2Panel`

---

## 5. Dashboard redesign

`OfficerDashboard` is now an intelligence command center.

It shows, from existing APIs only:

- AP pilot search totals (same `page_size=1` count queries as before)
- FUTURE / ONGOING / COMPLETED / UNKNOWN shares derived from those totals
- Unavailable fleet-wide Investigation Priority, Evidence Confidence, review queue, and insufficient-evidence index
- a sample of search rows (`page_size=8`) labelled as a sample, not a high-priority index
- project-level intelligence coverage, not invented coverage percentages
- the PROJECT → INTELLIGENCE → EVIDENCE → RISK → INVESTIGATION → OFFICER DECISION pipeline

The dashboard still does not load the 56,138-row extract and does not invent risk distributions.

---

## 6. Passport redesign

`/projects/[id]` remains the Digital Passport.

Added without removing required sections:

- PROJECT STORY assembled from observed fields
- one-line explanations for intelligence layers
- evidence timeline
- NEXT ACTION from stored Risk Fusion only

Required headings remain: PROJECT IDENTITY, FINANCE / RECOMMENDATION, INTELLIGENCE, EVIDENCE, PLAN / CLAIM / EVIDENCE, DOCUMENTS, IMAGES, GEOSPATIAL, SATELLITE, MILESTONES, JAN-SAKSHI, NEED & IMPACT, LIFECYCLE.

Heavy modules still load through `LazyDisclosure`.

---

## 7. Investigation Workspace redesign

`/projects/[id]/investigate` uses an asymmetric layout:

- centre: identity, lifecycle, lazy workspace tabs
- right: Investigation Priority, Evidence Confidence, recommendation, docked Copilot

Plan → Claim → Evidence shows a PLAN → CLAIM → EVIDENCE → RESULT chain.

The investigation flow is:

QUESTION → EVIDENCE → SIGNALS → RELATIONSHIPS → ASSESSMENT → DECISION

Officer decisions still write `officer_decision` only. Scores are unchanged.

---

## 8. Search redesign

`/search` keeps:

- State → Constituency cascade
- Enter / Search commit
- URL state
- Scheme ID / internal ID / work / MP search
- result count and pagination

Results remain a professional table with data-mode badges, status badges, and stacked layout on small screens. No backend search contract changed.

---

## 9. Evidence UX

Evidence cards now show type, status, source, data mode, confidence, timestamp where present, and expandable score bars.

ML evidence uses a distinct signal treatment and still states:

> ml_anomaly_score is not a fraud probability and is not Evidence Confidence.

Disposition grouping (WHY FLAGGED / WHY NOT FLAGGED / INCONCLUSIVE / INSUFFICIENT EVIDENCE) is unchanged.

---

## 10. Risk UX

Risk Fusion V1.1 and V2 still display:

- Investigation Priority 0–100
- Evidence Confidence 0–100
- contributing / independent / correlated / conflicting / unavailable groups

Added weighted bars from existing `effective_contribution` values. Unavailable groups are not shown as zero. Copy uses **Review priority**, not fraud risk.

---

## 11. ML UX

ML presentation still includes model, version, feature schema, training hash, data mode, anomaly score, feature availability, explanation, and limitations.

Suggested Copilot questions now include:

- Which model generated the ML signal?
- Is the ML score a fraud probability?

No fake confidence percentages were added.

---

## 12. Context UX

Contextual Intelligence still separates:

- PROJECT OBSERVATION
- EXTERNAL CONTEXT
- DERIVED COMPARISON

Missing indicators remain UNAVAILABLE / INCONCLUSIVE. They are not rendered as zeros.

---

## 13. Lifecycle UX

Lifecycle still uses FUTURE / ONGOING / COMPLETED / UNKNOWN from the existing API.

Current-state highlighting uses `--navy-fill`. Unavailable stages remain labelled unavailable. The panel still states that workflow actions are not sanctions or payments.

---

## 14. Jan-Sakshi UX

`/jan-sakshi` now explains:

- citizen observations are supporting evidence, not automatic truth
- the 500 m check is a prototype verification rule, not an official MPLADS guideline

Privacy behaviour is unchanged: captured GPS is used for verification and is not published as a public field.

---

## 15. Copilot UX

Investigation Copilot is docked on the Investigation Workspace.

Header copy:

**INVESTIGATION COPILOT**  
Evidence-grounded assistance for project investigation.

Answers still come from `POST /api/v1/projects/{id}/copilot/chat`. Source evidence is labelled separately from the Copilot response.

---

## 16. Demo Center UX

`/demo` is labelled a controlled hybrid demo launcher.

Each case still uses the existing catalog: GHOST, OVER-BILL, STUCK, CLEAN.

The journey nav now states:

PROJECT → PASSPORT → LIFECYCLE → INVESTIGATION → EVIDENCE → RISK → COPILOT → DECISION → SUMMARY

Outcomes are not forced. Demo notices remain.

---

## 17. New Project Assessment UX

`/assess-new-project` is framed as a pre-lifecycle assessment workspace.

After submit it still shows Cost V1.1, ML, overlap, compliance, contextual intelligence when returned, and the existing “no historical evidence to fuse” reason. No fake Investigation Priority is shown when unavailable.

---

## 18. Animations

Subtle CSS animations:

- page/section reveal
- score-bar grow
- pipeline pulse
- Copilot message reveal
- hover elevation on search rows

`prefers-reduced-motion` disables animation and transitions.

---

## 19. Responsive behaviour

- sidebar collapses behind a Menu button below `lg`
- investigation workspace stacks the Copilot/priority column below the main column
- search tables still stack on small screens
- project sub-nav remains horizontally scrollable

Primary target remains desktop/laptop SIH demonstration.

---

## 20. Accessibility

- skip link and `main` landmark retained
- semantic headings on major pages
- visible `:focus-visible` rings
- labelled search/filter controls
- tablist keyboard behaviour unchanged
- reduced-motion support
- REAL / HYBRID / SYNTHETIC remain text badges, not colour-only

---

## 21. Performance

- dashboard still uses `page_size=1` for totals
- recent-project sample is `page_size=8`
- Passport lazy-disclosures still avoid mounting unused heavy modules
- Workspace tabs still mount only the active tab panel
- graph/chart logic is unchanged and not loaded on the dashboard
- no new backend polling

---

## 22. Tests

Frontend: `npm test` — **40 files, 111 tests passed**.

Backend: `python -m pytest` from `backend/` — **761 passed**.

No backend files were modified.

Updated/added coverage:

- grouped navigation / Demo Center
- dashboard counts, unavailable fleet stats, `page_size=1` totals plus `page_size=8` sample
- REAL / HYBRID / SYNTHETIC badges
- Passport required sections
- Investigation Workspace scores + docked Copilot
- evidence timeline
- Risk Fusion V2 review-priority copy
- ML evidence
- contextual intelligence
- lifecycle
- Jan-Sakshi
- Copilot
- new-project assessment
- unavailable / inconclusive / loading / error states

Existing tests were not deleted because the UI changed.

---

## 23. Build

`npm run build` succeeded.

Confirmed routes:

| Route | Build |
| --- | --- |
| `/` | static |
| `/search` | static |
| `/projects/[id]` | dynamic |
| `/projects/[id]/investigate` | dynamic |
| `/projects/[id]/graph` | dynamic |
| `/jan-sakshi` | static |
| `/demo` | static |
| `/demo/[caseId]` | dynamic |
| `/assess-new-project` | static |
| `/need-impact` | static |
| `/reviews` | static |
| `/login` | static |

---

## 24. Browser smoke test result

**BROWSER SMOKE TEST = UNAVAILABLE**

No interactive browser session was available in this environment. Verification used frontend tests plus the production build.

---

## 25. Known limitations

- Fleet-wide Investigation Priority, Evidence Confidence, review queues, and insufficient-evidence indexes remain Unavailable. The UI does not invent them.
- Project intelligence pages (Passport, Workspace, Graph, Copilot, Lifecycle) still require a selected project.
- Satellite live imagery remains unavailable unless a provider is configured; the UI now states that explicitly.
- Officer login remains a prototype shell.
- Reviews remains a shell, not a fleet queue.
- Graph layout math is unchanged; only surrounding chrome and node colours were updated.
- Visual regression tooling was not added. The repository did not already have a screenshot/visual suite.

---

## 26. Screenshots / pages validated

Automated tests and production build covered:

- Dashboard
- Search
- Project Digital Passport
- Investigation Workspace
- Relationship Graph
- Demo Center
- New Project Assessment
- Need & Impact
- Jan-Sakshi
- Login
- Reviews

Manual visual click-through was not performed.

---

## Governance check

The redesigned UI does not display:

- Fraud detected
- Fraud probability as a legal conclusion
- Fraud risk percentage
- Corrupt project
- Confirmed wrongdoing

It continues to use:

- Anomaly signal
- Review priority
- Evidence mismatch
- Potential overlap
- Needs review
- Inconclusive
- Insufficient evidence
- Unavailable
