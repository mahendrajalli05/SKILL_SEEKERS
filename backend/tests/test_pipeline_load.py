from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.pipeline.load import detect_header_row, load_tabular


def test_detects_title_row_then_header(tmp_path: Path) -> None:
    path = tmp_path / "titled.csv"
    path.write_text(
        "MPLADS public extract\n"
        "State,District,Amount (Rs.)\n"
        "Andhra Pradesh,Guntur,1000\n",
        encoding="utf-8",
    )
    frames = load_tabular(path)
    frame, sheet, header_i, notes = frames[0]
    assert sheet is None
    assert header_i == 1
    assert list(frame.columns) == ["State", "District", "Amount (Rs.)"]
    assert len(frame) == 1
    assert any("header detected" in note for note in notes)


def test_detect_header_prefers_named_row() -> None:
    preview = pd.DataFrame(
        [
            ["Title only", None, None],
            ["State", "District", "Work Name"],
            ["Andhra Pradesh", "Guntur", "Road"],
        ]
    )
    assert detect_header_row(preview) == 1


def test_semicolon_delimited_csv(tmp_path: Path) -> None:
    path = tmp_path / "works.csv"
    path.write_text(
        '"MP NAME";"WORK";"STATE";"ALLOCATION AMOUNT"\n'
        '"Test MP";"Road";"Andhra Pradesh";"100000"\n',
        encoding="utf-8",
    )
    frame, _sheet, header_i, notes = load_tabular(path)[0]
    assert header_i == 0
    assert list(frame.columns) == ["MP NAME", "WORK", "STATE", "ALLOCATION AMOUNT"]
    assert frame.iloc[0]["STATE"] == "Andhra Pradesh"
    assert any("delimiter detected as ';'" in note for note in notes)
