# Overlap Intelligence V1 report

Date: 2026-09-10  
Engine: `overlap-multi-v1`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID layer: `data/synthetic/` only, labelled HYBRID/TEST

This engine measures **Potential Overlap** and **Potential Duplicate**: multi-signal similarity of recorded MPLADS works. It does **not** conclude that a work is fraudulent or definitely duplicated. Investigation Priority is not assigned here.

Cost Intelligence V1.1 and Time Intelligence V1 are frozen and were not modified.

---

## Dual mode

| Mode | Inputs | What is scored |
| --- | --- | --- |
| **REAL** | Work description, observed category, constituency, allocation, recommendation date, sparse place text (`city` / `ward` / `block` / `village`) | No GPS. Geographic evidence is reported unavailable when place text is missing. |
| **HYBRID_TEST** | Same observed fields plus synthetic latitude/longitude from the 10,000-record HYBRID layer | GPS proximity is scored when both works have coordinates. Outputs are labelled HYBRID/TEST. |

The real extract has **no** official work ID, verified district, vendor, verified expenditure, GPS, sanction date, or completion date. Those fields are never invented.

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, and `coordinate_source` are excluded from model inputs. Held-out labels are attached only after scoring.

MP name is not a geographic key.

---

## Architecture

The engine lives under `backend/app/engines/overlap/` and is independent of Cost, Time, Compliance, Risk Fusion, Graph, Copilot, frontend, citizen, milestone, and satellite.

Flow:

1. Preserve original `source_work` text.  
2. Normalise a copy for embeddings (Unicode/whitespace, strip observed `NA -` / `WS/…` prefixes).  
3. Generate **blocked candidates** (not all-pairs).  
4. Embed candidate titles (Sentence Transformers `all-MiniLM-L6-v2` when installed; otherwise the deterministic hashed-token + character n-gram backend used for tests and this evaluation).  
5. Cosine similarity on those vectors.  
6. Combine with category, geographic constituency, amount, recommendation-date proximity, place text, and GPS when present.  
7. Classify as Potential Duplicate, Potential Overlap, not linked, or insufficient evidence.  
8. Return Evidence Confidence separately. Persist to `evidence_object` and `overlap_link` only.

HTTP: `GET /api/v1/projects/{id}/overlap-intelligence` (`mode=real` or `hybrid-test`).

---

## Candidate-generation strategy

Do not compare all 56,138 rows to every other row.

Blocking keys:

1. Same **geographic** constituency + same observed category (full pairs only if the block has ≤ 80 members; larger blocks also require rare work-type token overlap or an exact normalised title).  
2. Exact normalised title inside the same geographic constituency.  
3. For non-geographic chamber labels (`Sitting Rajya Sabha`, `Nominated Rajya Sabha`): rare content tokens + same category + date window.  
4. Recommendation-date window of **180 days** when both dates exist (missing dates are not dropped).  
5. HYBRID GPS cells (~550 m) plus 8-neighbours, then haversine.

Per subject, at most 250 candidates are scored. Display keeps the top 10 matches.

Rare blocking tokens are observed title tokens after stripping generic filler (`construction`, `building`, `works`, …). That filler list is not an official work-type taxonomy.

---

## Similarity formula

Available signals only; missing fields are **unavailable**, not zero. Weights are renormalised over the signals that exist.

| Signal | Weight | Value |
| --- | ---: | --- |
| Semantic cosine | 0.40 | Clip cosine to [0, 1] |
| Geographic constituency match | 0.15 | 1 if both usable and equal, else 0 |
| Observed category match | 0.10 | 1 if both non-blank and equal |
| Amount similarity | 0.15 | \(1 - |a-b|/\max(a,b)\) for positive amounts |
| Date proximity | 0.10 | \(1 - \mathrm{days}/90\), floored at 0 |
| Place-text Jaccard | 0.10 (0.05 if GPS is also present) | Tokens from city/ward/block/village |
| GPS (HYBRID or real coords only) | 0.25 | \(1 - \mathrm{metres}/500\) |

\[
\mathrm{overall} = \frac{\sum_i w_i v_i}{\sum_i w_i}\quad\text{for available }i
\]

\[
\mathrm{overlap\ score} = \mathrm{round}(100 \cdot \mathrm{overall})
\]

Supporting signals (for duplicate vs overlap): category match; geographic constituency match; amount similarity ≥ 0.80; recommendation gap ≤ 45 days; place Jaccard ≥ 0.50; GPS ≤ 500 m.

