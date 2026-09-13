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
- Do not edit files placed in `raw/`.
- The database is loaded from `data/processed/mplads_works_cleaned.csv`. Raw files are not edited.

## Raw extracts and provenance

Place public MPLADS tabular files in `data/raw/` (`.csv`, `.tsv`, `.xlsx`, `.xls`, `.json`, `.parquet`).

For each file, add a sidecar named `<filename>.provenance.json` so source URL and extract/download date are preserved. Example:

```json
{
  "source_url": "https://www.data.gov.in/...",
  "extracted_at": "2026-09-09",
  "download_date": "2026-09-09",
  "publisher": "data.gov.in / MoSPI",
  "notes": "Public MPLADS extract"
}
```

A directory-level `PROVENANCE.json` with a `files` map keyed by filename is also accepted.

Filesystem mtime is recorded but is **not** treated as a confirmed extract date.

## Profiling (does not modify raw files)

From `backend/`:

```powershell
python -m app.pipeline.run
```

Writes `DATA_PROFILING_REPORT.md` and `DATA_DICTIONARY.md` at the repository root from **observed** columns only.

## Cleaning (does not modify raw files)

Primary source: `data/raw/github_vonter_india-mplads-works_MPLADS.csv` only. OpenCity MP-level summaries are not merged. Paid Dataful files are not used.

From `backend/`:

```powershell
python -m app.pipeline.clean_run
```

Writes:

- `data/processed/mplads_works_cleaned.csv`
- `data/processed/mplads_works_cleaned.provenance.json`
- `DATA_CLEANING_REPORT.md` (quality, limitations, lifecycle mapping)

`internal_project_id` is a SARVSAKSHI surrogate hash, not an official MPLADS work ID. District, vendor, coordinates, and expenditure are not added because they are absent from this extract.

## SQLite load (does not modify raw files)

From `backend/`:

```powershell
python -m app.pipeline.db_load_run
```

Writes `data/processed/sarvsakshi.db` from `mplads_works_cleaned.csv` plus its provenance sidecar. Schema: `DATABASE_SCHEMA.md`. The loader checks that the `project` row count matches the cleaned CSV. Evidence, risk, graph, citizen, and review tables stay empty.
