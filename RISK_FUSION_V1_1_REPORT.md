# Risk Fusion V1.1 report

Date: 2026-09-10  
Engine: `risk-fusion-v1.1`  
HTTP: `GET /api/v1/projects/{id}/risk`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID layer: `data/synthetic/` only, labelled HYBRID/TEST

This slice **only** changes how Investigation Priority is displayed. Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance Engine V1, Evidence Object V1, and Risk Fusion V1 signal mapping remain frozen.

It produces **Investigation Priority** (0–100 display) and **Evidence Confidence**. It does **not** determine fraud, does not output a fraud probability, and does not change those engines’ scores.

---

## What changed

V1 reported Investigation Priority as the un-renormalized weighted sum (theoretical maximum 70). Officers therefore never saw a true 0–100 Investigation Priority, even when every integrated signal was 100.

V1.1 keeps that missing-signal penalty and rescales the same raw total onto 0–100.

---

## Exact formula

Weights below are **prototype weights only. They are not official MoSPI weights.**

### Raw Risk (unchanged from V1)

Let \(s_i \in [0,100]\) be the assessable risk score of signal \(i\), and \(w_i\) its planned weight.

\[
\mathrm{Raw\ Risk} = \sum_{i \in \mathcal{A}} w_i \cdot s_i
\]

\(\mathcal{A}\) is the set of **assessable** integrated signals (disposition `WHY_FLAGGED` or `WHY_NOT_FLAGGED` with a usable score).

Unavailable, `NOT_ASSESSABLE`, `INCONCLUSIVE`, and not-yet-integrated slots contribute **0** and **their weights are not redistributed**.

Theoretical maximum of Raw Risk is \(0.70 \times 100 = 70\).

### Investigation Priority (V1.1 display)

\[
\mathrm{IP}_{0\text{–}100} = \frac{\mathrm{Raw\ Risk}}{0.70}
\]

Displayed Investigation Priority is that value clipped to \([0,100]\) and rounded (1 decimal on `investigation_priority_0_100`; integer half-up on `investigation_priority`).

The divisor is **always 0.70**, never the currently available weight.

Worked example (Cost = 100, all other integrated signals unavailable):

- `raw_risk` = 25
- `available_signal_weight` = 0.25
- `unavailable_signal_weight` = 0.45
- `investigation_priority_0_100` = 35.7
- displayed `investigation_priority` = 36

That must **not** become 100. Silent renormalization onto available signals only would be \(25 / 0.25 = 100\) and is forbidden.

All four integrated signals = 100:

- `raw_risk` = 70
- Investigation Priority = 100

No assessable signals:

- Raw Risk = 0
- Investigation Priority = 0
- explanation type `INSUFFICIENT_EVIDENCE` (inconclusive)

### Evidence Confidence (unchanged)

Evidence Confidence is **completely separate**. V1.1 does not copy Investigation Priority into Evidence Confidence. Mode caps remain REAL 90, HYBRID 72, SYNTHETIC 55.

---

## New response fields

| Field | Meaning |
| --- | --- |
| `raw_risk` | Un-renormalized weighted sum (max 70) |
| `investigation_priority` | Integer 0–100 display used for bands and recommendations |
| `investigation_priority_0_100` | Same formula, 1 decimal |
| `available_signal_weight` | Sum of assessable integrated weights |
| `unavailable_signal_weight` | \(0.70\) minus available (integrated slots only; excludes reserved 30%) |
| `evidence_coverage` | available / 0.70 |

`unused_weight` still includes reserved future slots (for example Cost-only: available 0.25, unavailable 0.45, unused 0.75).

---

## Weights (frozen)

| Slot | Weight | Source |
| --- | ---: | --- |
| Cost | 25% | Cost Evidence Object `allocation_cost_anomaly` score |
| Schedule | 15% | Time Evidence Object `time_anomaly` score |
| Overlap | 15% | Overlap Evidence Object `potential_overlap` score |
| Compliance | 15% | mapped from compliance evidence (unchanged) |
| Field / graph / citizen / geo / image / document / milestone | 30% | not yet integrated |

---

## Recommended action

Recommendations use the **normalized Investigation Priority** together with Evidence Confidence. Not a legal or administrative decision.

| Investigation Priority | Band | Action |
| --- | --- | --- |
| 0–24 | LOW | MONITOR |
| 25–44 | MEDIUM | REVIEW |
| 45–59 | HIGH | INSPECT |
| 60–100 | HIGH | INVESTIGATE |

Explanation always states:

1. Investigation Priority (display 0–100, with Raw Risk / 0.70)
2. Evidence Confidence (separate)
3. available signals
4. unavailable signals
5. top contributing signals

---

## Tests

**334** backend tests passed (0 failed), including frozen Cost/Time/Overlap/Compliance/Evidence suites plus Risk Fusion V1.1:

1. all four signals = 100 → IP = 100  
2. one signal only retains the missing-signal penalty (Cost=100 → IP=36, not 100)  
3. no signals → 0 / `INSUFFICIENT_EVIDENCE`  
4. monotonicity  
5. bounded 0–100  
6. deterministic result  
7. missing signals are not silently renormalized  
8. Evidence Confidence remains independent  
9. REAL and HYBRID remain distinguishable  

