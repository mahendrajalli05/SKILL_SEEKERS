"""TEST-labelled PDF/image bytes. Not official government documents."""

from __future__ import annotations

from app.engines.document.constants import TEST_WATERMARK

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

JPEG_1X1 = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e"
    "121210131518281a181616183123251d283a333d3c3933383740485c4e404457453738"
    "506d51575f626768673e4d71797064785c656763ffc0000b080001000101011100ffc4"
    "001b000003010100000000000000000000000000000400010203ffc4001b10000203"
    "00000000000000000000000000000001020300ffda00080001001100003f00bf8000"
    "ffd9"
)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_text_pdf(lines: list[str], *, extra_pages: list[list[str]] | None = None) -> bytes:
    """Minimal TEXT PDF for tests. First line should keep the TEST watermark."""
    pages = [lines, *(extra_pages or [])]
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_obj_ids = [3 + i for i in range(len(pages))]
    content_obj_ids = [3 + len(pages) + i for i in range(len(pages))]
    font_obj_id = 3 + 2 * len(pages)
    kids = " ".join(f"{item} 0 R" for item in page_obj_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii"))
    contents: list[bytes] = []
    for index, page_lines in enumerate(pages):
        ops = ["BT", "/F1 11 Tf", "50 740 Td"]
        for i, line in enumerate(page_lines):
            if i:
                ops.append("0 -16 Td")
            ops.append(f"({_escape(line)}) Tj")
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1", errors="replace")
        contents.append(stream)
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_obj_ids[index]} 0 R "
                f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>"
            ).encode("ascii")
        )
    for stream in contents:
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        if not obj.endswith(b"\n"):
            out.extend(b"\n")
        out.extend(b"endobj\n")
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(out)


def consistent_blueprint_pdf() -> bytes:
    return make_text_pdf(
        [
            TEST_WATERMARK,
            "Work name: Community hall construction",
            "Area: 2000 sq.ft",
            "Estimate: Rs 2000000",
            "Agency: TEST implementing agency",
        ]
    )


def mismatch_blueprint_pdf() -> bytes:
    return make_text_pdf(
        [
            TEST_WATERMARK,
            "Work name: Community hall construction",
            "Area: 800 sq.ft",
            "Estimate: Rs 2000000",
        ]
    )


def boq_pdf() -> bytes:
    return make_text_pdf(
        [
            TEST_WATERMARK,
            "Work name: Community hall construction",
            "Item: Cement Quantity: 100 Unit: bags",
            "Milestone M1 amount 500000 target 2024-01-15",
            "Total amount: Rs 1950000",
            "Area: 1950 sq.ft",
        ]
    )


def missing_fields_pdf() -> bytes:
    return make_text_pdf(
        [
            TEST_WATERMARK,
            "This TEST progress note has no labelled dimensions or budget amount.",
        ]
    )


def empty_scanned_pdf() -> bytes:
    return make_text_pdf([""])
