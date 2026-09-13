"""Deterministic labelled-field extraction from machine-readable PDF text.

No OCR. No LLM. Missing values stay unavailable. Measurements are not inferred.
"""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from typing import Any

from app.engines.document.constants import (
    EXTRACT_FIELD_NAMES,
    EXTRACTION_EXTRACTED,
    EXTRACTION_INCONCLUSIVE,
    METHOD_OCR_NOT_AVAILABLE,
    METHOD_PDF_TEXT,
    METHOD_REGEX,
    METHOD_UNAVAILABLE,
    MISSING_BUDGET_REASON,
    NO_INFER_REASON,
    OCR_NOT_AVAILABLE,
    OCR_REASON,
    SCANNED_REASON,
)
from app.engines.document.types import ExtractedField, MilestoneItem, QuantityItem

_MIN_TEXT_CHARS = 12

_AMOUNT_UNIT = r"(?:rs\.?|inr|₹)?"
_NUM = r"([\d]{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)"

_LABELED_TEXT = {
    "work_name": re.compile(
        r"(?:project|work)\s*(?:name|title)\s*[:\-]\s*(.+)$",
        re.IGNORECASE,
    ),
    "scope_description": re.compile(
        r"(?:scope|description)\s*[:\-]\s*(.+)$",
        re.IGNORECASE,
    ),
    "agency_text": re.compile(
        r"(?:agency|contractor|implementing\s+agency)\s*[:\-]\s*(.+)$",
        re.IGNORECASE,
    ),
    "reference_number": re.compile(
        r"(?:ref(?:erence)?(?:\s*(?:no\.?|number))?|document\s*(?:no\.?|number))\s*[:\-]\s*(\S.+)$",
        re.IGNORECASE,
    ),
}

_AREA = re.compile(
    rf"(?:area|carpet\s+area|built[- ]?up\s+area)\s*[:\-]?\s*{_NUM}\s*(sq\.?\s*ft|sqft|square\s*feet|sq\.?\s*m|sqm)?",
    re.IGNORECASE,
)
_AREA_UNIT_ONLY = re.compile(
    rf"{_NUM}\s*(sq\.?\s*ft|sqft|square\s*feet)\b",
    re.IGNORECASE,
)
_LENGTH = re.compile(rf"(?:^|\b)length\s*[:\-]\s*{_NUM}\s*([a-z.\s]+)?$", re.IGNORECASE)
_WIDTH = re.compile(rf"(?:^|\b)width\s*[:\-]\s*{_NUM}\s*([a-z.\s]+)?$", re.IGNORECASE)
_HEIGHT = re.compile(rf"(?:^|\b)height\s*[:\-]\s*{_NUM}\s*([a-z.\s]+)?$", re.IGNORECASE)
_VOLUME = re.compile(
    rf"(?:^|\b)volume\s*[:\-]\s*{_NUM}\s*(cum|cu\.?\s*m|m3|m\^3)?",
    re.IGNORECASE,
)
_FLOORS = re.compile(r"(?:^|\b)floors?\s*[:\-]\s*(\d+)\b", re.IGNORECASE)

_ESTIMATE = re.compile(
    rf"(?:estimate|budget|sanctioned\s+amount|allocation|estimated\s+cost)\s*[:\-]?\s*{_AMOUNT_UNIT}\s*{_NUM}\s*(lakh|lakhs|rupees|inr)?",
    re.IGNORECASE,
)
_TOTAL = re.compile(
    rf"(?:grand\s+total|total\s+amount|total)\s*[:\-]?\s*{_AMOUNT_UNIT}\s*{_NUM}\s*(lakh|lakhs)?",
    re.IGNORECASE,
)
_ITEM_AMOUNT = re.compile(
    rf"(?:item\s+amount|rate\s+amount)\s*[:\-]?\s*{_AMOUNT_UNIT}\s*{_NUM}",
    re.IGNORECASE,
)

