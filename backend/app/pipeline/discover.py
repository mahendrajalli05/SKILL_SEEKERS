from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.pipeline.types import Provenance

TABULAR_SUFFIXES = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet"}
SKIP_FILENAMES = {".gitkeep", "thumbs.db", ".ds_store"}
PROVENANCE_FILENAMES = {"provenance.json", "provenance.md"}
MAX_HASH_BYTES = 1024 * 1024 * 512  # 512 MiB; still hash in streaming either way


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mtime_iso(path: Path) -> str | None:
    try:
        ts = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def _sidecar_for(path: Path) -> Path | None:
    candidates = [
        path.with_name(path.name + ".provenance.json"),
        path.with_suffix(path.suffix + ".provenance.json"),
        path.with_name(path.stem + ".provenance.json"),
        path.parent / "PROVENANCE.json",
        path.parent / "provenance.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_sidecar(path: Path, relative_name: str) -> tuple[dict, Path | None]:
    sidecar = _sidecar_for(path)
    if sidecar is None:
        return {}, None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, sidecar
    if isinstance(payload, dict) and "files" in payload and isinstance(payload["files"], dict):
        per_file = payload["files"].get(relative_name) or payload["files"].get(path.name) or {}
        if isinstance(per_file, dict):
            return per_file, sidecar
        return {}, sidecar
    if isinstance(payload, dict):
        return payload, sidecar
    return {}, sidecar


def _missing_provenance_fields(source_url: str | None, extracted_at: str | None, download_date: str | None) -> list[str]:
    missing: list[str] = []
    if not source_url:
        missing.append("source_url")
    if not extracted_at and not download_date:
        missing.append("extracted_at_or_download_date")
    return missing


def build_provenance(path: Path, raw_dir: Path) -> Provenance:
    relative = path.relative_to(raw_dir).as_posix()
    sidecar_fields, sidecar_path = _load_sidecar(path, relative)
    source_url = _clean_str(sidecar_fields.get("source_url"))
    extracted_at = _clean_str(sidecar_fields.get("extracted_at"))
    download_date = _clean_str(sidecar_fields.get("download_date"))
    publisher = _clean_str(sidecar_fields.get("publisher"))
    notes = _clean_str(sidecar_fields.get("notes"))
    return Provenance(
        original_filename=path.name,
        relative_path=relative,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
        file_mtime_iso=_mtime_iso(path),
        source_url=source_url,
        extracted_at=extracted_at,
        download_date=download_date,
        publisher=publisher,
        notes=notes,
        sidecar_path=sidecar_path.as_posix() if sidecar_path else None,
        missing_fields=_missing_provenance_fields(source_url, extracted_at, download_date),
    )


def _clean_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def discover_raw_files(raw_dir: Path) -> tuple[list[Path], list[str]]:
    """Return (tabular files, skipped names). Never modifies files."""
    skipped: list[str] = []
    found: list[Path] = []
    if not raw_dir.exists():
        return [], [f"missing directory: {raw_dir}"]
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in SKIP_FILENAMES:
            skipped.append(path.name)
            continue
        if name.endswith(".provenance.json") or name in PROVENANCE_FILENAMES:
            skipped.append(path.name)
            continue
        if path.suffix.lower() in TABULAR_SUFFIXES:
            found.append(path)
        else:
            skipped.append(path.name)
    return found, skipped
