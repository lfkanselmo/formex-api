from io import BytesIO

from openpyxl import Workbook
from src.infrastructure.parsing.openpyxl_row_parser import OpenpyxlRowParser


def _build_workbook_bytes(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_parse_returns_one_dict_per_data_row() -> None:
    content = _build_workbook_bytes(
        [
            ["arrendatario", "fecha_inicio", "canon_mensual"],
            ["Maria Gonzalez", "2026-09-01", "1500000"],
            ["Juan Perez", "2026-09-15", "1200000"],
        ]
    )

    rows = OpenpyxlRowParser().parse(content)

    assert rows == [
        {
            "arrendatario": "Maria Gonzalez",
            "fecha_inicio": "2026-09-01",
            "canon_mensual": "1500000",
        },
        {"arrendatario": "Juan Perez", "fecha_inicio": "2026-09-15", "canon_mensual": "1200000"},
    ]


def test_parse_skips_fully_empty_rows() -> None:
    content = _build_workbook_bytes([["arrendatario"], ["Maria"], [None], ["Juan"]])

    rows = OpenpyxlRowParser().parse(content)

    assert rows == [{"arrendatario": "Maria"}, {"arrendatario": "Juan"}]


def test_parse_returns_empty_list_when_only_header_present() -> None:
    content = _build_workbook_bytes([["arrendatario", "fecha_inicio"]])

    rows = OpenpyxlRowParser().parse(content)

    assert rows == []
