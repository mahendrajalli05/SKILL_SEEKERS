# External contextual data

Provenance-first public contextual snapshots used by Real Contextual Data
Enrichment V1. These files are **not** MPLADS project records.

| Path | Purpose |
| --- | --- |
| `sources/registry.json` | Source registry (publisher, URL, limitations, active flag) |
| `snapshots/` | Verified public extracts used in REAL mode |
| `fixtures/` | Small labelled TEST/SYNTHETIC fixtures for HYBRID tests only |

Rules:

- Do not place files here into `data/raw/`.
- Do not merge these values into `project` rows.
- Do not treat a state-level statistic as a project-specific fact.
- Do not treat absence of a value as zero.
