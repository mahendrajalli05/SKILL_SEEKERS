# Cost Intelligence V1.1 report

Date: 2026-09-10  
Engine: `cost-peer-v1.1`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID labels: held-out evaluation only

This engine measures **Allocation Cost Anomaly**: recorded `allocation_amount` versus comparable works. It does **not** measure expenditure anomaly, over-billing, physical quantity mismatch, or a legal finding. Investigation Priority is not assigned here.

---

## What changed

| Area | V1 | V1.1 |
| --- | --- | --- |
| Constituency geography | Any non-blank `constituency` was a place | Chamber labels such as `Sitting Rajya Sabha` / `Nominated Rajya Sabha` are excluded from constituency-level geography, with an explicit reason |
| Work type | Exact title only | Deterministic token Jaccard on observed titles (light plural strip). Similar road titles group together. No official sector list |
| Peer quality | Missing; large loose groups looked high-confidence | `peer_quality` 0–100 plus a similarity rationale. Count alone does not raise confidence |
| Scoring | Blend of % deviation and raw-scale modified z. Tiny MAD → 100 from modest gaps | Log-scale modified z when titles are similar; otherwise multiplicative log-ratio (4× → 100). Loose mix + 33% no longer scores 100 |
| Evidence Confidence | Extra points for raw peer count (329 peers → 80) | Driven by peer quality and scope tightness. Capped at 90. Loose category mixes cap lower |
| Signal name | `cost_anomaly` | `allocation_cost_anomaly` |

`data/raw/` and the real extract were not modified. Synthetic scenario columns are never model inputs.

---

## Peer strategy

1. Same **geographic** constituency + same category + work-title Jaccard ≥ 0.50  
2. Same geographic constituency + broader category  
3. Same Andhra Pradesh state + same category + Jaccard ≥ 0.50  
4. Same Andhra Pradesh state + broader comparable work title (Jaccard ≥ 0.50, category optional)

Skipped when the constituency is blank or a house/chamber label. MP name is not a geography key. Minimum 5 usable positive-amount peers. Never fabricate peers.

Peer quality = geography tightness + median title Jaccard + category match + a small sufficiency bonus (not a bonus for n = 300). Loose title mixes are capped at 48–55.

---

## Score formula

Display baseline stays the **original-scale median** and P25–P75 expected range.

Let \(x\) be actual allocation and \(m\) the peer median, both > 0.

**If** log-MAD of peer amounts > 0 **and** median title Jaccard ≥ 0.35:

\[
z = 0.6745 \cdot \frac{\ln x - \mathrm{median}(\ln \mathrm{peers})}{\mathrm{MAD}(\ln \mathrm{peers})}
\]

\[
\mathrm{score} = \min\left(100,\ \mathrm{round}(100 \cdot |z| / 3.5)\right)
\]

3.5 is the Iglewicz–Hoaglin modified-z reference. Review flag 60 ⇔ \(|z| \approx 2.1\). This is a mapping cutoff, not a claim that “60 means high risk”.

**Else** (identical peer amounts, or a loose title mix):

\[
\mathrm{score} = \min\left(100,\ \mathrm{round}\left(100 \cdot \frac{|\ln(x/m)|}{\ln 4}\right)\right)
\]

Equal amounts → 0. A 4× (or ¼×) ratio → 100. A 2× ratio → 50 (not flagged). Score is monotonic in \(|\ln(x/m)|\) for a fixed peer set.

Deviation % for explanation: \((x-m)/m \times 100\), one decimal.

---

## Validation results

All **125** backend tests passed, including non-geographic constituencies, precise vs broad groups, peer quality, skewed amounts, outliers, insufficient peers, fallback, deterministic scoring, monotonicity, explanation wording, and synthetic-label leakage.

---

## 10 examples (5 real, 5 held-out HYBRID)

HYBRID `scenario_type` / `demo_case_id` were attached **after** scoring.

### Real

| Project | Constituency | Category | Amount | Peer scope | n | Quality | Median | Expected range | Dev | Cost Anomaly | Evidence Confidence |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: |
| 2430 lift irrigation | Sitting Rajya Sabha | Normal/Others | 50,000,000 | none (non-geographic) | 0 | 0 | — | — | — | — | 6 |
| 3715 school rooms | KURNOOL | Normal/Others | 267,000 | constituency + broader category | 329 | 48 | 200,000 | 199,950–200,000 | +33.5% | **21** | 42 |
| 50279 culverts | Sitting Rajya Sabha | Normal/Others | 0 | none | 0 | 0 | — | — | — | — | 0 |
| 3348 community halls | SRIKAKULAM | Repair and Renovation | 500,000 | AP state + work title | 335 | 63 | 1,000,000 | 500,000–2,000,000 | −50.0% | 19 | 48 |
| 21769 water tanks | ELURU | Normal/Others | 5,000,000 | AP state + category + title | 20 | 78 | 450,000 | 250,000–1,387,500 | +1011.1% | **67** | 61 |