_DATE_ISO = r"(\d{4}-\d{2}-\d{2})"
_DATE_DMY = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
_PLANNED_START = re.compile(
    rf"(?:planned\s+start(?:\s+date)?|start\s+date)\s*[:\-]\s*(?:{_DATE_ISO}|{_DATE_DMY})",
    re.IGNORECASE,
)
_PLANNED_END = re.compile(
    rf"(?:planned\s+completion(?:\s+date)?|completion\s+date|date\s+of\s+completion)\s*[:\-]\s*(?:{_DATE_ISO}|{_DATE_DMY})",
    re.IGNORECASE,
)

_MILESTONE = re.compile(
    rf"milestone\s*[:\-]?\s*(M?\d+|[A-Za-z][\w ]{{0,40}}?)\s*(?:amount)?\s*[:\-]?\s*{_AMOUNT_UNIT}\s*{_NUM}(?:\s*(?:target|date)\s*[:\-]?\s*(?:{_DATE_ISO}|{_DATE_DMY}))?",
    re.IGNORECASE,
)
_QUANTITY_ITEM = re.compile(
    rf"(?:item)\s*[:\-]\s*(.+?)\s+quantity\s*[:\-]\s*{_NUM}\s+unit\s*[:\-]\s*([A-Za-z.]+)",
    re.IGNORECASE,
)

_OFFICIAL_MARKERS = re.compile(
    r"\b(government of india|ministry of statistics|official mplads sanction|gazette of india)\b",
    re.IGNORECASE,
)


def parse_number(text: str) -> float | None:
    cleaned = text.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value.is_integer():
        return float(int(value))
    return value


def money_value(number: float, unit: str | None) -> tuple[float, str | None]:
    unit_norm = (unit or "").casefold().strip()
    if unit_norm in {"lakh", "lakhs"}:
        return number * 100_000.0, "INR"
    if unit_norm in {"rupees", "inr", "rs", "rs."}:
        return number, "INR"
    return number, "INR" if unit_norm == "" else unit


def normalize_area_unit(unit: str | None) -> str | None:
    if not unit:
        return "sq.ft"
    text = unit.casefold().replace(" ", "")
    if text in {"sq.ft", "sqft", "squarefeet", "sq.feet"}:
        return "sq.ft"
    if text in {"sq.m", "sqm", "sq.metre", "sq.meter"}:
        return "sq.m"
    return unit.strip()


def _clean_line(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split()).strip()


def normalize_extracted_text(text: str) -> str:
    return " ".join(text.casefold().split())


def text_digest(text: str) -> str:
    return hashlib.sha256(normalize_extracted_text(text).encode("utf-8")).hexdigest()


def parse_date(raw: str) -> str | None:
    text = raw.strip()
    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
    if iso:
        return text
    parts = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", text)
    if not parts:
        return None
    first, second, year = int(parts.group(1)), int(parts.group(2)), int(parts.group(3))
    if year < 100:
        year += 2000
    if first > 12 and second <= 12:
        day, month = first, second
    elif second > 12 and first <= 12:
        day, month = second, first
    else:
        return None
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _unavailable(name: str, reason: str, method: str = METHOD_UNAVAILABLE) -> ExtractedField:
    return ExtractedField(
        name=name,
        available=False,
        extraction_method=method,
        unavailable_reason=reason,
    )


def _field(
    name: str,
    value: Any,
    *,
    unit: str | None,
    confidence: float,
    method: str,
    page: int,
) -> ExtractedField:
    return ExtractedField(
        name=name,
        value=value,
        unit=unit,
        confidence=round(confidence, 4),
        extraction_method=method,
        source_location=f"page {page}",
        available=True,
    )


def _pick_unique(matches: list[tuple[Any, str | None, int]]) -> tuple[Any, str | None, int] | None:
    if not matches:
        return None
    values = {(item[0], item[1]) for item in matches}
    if len(values) > 1:
        return None
    return matches[0]


