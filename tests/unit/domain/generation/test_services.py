from datetime import datetime
from uuid import uuid4

from src.domain.generation.models import Template
from src.domain.generation.services import BatchRowValidator


def _now() -> datetime:
    return datetime(2026, 8, 11, 12, 0, 0)


def _build_template() -> Template:
    return Template.create(
        organization_id=uuid4(),
        name="Contrato_Arrendamiento_v3.docx",
        storage_key="templates/contrato.docx",
        placeholders=["arrendatario", "fecha_inicio", "canon_mensual"],
        created_at=_now(),
    )


def test_validate_separates_valid_and_invalid_rows() -> None:
    template = _build_template()
    complete_row = {
        "arrendatario": "Maria Gonzalez",
        "fecha_inicio": "2026-09-01",
        "canon_mensual": "1500000",
    }
    incomplete_row = {"arrendatario": "Juan Perez", "fecha_inicio": "2026-09-15"}
    validator = BatchRowValidator()

    result = validator.validate(template, [complete_row, incomplete_row])

    assert result.valid_rows == (complete_row,)
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 2
    assert "canon_mensual" in result.errors[0].reason


def test_validate_accepts_rows_with_extra_columns() -> None:
    template = _build_template()
    row = {
        "arrendatario": "Maria Gonzalez",
        "fecha_inicio": "2026-09-01",
        "canon_mensual": "1500000",
        "observaciones": "ninguna",
    }
    validator = BatchRowValidator()

    result = validator.validate(template, [row])

    assert result.valid_rows == (row,)
    assert result.errors == ()


def test_validate_returns_empty_result_for_no_rows() -> None:
    template = _build_template()
    validator = BatchRowValidator()

    result = validator.validate(template, [])

    assert result.valid_rows == ()
    assert result.errors == ()
