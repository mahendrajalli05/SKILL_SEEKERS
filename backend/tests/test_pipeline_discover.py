from __future__ import annotations

import json
from pathlib import Path

from app.pipeline.discover import build_provenance, discover_raw_files, sha256_file


def test_discover_skips_gitkeep_and_sidecar(tmp_path: Path) -> None:
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not tabular", encoding="utf-8")
    (tmp_path / "works.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "works.csv.provenance.json").write_text("{}", encoding="utf-8")

    found, skipped = discover_raw_files(tmp_path)

    assert [p.name for p in found] == ["works.csv"]
    assert ".gitkeep" in skipped
    assert "notes.txt" in skipped
    assert "works.csv.provenance.json" in skipped


def test_sha256_and_sidecar_provenance(tmp_path: Path) -> None:
    csv_path = tmp_path / "extract.csv"
    payload = "state,district\nAndhra Pradesh,Guntur\n"
    csv_path.write_text(payload, encoding="utf-8")
    sidecar = {
        "source_url": "https://example.invalid/mplads.csv",
        "extracted_at": "2026-09-09",
        "download_date": "2026-09-09",
        "publisher": "test fixture publisher",
        "notes": "TEST FIXTURE — not a government extract",
    }
    (tmp_path / "extract.csv.provenance.json").write_text(json.dumps(sidecar), encoding="utf-8")

    provenance = build_provenance(csv_path, tmp_path)

    assert provenance.sha256 == sha256_file(csv_path)
    assert provenance.source_url == sidecar["source_url"]
    assert provenance.extracted_at == "2026-09-09"
    assert provenance.download_date == "2026-09-09"
    assert provenance.missing_fields == []
    assert provenance.is_complete is True


def test_missing_sidecar_records_incomplete_provenance(tmp_path: Path) -> None:
    csv_path = tmp_path / "extract.csv"
    csv_path.write_text("a\n1\n", encoding="utf-8")

    provenance = build_provenance(csv_path, tmp_path)

    assert "source_url" in provenance.missing_fields
    assert "extracted_at_or_download_date" in provenance.missing_fields
    assert provenance.source_url is None
    assert provenance.file_mtime_iso is not None