def extract_pdf_pages(payload: bytes) -> tuple[list[tuple[int, str]], str | None]:
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover - exercised when dependency missing
        return [], "pypdf is not installed; PDF text extraction is unavailable."
    try:
        reader = PdfReader(BytesIO(payload))
    except Exception:
        return [], "The PDF could not be opened for text extraction."
    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception:
            return [], "The PDF is encrypted and could not be read."
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append((index, text))
    return pages, None


def parse_labelled_fields(pages: list[tuple[int, str]]) -> tuple[list[ExtractedField], list[QuantityItem], list[MilestoneItem], list[str]]:
    notes: list[str] = []
    collected: dict[str, list[tuple[Any, str | None, int]]] = {name: [] for name in EXTRACT_FIELD_NAMES}
    quantities: list[QuantityItem] = []
    milestones: list[MilestoneItem] = []

    for page, raw in pages:
        for original in raw.splitlines():
            line = _clean_line(original)
            if not line:
                continue
            if _OFFICIAL_MARKERS.search(line) and "TEST DATA" not in line.upper():
                notes.append(
                    "Official-looking wording was not treated as proof of authenticity."
                )
            for name, pattern in _LABELED_TEXT.items():
                match = pattern.search(line)
                if match:
                    value = _clean_line(match.group(1))
                    if value:
                        collected[name].append((value, None, page))
            area = _AREA.search(line)
            if area:
                number = parse_number(area.group(1))
                if number is not None:
                    collected["area"].append((number, normalize_area_unit(area.group(2)), page))
            elif "area" in line.casefold() and _AREA_UNIT_ONLY.search(line):
                only = _AREA_UNIT_ONLY.search(line)
                if only:
                    number = parse_number(only.group(1))
                    if number is not None:
                        collected["area"].append((number, normalize_area_unit(only.group(2)), page))
            for name, pattern in (("length", _LENGTH), ("width", _WIDTH), ("height", _HEIGHT), ("volume", _VOLUME)):
                match = pattern.search(line)
                if match:
                    number = parse_number(match.group(1))
                    unit = _clean_line(match.group(2) or "") or None
                    if number is not None:
                        collected[name].append((number, unit, page))
            floors = _FLOORS.search(line)
            if floors:
                collected["floors"].append((int(floors.group(1)), None, page))
            estimate = _ESTIMATE.search(line)
            if estimate:
                number = parse_number(estimate.group(1))
                if number is not None:
                    value, unit = money_value(number, estimate.group(2))
                    collected["estimate_amount"].append((value, unit, page))
            total = _TOTAL.search(line)
            if total and "milestone" not in line.casefold():
                number = parse_number(total.group(1))
                if number is not None:
                    value, unit = money_value(number, total.group(2))
                    collected["total_amount"].append((value, unit, page))
            item_amount = _ITEM_AMOUNT.search(line)
            if item_amount:
                number = parse_number(item_amount.group(1))
                if number is not None:
                    collected["item_amount"].append((number, "INR", page))
            start = _PLANNED_START.search(line)
            if start:
                raw_date = next((part for part in start.groups() if part), None)
                parsed = parse_date(raw_date) if raw_date else None
                if parsed:
                    collected["planned_start"].append((parsed, None, page))
            end = _PLANNED_END.search(line)
            if end:
                raw_date = next((part for part in end.groups() if part), None)
                parsed = parse_date(raw_date) if raw_date else None
                if parsed:
                    collected["planned_completion"].append((parsed, None, page))
            milestone = _MILESTONE.search(line)
            if milestone:
                amount = parse_number(milestone.group(2))
                date_raw = next((part for part in milestone.groups()[2:] if part), None)
                target = parse_date(date_raw) if date_raw else None
                milestones.append(
                    MilestoneItem(
                        milestone=_clean_line(milestone.group(1)),
                        amount=amount,
                        target_date=target,
                        confidence=0.86,
                        source_location=f"page {page}",
                    )
                )
            qty = _QUANTITY_ITEM.search(line)
            if qty:
                number = parse_number(qty.group(2))
                if number is not None:
                    quantities.append(
                        QuantityItem(
                            item=_clean_line(qty.group(1)),
                            quantity=number,
                            unit=_clean_line(qty.group(3)),
                            confidence=0.88,
                            source_location=f"page {page}",
                        )
                    )

    fields: list[ExtractedField] = []
    for name in EXTRACT_FIELD_NAMES:
        picked = _pick_unique(collected[name])
        if picked is None and collected[name]:
            fields.append(
                _unavailable(
                    name,
                    "Multiple conflicting values were found in this document.",
                    METHOD_REGEX,
                )
            )
            continue
        if picked is None:
            reason = MISSING_BUDGET_REASON if name in {"estimate_amount", "total_amount"} else NO_INFER_REASON
            if name in {"area", "length", "width", "height", "volume", "floors"}:
                reason = NO_INFER_REASON
            fields.append(_unavailable(name, reason))
            continue
        value, unit, page = picked
        confidence = 0.94 if name in {"area", "estimate_amount", "work_name"} else 0.90
        fields.append(
            _field(
                name,
                value,
                unit=unit,
                confidence=confidence,
                method=METHOD_REGEX,
                page=page,
            )
        )
    return fields, quantities, milestones, notes