```powershell
cd backend
python -m pytest
python -m app.engines.fusion.evaluate_run
```

---

## Old vs new (10 REAL examples)

V1 IP was `round(Raw Risk)` (max 70). V1.1 is `Raw Risk / 0.70` (max 100). Evidence Confidence is unchanged.

| Project | Case | V1 IP | V1.1 IP | Raw Risk | Avail w | Unavail w | Coverage | EC | Action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 846 | water tankers | 11 | **16** | 11.25 | 0.30 | 0.40 | 0.4286 | 40 | MONITOR |
| 232 | Hindupur roads | 13 | **19** | 13.20 | 0.55 | 0.15 | 0.7857 | 65 | MONITOR |
| 217 | Hindupur crematorium | 12 | **17** | 12.15 | 0.55 | 0.15 | 0.7857 | 58 | MONITOR |
| 3348 | Srikakulam halls | 16 | **24** | 16.45 | 0.55 | 0.15 | 0.7857 | 60 | MONITOR |
| 3715 | Kurnool school rooms | 12 | **18** | 12.30 | 0.55 | 0.15 | 0.7857 | 58 | MONITOR |
| 21769 | Eluru water tanks | 29 | **41** | 28.90 | 0.55 | 0.15 | 0.7857 | 62 | REVIEW |
| 5263 | Ongole roads | 15 | **21** | 15.00 | 0.55 | 0.15 | 0.7857 | 65 | MONITOR |
| 21192 | Araku sanitation | 19 | **28** | 19.30 | 0.55 | 0.15 | 0.7857 | 65 | REVIEW |
| 233 | Anakapalle borewells | 24 | **35** | 24.35 | 0.55 | 0.15 | 0.7857 | 65 | REVIEW |
| 234 | Anakapalle multi-gym | 8 | **12** | 8.10 | 0.55 | 0.15 | 0.7857 | 58 | MONITOR |

Schedule is not assessable on REAL works. Reserved 30% is unavailable on every row. 846 has Cost unavailable as well, so available weight is only 0.30 (Overlap + Compliance).

21192 and 233 move from MONITOR to REVIEW because the display scale is now 0–100. That is the intended V1.1 ranking change, not a new engine finding.

---

## 10 HYBRID evaluation examples

HYBRID labels were attached **after** fusion. Evidence Confidence is unchanged from V1 (capped at 72).

| Project | Case | V1 IP | V1.1 IP | Raw Risk | Avail w | Unavail w | EC | Action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 23028 | overlap group A | 23 | **33** | 23.05 | 0.55 | 0.15 | 65 | REVIEW |
| 9982 | overlap group B | 11 | **16** | 11.40 | 0.55 | 0.15 | 65 | MONITOR |
| 26946 | DEMO_CLEAN | 41 | **59** | 41.20 | 0.70 | 0.00 | 71 | INSPECT |
| 22177 | DEMO_OVERBILL | 12 | **17** | 12.00 | 0.45 | 0.25 | 47 | MONITOR |
| 52862 | DEMO_STUCK | 37 | **52** | 36.65 | 0.70 | 0.00 | 72 | INSPECT |
| 53637 | DEMO_GHOST | 35 | **51** | 35.35 | 0.70 | 0.00 | 72 | INSPECT |
| 46124 | NORMAL | 25 | **35** | 24.70 | 0.55 | 0.15 | 65 | REVIEW |
| 15149 | overlap GPS 119 m | 14 | **20** | 13.65 | 0.55 | 0.15 | 65 | MONITOR |
| 16180 | MIXED overlap+cost | 26 | **37** | 25.95 | 0.70 | 0.00 | 72 | REVIEW |
| 25533 | COST_ANOMALY | 26 | **38** | 26.25 | 0.70 | 0.00 | 72 | REVIEW |

DEMO_OVERBILL remains LOW: Cost is unavailable, so the 0.25 Cost weight is not redistributed. IP 17 is not a claim that over-billing is absent.

DEMO_CLEAN can still have a high **allocation** Cost signal. The held-out CLEAN label is not a fusion input.

---

## Maximum / minimum

| Case | Raw Risk | IP 0–100 | Displayed IP |
| --- | ---: | ---: | ---: |
| All four signals = 100 | 70 | 100.0 | **100** |
| Cost = 100, others missing | 25 | 35.7 | **36** (not 100) |
| No assessable signals | 0 | 0.0 | **0** (inconclusive) |

---

## Limitations

- Prototype weights are not official MoSPI weights.  
- Display scaling does not invent evidence for the reserved 30%.  
- REAL Time Anomaly remains not assessable.  
- Overlap V1 still flags generic repeated titles; fusion inherits that review-queue signal.  
- High Investigation Priority is not fraud.  
- This slice does not implement Relationship Graph, Digital Passport UI, documents, vision, geo, citizen, milestone, Copilot, or frontend.

STOP. Graph, Passport, Copilot, and frontend were not built in this slice.
