from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def _score_header_row(values: list[object]) -> float:
    texts = [str(v).strip() if v is not None and not (isinstance(v, float) and pd.isna(v)) else "" for v in values]
    non_empty = [t for t in texts if t and t.lower() not in {"nan", "none"}]
    if not non_empty:
        return -1.0
    unique_ratio = len(set(non_empty)) / len(non_empty)
    unnamed = sum(1 for t in non_empty if t.lower().startswith("unnamed"))
    numericish = 0
    for t in non_empty:
        try:
            float(str(t).replace(",", ""))
            numericish += 1
        except ValueError:
            pass
    numeric_penalty = numericish / max(len(non_empty), 1)
    return len(non_empty) + unique_ratio * 5 - unnamed * 3 - numeric_penalty * 8


def detect_header_row(preview: pd.DataFrame, max_scan: int = 12) -> int:
    best_i = 0
    best_score = -1e9
    scan = min(max_scan, len(preview))
    for i in range(scan):
        score = _score_header_row(list(preview.iloc[i].values))
        if score > best_score:
            best_score = score
            best_i = i
    return best_i


def detect_csv_delimiter(sample: str) -> str:
    """Sniff comma/semicolon/tab from a text sample. Does not alter the file."""
    if not sample.strip():
        return ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        if dialect.delimiter in {",", ";", "\t", "|"}:
            return dialect.delimiter
    except csv.Error:
        pass
    first = next((line for line in sample.splitlines() if line.strip()), "")
    counts = {",": first.count(","), ";": first.count(";"), "\t": first.count("\t")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _read_csv_rows(path: Path, sep: str, encoding: str) -> list[list[str]]:
    with path.open("r", encoding=encoding, newline="") as handle:
        return list(csv.reader(handle, delimiter=sep))


def _frame_from_rows(rows: list[list[str]], header_i: int) -> pd.DataFrame:
    header_vals = rows[header_i] if header_i < len(rows) else []
    width = max((len(row) for row in rows[header_i:]), default=0)
    columns = [_clean_column_name(header_vals[i] if i < len(header_vals) else "", i) for i in range(width)]
    body = rows[header_i + 1 :]
    padded = [row + [""] * (width - len(row)) for row in body]
    if not padded:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(padded, columns=columns)


def _read_csv(path: Path, sep: str | None = None) -> tuple[pd.DataFrame, int, list[str]]:
    notes: list[str] = []
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            sample = path.read_text(encoding=encoding, errors="strict")[:32768]
            detected = sep if sep is not None else detect_csv_delimiter(sample)
            rows = _read_csv_rows(path, detected, encoding)
            if not rows:
                return pd.DataFrame(), 0, ["file has no rows"]
            preview = pd.DataFrame(rows[:15])
            header_i = detect_header_row(preview)
            frame = _frame_from_rows(rows, header_i)
            if encoding not in {"utf-8-sig", "utf-8"}:
                notes.append(f"read with encoding={encoding}")
            if sep is None and detected != ",":
                notes.append(f"delimiter detected as {detected!r}")
            if header_i != 0:
                notes.append(f"header detected at row index {header_i} (0-based in file preview)")
            return frame, header_i, notes
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    raise OSError(f"Could not decode {path.name}: {last_error}")


def _clean_column_name(name: object, index: int) -> str:
    text = str(name).strip() if name is not None else ""
    if not text or text.lower().startswith("unnamed"):
        return f"Unnamed:{index}"
    return text


def load_tabular(path: Path) -> list[tuple[pd.DataFrame, str | None, int, list[str]]]:
    """Return list of (frame, sheet_name, header_row_index, notes). All cells as strings."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame, header_i, notes = _read_csv(path)
        return [(frame, None, header_i, notes)]
    if suffix == ".tsv":
        frame, header_i, notes = _read_csv(path, sep="\t")
        return [(frame, None, header_i, notes)]
    if suffix in {".xlsx", ".xls"}:
        engine = "openpyxl" if suffix == ".xlsx" else None
        try:
            sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str, engine=engine)
        except ImportError as exc:
            raise OSError(f"Excel support missing for {path.name}: {exc}") from exc
        results = []
        for sheet_name, preview in sheets.items():
            if preview.empty:
                results.append((pd.DataFrame(), str(sheet_name), 0, ["empty sheet"]))
                continue
            header_i = detect_header_row(preview)
            header = [_clean_column_name(c, i) for i, c in enumerate(preview.iloc[header_i].tolist())]
            body = preview.iloc[header_i + 1 :].copy()
            body.columns = header
            body = body.reset_index(drop=True)
            notes = []
            if header_i != 0:
                notes.append(f"header detected at row index {header_i} on sheet {sheet_name}")
            results.append((body, str(sheet_name), header_i, notes))
        return results
    if suffix == ".json":
        payload = pd.read_json(path, dtype=str)
        if isinstance(payload, pd.Series):
            payload = payload.to_frame()
        payload.columns = [_clean_column_name(c, i) for i, c in enumerate(payload.columns)]
        return [(payload.astype(str), None, 0, [])]
    if suffix == ".parquet":
        frame = pd.read_parquet(path)
        frame = frame.astype(str)
        frame.columns = [_clean_column_name(c, i) for i, c in enumerate(frame.columns)]
        return [(frame, None, 0, [])]
    raise OSError(f"Unsupported suffix: {suffix}")
