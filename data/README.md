# Data directory

This folder holds MPLADS extracts and derived files. It does **not** ship government data.

| Path | Purpose |
| --- | --- |
| `raw/` | Original public extracts plus provenance (`source_url`, extract date, SHA256) |
| `processed/` | Cleaned tables and the local SQLite file |
| `guidelines/` | Official MPLADS Guidelines PDF and extracted snippets |
| `demo/` | Only explicitly labelled `SYNTHETIC` artefacts, when those are added later |

Rules:
- Do not invent government fields or values.
- Do not place unlabeled synthetic rows next to real extracts.
- The database starts empty until a real public extract is ingested (Phase 2).
