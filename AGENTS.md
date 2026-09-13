# SARVSAKSHI — AI DEVELOPMENT RULES

## Project
SARVSAKSHI
MPLADS Project Integrity & Investigation Layer
SIH 2026 — Problem Statement SIH26102

## Core Purpose
Build an evidence-driven intelligence and verification platform
for proposed, ongoing and completed MPLADS works.

## Core Principle
AI recommends.
Authorized officers decide.

The system provides investigation priority and evidence confidence.
It does not legally determine fraud.

## IMPORTANT GOVERNANCE RULES

Never:
- say a project is legally "fraud"
- output a fraud probability as a legal conclusion
- autonomously sanction a project
- autonomously release government funds
- claim to replace eSAKSHI, CAG or PFMS
- invent documents, dates, evidence or facts
- claim exact satellite measurements when imagery cannot support them
- treat one citizen report as truth
- claim perfect AI-generated-image detection
- claim live government/private data unless actually available

Use:
- Investigation Priority
- Evidence Confidence
- Explainable evidence
- Human-in-the-loop decisions
- Inconclusive when evidence is insufficient

## PROJECT LIFECYCLE

The system must support:

1. FUTURE / PROPOSED
2. ONGOING
3. COMPLETED

All three stages use the same Project Digital Passport.

## CORE INTELLIGENCE

Cost Intelligence:
- region-aware
- district-aware
- project-type-aware
- peer-based
- use scale/rural-urban context when available
- optional dated material/SoR data only when sourced

Time Intelligence:
- peer duration
- schedule slippage
- expected completion

Overlap Intelligence:
- semantic similarity
- location
- amount
- dates
- GPS proximity when available

Compliance:
- transparent rule engine
- official MPLADS guideline references
- rule IDs
- NEVER treat the rule engine as ML

Relationship Graph:
- project
- agency
- district/place
- type
- amount
- timing
- similarity

Evidence Intelligence:
- image reuse
- perceptual hash
- metadata
- GPS/timestamp
- document extraction
- blueprint/BOQ extraction
- visual consistency
- optional weak AI-image/manipulation signal

Risk Fusion:
- combines evidence objects
- produces Investigation Priority
- separately produces Evidence Confidence
- must explain why flagged
- must support why-not-flagged

## PLAN VS CLAIM VS EVIDENCE

PLAN:
- sanctioned scope
- blueprint
- dimensions
- estimate
- milestones

CLAIM:
- reported progress
- amount used
- completion statement

EVIDENCE:
- documents
- photographs
- metadata
- geospatial evidence
- citizen evidence
- inspection evidence

The system should identify:
- consistent
- mismatch
- inconclusive

## CITIZEN / JAN-SAKSHI

Citizen evidence:
- work location proximity <= 500m
- live capture preferred
- watermark
- latitude
- longitude
- timestamp
- structured options
- rating
- optional text

Citizen evidence is supporting evidence only.
Aggregate independent reports.
Never treat one citizen report as truth.

## MILESTONE ADVISOR

The system recommends:
- PROCEED
- HOLD
- INSPECT

An authorized human makes the final decision.

Never integrate autonomous PFMS payment release in the prototype.

## COPILOT

The Investigation Copilot must be grounded in:
- project evidence
- stored facts
- comparable projects
- relationship findings
- guideline snippets

It must not invent evidence.

It should answer:
- why flagged?
- why not flagged?
- comparable projects?
- triggered rules?
- missing evidence?
- what should an inspector verify?

## DATA

Primary data:
- real/public MPLADS data
- preserve source URL
- preserve extraction date
- preserve dataset provenance

CAG cases:
- use for validation/reference
- do not invent nationwide fraud labels

Synthetic data:
- clearly mark as SYNTHETIC
- never present synthetic projects as real government projects

## BUILD PRIORITY

P0:
- real data
- search
- cost
- time
- overlap
- rules
- risk fusion
- evidence objects
- Project Digital Passport
- peers
- Plan vs Claim vs Evidence
- human review
- four demo cases
- Evidence Confidence
- Relationship Graph MVP
- grounded Copilot
- Need & Impact

P1:
- image authenticity signals
- geospatial consistency
- milestone UI
- Jan-Sakshi

P2:
- full satellite CV
- live PFMS control
- production-scale security
- continuous retraining
- deep external government APIs

## CODING RULE

Do not implement multiple unrelated features in one task.

Before modifying code:
1. Read this file.
2. Read ARCHITECTURE.md.
3. Read ROADMAP.md.
4. Explain planned changes.
5. Implement only the requested task.
6. Add tests.
7. Run tests.
8. Fix failures.
9. Update ROADMAP.md.

Do not change architecture without approval.