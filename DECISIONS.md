# SARVSAKSHI Engineering Decisions

## D001 — Architecture
Use a modular monolith.

Frontend:
Next.js

Backend:
FastAPI

Database:
SQLite for MVP

## D002 — Risk terminology
Use:
Investigation Priority

Do not use:
Fraud probability as a legal conclusion.

## D003 — Fraud classifier
Do not build a supervised national fraud classifier.
Reliable national fraud labels are unavailable.

## D004 — Compliance
Compliance is a deterministic rule engine.

## D005 — Regional intelligence
Risk/cost analysis must use contextual peer groups:
region + district + work type + scale/context where available.

## D006 — Evidence
Every significant finding must be stored as an evidence object.

## D007 — Evidence Confidence
Keep Evidence Confidence separate from Investigation Priority.

## D008 — Human authority
AI recommends.
Authorized officer decides.

## D009 — PFMS
No autonomous fund release in prototype.

## D010 — Citizen evidence
One citizen report does not establish truth.
Use trusted, aggregated signals.

## D011 — Satellite
Return inconclusive when imagery cannot support the claim.

## D012 — LLM
LLM must be grounded in stored evidence and rules.
No invented facts.

## D013 — Synthetic data
Synthetic records must be explicitly labelled.

## D014 — Geography
Initial pilot:
Coastal Andhra Pradesh,
subject to actual data availability.

## D015 — Demo cases
Ghost
Over-bill
Stuck
Clean

## D016 — Peer Comparison Geography

Primary peer scope:
same constituency + same category/work type.

Fallback order:
1. Same constituency + same category/work type
2. Same constituency + broader category
3. Same Andhra Pradesh state + same category/work type
4. Same Andhra Pradesh state + broader comparable group

The system must display which peer scope was used.

Do not use MP name as the primary geographic peer group.
MP may be used only as contextual/relationship information.

If insufficient comparable records exist, report insufficient evidence or expand to the next peer level. Never fabricate peers.