"""Data pipeline: raw-file profiling, work-level cleaning, SQLite load,
and SYNTHETIC HYBRID enrichment.

Profiling never invents government fields or values and never writes back
to ``data/raw``. Cleaning writes ``data/processed/`` only and does not merge
OpenCity MP-level files. SQLite load reads the cleaned CSV only. Synthetic
enrichment writes ``data/synthetic/`` only and does not modify the real
project table.
"""