2430 explanation (why not scored): `Sitting Rajya Sabha` is a chamber label, not a geographic constituency. Only 3 Andhra Pradesh title-similar peers after fallback. Insufficient evidence.

3715 explanation (why not flagged): Allocation is 33.5% above the median of 329 broader-category works. Score 21 is below the review flag of 60. Peer quality 48 because title Jaccard is 0.00.

21769 explanation (why flagged): Allocation is 1011.1% above the median of 20 comparable Andhra Pradesh water-tank works. Score 67. Peer quality 78.

### Held-out HYBRID

| Project | Constituency | Category | Amount | Peer scope | n | Quality | Median | Expected range | Dev | Cost Anomaly | Evidence Confidence | Held-out label |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 22177 DEMO_OVERBILL | ELURU | Repair and Renovation | 3,550,000 | none | 0 | 0 | — | — | — | — | 6 | OVERBILL |
| 26946 DEMO_CLEAN | KADAPA | Normal/Others | 3,500,000 | constituency + broader category | 110 | 48 | 487,500 | 400,000–500,000 | +617.9% | **100** | 42 | CLEAN |
| 52862 DEMO_STUCK | ANANTAPUR | Normal/Others | 1,000,000 | constituency + category + title | 14 | 100 | 500,000 | 500,000–500,000 | +100.0% | 50 | 82 | STUCK |
| 53637 DEMO_GHOST | VIZIANAGARAM | Normal/Others | 7,378,000 | constituency + broader category | 249 | 48 | 280,000 | 199,127–490,000 | +2535.0% | **100** | 42 | GHOST |
| 4744 COST_ANOMALY | GUNTUR | Normal/Others | 260,000 | constituency + category + title | 80 | 85 | 675,000 | 347,500–1,025,000 | −61.5% | 32 | 73 | COST_ANOMALY |

**Why DEMO_CLEAN can still have an Allocation Cost Anomaly:** the synthetic CLEAN label describes **expenditure behaviour** (spend stays within sanctioned amount). This engine compares **recorded allocation** with Kadapa peers. 3,500,000 versus a 487,500 peer median is a 7× allocation gap. That is a different signal. Evidence Confidence is only 42 because the peer titles are a loose Normal/Others mix.

DEMO_OVERBILL is an **expenditure > sanctioned** test case. Allocation-vs-peers has fewer than 5 comparable Repair-and-Renovation works, so this engine correctly returns insufficient evidence.

The held-out COST_ANOMALY row is also spend-vs-sanction. Its allocation sits below the Guntur title-similar median (score 32, not flagged).

---

## Before vs after (same projects)

| Case | V1 scope / n / score / confidence | V1.1 |
| --- | --- | --- |
| Sitting RS 50,000,000 | constituency+category / 661 / 100 / 80 | Non-geographic; insufficient (3 AP title peers); confidence 6 |
| Kurnool 267,000 | constituency+category / 329 / 77 / 80 | Same loose fallback, but score **21**, quality 48, confidence **42**, not flagged |
| Eluru water tanks 5,000,000 | AP state+title / 20 / 100 / 75 | Same scope; score **67** (log-robust); quality 78; confidence 61 |
| DEMO_CLEAN 3,500,000 | constituency+category / 110 / 100 / 80 | Still flagged (7× allocation); quality 48; confidence **42** |
| DEMO_STUCK 1,000,000 | exact title / 8 / 45 / 61 | Similar titles / 14 / **50** / quality 100 / confidence 82; 2× with identical peers is not a review flag |

---

## Remaining limitations

- No district, expenditure, vendor, GPS, sanction date, completion date, or verified material prices  
- Amount unit is unspecified  
- ~99% of works are `Normal/Others`; many unique titles still fall to a broad category mix (quality and confidence stay low)  
- State fallback is Andhra Pradesh only  
- `Sitting Rajya Sabha` works can only use AP state title peers; rare titles remain insufficient  
- Isolation Forest and material-price adjustment are still out of scope  
- This slice does not implement Time, Overlap, Compliance, Risk Fusion, or Investigation Priority
