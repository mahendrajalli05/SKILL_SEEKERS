# UI Polish V1 report

Date: 2026-09-10  
Layer: `ui-polish-v1`

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph V1 calculations, Need & Impact scoring, Milestone Advisor, Jan-Sakshi, Investigation Copilot retrieval/guardrails, Satellite, Geospatial, Image Evidence, Image Forensics, Documents/Blueprint, Plan → Claim → Evidence, Lifecycle orchestration, Search backend.

This slice is **visual / UX integration only**. It turns the existing End-to-End Lifecycle V1 surfaces into one cohesive government decision-support interface. It does **not** add intelligence features, does not invent statistics, and does not change engine outputs.

---

## Architecture

```
Existing FastAPI intelligence APIs (unchanged)
        ↓
Next.js thin client
        ↓
Shared UI tokens, badges, page states, AppHeader, ProjectSubNav
        ↓
Officer Dashboard (pilot search totals only, page_size=1)
Search / Passport / Investigation Workspace / Graph
        ↓
Lazy tabs (workspace) and LazyDisclosure (passport)
so unused modules are not mounted
```

No backend routes were added. Dashboard counts reuse `GET /api/v1/projects` with `page_size=1` and observed STATUS filters (Unsanctioned + Sanctioned → Future, Ongoing, Completed). Fleet-wide Investigation Priority, Evidence Confidence, review queues, and insufficient-evidence indexes are shown as **Unavailable** rather than computed by loading the 56,138-row extract.

---

## 1. Product identity

Header and pages consistently show:

- SARVSAKSHI
- SIH26102
- MPLADS Project Integrity & Investigation Layer
- Current Pilot: Andhra Pradesh
- Data mode: **REAL DATA** or **HYBRID DEMO**

Synthetic values remain labelled. Hybrid pages also show:

> Prototype simulation: some fields are synthetic and are not official MPLADS records.

---

## 2. Global navigation

Primary nav (operational pages only):

- Dashboard
- Search
- Need & Impact
- Jan-Sakshi
- Projects / Investigation (opens Search; project routes exist only after a work is selected)

Reviews is **not** in primary nav (the page remains a shell).

On `/projects/[id]/*`, a project sub-nav provides:

- Digital Passport
- Investigation Workspace
- Relationship Graph
- Milestones (workspace hash)
- Copilot

---

## 3. Dashboard

Officer dashboard cards from available search totals only:

- Projects in current AP pilot
- Future / Ongoing / Completed (from observed STATUS)

Explicitly **Unavailable** (not zero):

- Investigation Priority distribution
- Evidence Confidence (fleet-wide)
- Projects requiring review
- Projects with insufficient evidence

Actions: Search Projects, Open High-Priority Cases (honest note: no fleet-wide high-priority index), Open Need & Impact, Open Investigation Workspace.

HYBRID mode states that prototype/demo values may use synthetic enrichment.

---

## 4. Search

Search behaviour is unchanged: State → Constituency → Category → Status → Text Search; Scheme ID / internal_project_id / work / MP; AP pilot; URL state; Enter/Search commit.

Visual only: spacing, table typography, REAL/HYBRID badges, loading/empty/error states, stacked table on small screens, labelled form controls.

---

## 5. Project Digital Passport

Top identity: Scheme ID, Internal Project ID, Data Mode, Lifecycle State.

Named sections: PROJECT IDENTITY, FINANCE / RECOMMENDATION, INTELLIGENCE, EVIDENCE, PLAN / CLAIM / EVIDENCE, DOCUMENTS, IMAGES, GEOSPATIAL, SATELLITE, MILESTONES, JAN-SAKSHI, RELATIONSHIP GRAPH, NEED & IMPACT, LIFECYCLE.

Heavy modules (PCE, documents, images, geospatial, satellite) load only when the officer opens the disclosure. Closed sections say the data is unavailable until opened rather than implying records exist.

---

## 6. Investigation Workspace

Primary application screen. Top summary: project, lifecycle, Investigation Priority 0–100, Evidence Confidence 0–100, recommendation.

Tabs (lazy-mounted): Why?, Evidence, Risk Signals, Plan → Claim → Evidence, Documents, Images, Forensics, Geospatial, Satellite, Citizen, Milestones, Relationship Graph, Need & Impact, Copilot.

Officer decision and evidence timeline remain on the page. Existing panels are not removed.

---

## 7. Status badges

Shared styles for REAL / HYBRID / SYNTHETIC, CONSISTENT / MISMATCH / INCONCLUSIVE, PROCEED / HOLD / INSPECT / REVIEW / MONITOR / NEED MORE INFORMATION, plus Unavailable / Not assessable / Insufficient evidence.

Ordinary evidence signals use restrained colours. The UI does not say “fraud confirmed”.

---

## 8. Risk presentation

Risk Fusion V1.1 and V2 displays still show Investigation Priority and Evidence Confidence on a 0–100 scale, Why?, contributing / correlated / conflicting / unavailable evidence. Calculations are unchanged. No fraud probability.

---

## 9. Copilot

Copilot is a workspace tab. Suggested prompts always include:

- Why is this project high priority?
- What evidence supports this?
- What information is missing?
- What should I inspect next?
- Summarize Plan → Claim → Evidence.

API-suggested questions are preserved. Retrieval and guardrails are unchanged.

---

## 10. Graph

Relationship Graph V1 API and layout math are unchanged. The officer view adds a legend, clearer hierarchy, and hash-safe mode URLs. Central project, connected nodes, relationship details, findings, and graph evidence remain.

---

## 11–16. Honesty, responsive, accessibility, states

- REAL DATA vs HYBRID DEMO on important project pages
- Stacked search table below 768px; `max-w-7xl`; no invented overflow widgets
- Skip link, `aria-current`, labelled controls, `:focus-visible`, heading hierarchy
- Shared Loading / Unavailable / Inconclusive / Insufficient Evidence / API Error / No Results
- Unknown and unavailable values are not shown as zero or low risk

---

## Testing

Frontend tests added/updated for dashboard, navigation, AP pilot, REAL/HYBRID badges, search, passport, investigation workspace, lifecycle empty state, risk cards, evidence cards, Copilot prompts, graph HYBRID labelling, loading/empty/error, lazy tabs/disclosures, and skip-link / form labels.

Backend tests were not changed.

Results:

- Backend: **656 passed**
- Frontend: **95 passed**
- Next.js build: **compiled successfully**

Live browser click-through was not available in this environment. Verification used the test suite, Next.js typecheck/build, and the existing page contracts.

---

## Performance

- Dashboard fetches health plus five `page_size=1` search totals. It does not load every module for every project.
- Investigation Workspace mounts tab panels on demand.
- Passport document/image/geo/satellite/PCE panels mount only when opened.
- The 56,138-row extract is not loaded into the browser.

---

## Files

Created (frontend UI only): `AppHeader`, `ProjectSubNav`, `OfficerDashboard`, `StatusBadge`, `PageState`, `SectionCard`, `WorkspaceTabs`, `LazyDisclosure`, `statusBadge.ts`, `dashboardStats.ts`, polish tests, this report.

Changed (frontend UI only): `globals.css`, `AppShell`, `PilotChrome`, `DataModeBanner`, `display.ts`, dashboard/search/passport/investigate/graph/jan-sakshi/need-impact/reviews/login pages, project layout, and visual wrappers around existing cards/panels.

No engine, fusion, search-backend, or schema files were modified.