**Potential Duplicate:** semantic ≥ 0.92 **and** at least two supporting signals.  
**Potential Overlap:** high semantic similarity (≥ 0.85), or semantic ≥ 0.72 with support / overall ≥ 0.58, or HYBRID GPS ≤ 500 m with constituency or location support. High semantic similarity **alone** is Potential Overlap, never a duplicate.  
**Not linked / insufficient:** below those thresholds, or missing descriptions without GPS.

Review flag 60 on the 0–100 overlap score, or any Potential Duplicate.

---

## Thresholds

| Name | Value |
| --- | ---: |
| Semantic candidate / overlap / high / near-duplicate | 0.55 / 0.72 / 0.85 / 0.92 |
| Amount similar | 0.80 |
| Date proximate / candidate window / decay | 45 / 180 / 90 days |
| GPS proximity | 500 m |
| Overall overlap minimum | 0.58 |
| Supporting signals for duplicate | 2 |
| Full-block size / max candidates / display | 80 / 250 / 10 |
| REAL Evidence Confidence cap | 66 |
| HYBRID GPS Evidence Confidence cap | 70 |

---

## Validation

All **223** backend tests passed, including:

- text normalisation and original-text preservation  
- embedding determinism (hashed backend)  
- candidate generation (not all-pairs)  
- cosine similarity  
- multi-signal scoring and thresholds  
- missing-field handling  
- duplicate text and near-duplicate text  
- false-positive prevention (same category / amount / constituency, different works)  
- deterministic output  
- synthetic-label leakage  

---

## 10 real-project examples

GPS is absent on every real row. Place text is used when present.

| Project | Constituency | Title (truncated) | Candidates | Matches | Semantic | Const. | Category | Amount | Date gap | Place | Overlap | Conf. | Outcome |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 846 water tankers | Sitting Rajya Sabha | Purchase of mobile water tankers | 250 | 10 | 1.00 | no | yes | 0.33 | 0 | 1.00 | **75** | 66 | Potential Duplicate |
| 232 Hindupur roads | HINDUPUR | Construction of roads, link roads… | 61 | 10 | 1.00 | yes | yes | 0.50 | 38 | 1.00 | **88** | 66 | Potential Duplicate |
| 217 Hindupur crematorium | HINDUPUR | Crematoriums or structures on burial… | 61 | 3 | 1.00 | yes | yes | 0.50 | 57 | 0.50 | **81** | 66 | Potential Duplicate |
| 3348 Srikakulam halls | SRIKAKULAM | Community centers and community halls | 36 | 10 | 1.00 | yes | no | 0.99 | 19 | 0.00 | **78** | 66 | Potential Duplicate |
| 3715 Kurnool school rooms | KURNOOL | Rooms and halls in school and colleges | 3 | 0 | 0.49* | — | — | — | — | — | 47 | 66 | Not linked |
| 21769 Eluru water tanks | ELURU | Construction of water tanks | 2 | 1 | 1.00 | yes | yes | 0.46 | 4 | 0.00 | **81** | 66 | Potential Duplicate |
| 5263 Ongole roads | ONGOLE | Construction of roads, link roads… | 131 | 10 | 1.00 | yes | yes | 1.00 | 0 | 1.00 | **100** | 66 | Potential Duplicate |
| 21192 Araku sanitation | ARAKU(ST) | Purchase of mobile sanitation equipment | 51 | 10 | 1.00 | yes | yes | 0.83 | 0 | 1.00 | **97** | 66 | Potential Duplicate |
| 233 Anakapalle borewells | ANAKAPALLE | Installing tube-wells and borewells | 63 | 5 | 1.00 | yes | yes | 0.50 | 34 | 0.00 | **79** | 66 | Potential Duplicate |
| 234 Anakapalle multi-gym | ANAKAPALLE | Construction of buildings for multi-gym | 63 | 0 | 0.22* | — | — | — | — | — | 54 | 66 | Not linked |

\* Best rejected candidate (not a kept match). GPS column is always unavailable on REAL.

846 explanation: `Sitting Rajya Sabha` is not geographic constituency, so constituency match is false. Identical tanker wording plus category, same-day recommendation, and matching place text still produce a Potential Duplicate for review. Not a legal finding.

3715 explanation (why not linked): 49% semantic similarity against Kurnool candidates is below the overlap threshold even with category and constituency support.

234 explanation (why not linked): 22% semantic similarity against 63 Anakapalle candidates. Same constituency and category are not enough.