def extract_from_bytes(payload: bytes, mime_type: str) -> dict[str, Any]:
    """Return a serialisable extraction payload. Never invents values."""
    if mime_type != "application/pdf":
        return {
            "status": OCR_NOT_AVAILABLE,
            "extraction_method": METHOD_OCR_NOT_AVAILABLE,
            "pages": [],
            "combined_text": "",
            "raw_text_available": False,
            "page_count": None,
            "fields": [_unavailable(name, OCR_REASON, METHOD_OCR_NOT_AVAILABLE).as_dict() for name in EXTRACT_FIELD_NAMES],
            "quantities": [],
            "milestones": [],
            "notes": [OCR_REASON, SCANNED_REASON],
            "text_sha256": None,
        }
    pages, error = extract_pdf_pages(payload)
    combined = "\n".join(text for _page, text in pages)
    usable = normalize_extracted_text(combined)
    if error or len(usable) < _MIN_TEXT_CHARS:
        reason = error or SCANNED_REASON
        status = OCR_NOT_AVAILABLE if not usable else EXTRACTION_INCONCLUSIVE
        method = METHOD_OCR_NOT_AVAILABLE if not usable else METHOD_PDF_TEXT
        return {
            "status": status,
            "extraction_method": method,
            "pages": [{"page": page, "text_length": len(text)} for page, text in pages],
            "combined_text": combined,
            "raw_text_available": bool(usable),
            "page_count": len(pages) or None,
            "fields": [_unavailable(name, reason, method).as_dict() for name in EXTRACT_FIELD_NAMES],
            "quantities": [],
            "milestones": [],
            "notes": [reason],
            "text_sha256": text_digest(combined) if usable else None,
        }
    fields, quantities, milestones, notes = parse_labelled_fields(pages)
    available = [item for item in fields if item.available]
    status = EXTRACTION_EXTRACTED if available else EXTRACTION_INCONCLUSIVE
    if not available:
        notes.append("No labelled fields could be extracted from the machine-readable text.")
    return {
        "status": status,
        "extraction_method": METHOD_PDF_TEXT,
        "pages": [{"page": page, "text_length": len(text)} for page, text in pages],
        "combined_text": combined,
        "raw_text_available": True,
        "page_count": len(pages),
        "fields": [item.as_dict() for item in fields],
        "quantities": [item.as_dict() for item in quantities],
        "milestones": [item.as_dict() for item in milestones],
        "notes": notes,
        "text_sha256": text_digest(combined),
    }