---

## 10 HYBRID evaluation examples

HYBRID `scenario_type` / `demo_case_id` / `overlap_group_id` were attached **after** scoring. Coordinates are SYNTHETIC.

| Project | Constituency | Held-out label | Candidates | Matches | Semantic | GPS m | Overlap | Conf. | Outcome |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 23028 electricity | ANANTNAG | OVERLAP group 0054 | 45 | 10 | 1.00 | 59444 | **72** | 70 | Potential Duplicate |
| 9982 street lights | ANANTNAG | OVERLAP group 0054 | 45 | 10 | 1.00 | 56389 | **76** | 70 | Potential Duplicate |
| 26946 DEMO_CLEAN culverts | KADAPA | CLEAN | 16 | 0 | 0.26* | 5450* | 43 | 70 | Not linked |
| 22177 DEMO_OVERBILL lift | ELURU | OVERBILL | 0 | 0 | — | — | — | 16 | Not linked |
| 52862 DEMO_STUCK rooms | ANANTAPUR | STUCK | 43 | 2 | 1.00 | 8346 | **68** | 70 | Potential Duplicate |
| 53637 DEMO_GHOST prosthetics | VIZIANAGARAM | GHOST | 38 | 0 | 0.13* | 1.8e6* | 35 | 70 | Not linked |
| 46124 NORMAL roads | KURNOOL | NORMAL | 4 | 3 | 1.00 | 2930 | **73** | 70 | Potential Duplicate |
| 15149 school rooms | DAVANAGERE | OVERLAP group 0069 | 9 | 4 | 1.00 | **119** | **91** | 70 | Potential Duplicate |
| 16180 MIXED libraries | KANCHEEPURAM(SC) | MIXED+OVERLAP 0119 | 56 | 10 | 1.00 | — | **93** | 70 | Potential Duplicate |
| 25533 COST labs | ARAKU(ST) | COST_ANOMALY | 70 | 10 | 1.00 | — | **93** | 70 | Potential Duplicate |

26946 explanation (why not linked): 26% semantic similarity, GPS about 5.4 km. Held-out CLEAN is not a model input.

22177 explanation (insufficient candidates): Repair and Renovation in Eluru has no blocked HYBRID peers. Evidence Confidence 16.

15149 explanation: 119 m synthetic GPS plus identical school-room wording, same constituency/category/amount/date. Potential Duplicate for review. HYBRID/TEST only.

53637 explanation: offshore DEMO_GHOST coordinates are ~1,800 km from Vizianagaram peers. Not linked on overlap.

---

## False-positive observations

1. **Generic repeated titles.** Many extract rows share the same `NA - Construction of …` / `WS/…` title inside a constituency. Semantic cosine is then 1.00. With category, constituency, and a close recommendation date, V1 records Potential Duplicate. That is a **source-text limitation**, not proof that the government recorded two copies of one work. Officers should treat identical template titles as a review queue, not as confirmed duplication.

2. **Place-text collision.** Sparse `block`/`village` strings can be identical across works (Jaccard 1.00) without GPS. REAL therefore sometimes reports “geographic evidence available” from place tokens even though coordinates do not exist.

3. **HYBRID overlap groups vs identical titles.** Held-out OVERLAP groups are GPS+vendor clusters and may have **different** titles. Ranking by overall score can surface a same-title peer tens of kilometres away ahead of the ~100 m group-mate (see ANANTNAG 23028/9982, GPS ~56–59 km on the top match). Group 0069 (Davanagere 15149) is the cleaner GPS case (119 m).

4. **Same constituency / category / amount are not enough.** Unit tests and real 234 (multi-gym vs other Anakapalle works at 22% semantic) stay not linked. Same amount on unrelated titles (ambulance vs tanks) is not treated as overlap.

5. **High semantic similarity alone is Potential Overlap**, never Potential Duplicate, unless two other signals agree.

---

## Remaining limitations

- Real works have no GPS; HYBRID coordinates are SYNTHETIC and Evidence Confidence is capped  
- Place text is sparse; many titles are generic templates  
- Amount unit is unspecified  
- Chamber constituencies are excluded from geography  
- This evaluation used the deterministic hashed-token embedder so tests do not download model weights. Sentence Transformers `all-MiniLM-L6-v2` is the preferred production backend when `sentence-transformers` is installed; cosine scoring is unchanged  
- This slice does not implement Compliance, Risk Fusion, Relationship Graph, Copilot, frontend, citizen, milestone, or satellite  
