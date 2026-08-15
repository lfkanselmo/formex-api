from datetime import datetime
from uuid import uuid4

import pytest
from src.domain.generation.exceptions import MissingPlaceholdersError
from src.domain.generation.models import (
    BatchStatus,
    DocumentStatus,
    GeneratedDocument,
    GenerationBatch,
    Template,
)


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


def _build_batch(total_rows: int = 4) -> GenerationBatch:
    return GenerationBatch.create(
        organization_id=uuid4(),
        template_id=uuid4(),
        total_rows=total_rows,
        created_at=_now(),
    )


def _build_document() -> GeneratedDocument:
    return GeneratedDocument.create(
        batch_id=uuid4(),
        row_index=0,
        row_data={"arrendatario": "Maria Gonzalez"},
    )


def test_template_create_stores_placeholders_as_tuple() -> None:
    template = _build_template()
    assert template.placeholders == ("arrendatario", "fecha_inicio", "canon_mensual")


def test_missing_placeholders_detects_gap() -> None:
    template = _build_template()
    missing = template.missing_placeholders(["arrendatario", "fecha_inicio"])
    assert missing == frozenset({"canon_mensual"})


def test_missing_placeholders_empty_when_covered() -> None:
    template = _build_template()
    missing = template.missing_placeholders(
        ["arrendatario", "fecha_inicio", "canon_mensual", "extra"]
    )
    assert missing == frozenset()


def test_ensure_columns_cover_placeholders_raises_when_missing() -> None:
    template = _build_template()
    with pytest.raises(MissingPlaceholdersError):
        template.ensure_columns_cover_placeholders(["arrendatario"])


def test_ensure_columns_cover_placeholders_passes_when_covered() -> None:
    template = _build_template()
    template.ensure_columns_cover_placeholders(["arrendatario", "fecha_inicio", "canon_mensual"])


def test_missing_values_detects_blank_cell() -> None:
    template = _build_template()
    row = {"arrendatario": "Maria Gonzalez", "fecha_inicio": "2026-09-01", "canon_mensual": ""}

    assert template.missing_values(row) == frozenset({"canon_mensual"})


def test_missing_values_detects_absent_key_as_blank() -> None:
    template = _build_template()
    row = {"arrendatario": "Maria Gonzalez", "fecha_inicio": "2026-09-01"}

    assert template.missing_values(row) == frozenset({"canon_mensual"})


def test_missing_values_empty_when_every_placeholder_has_a_value() -> None:
    template = _build_template()
    row = {
        "arrendatario": "Maria Gonzalez",
        "fecha_inicio": "2026-09-01",
        "canon_mensual": "1500000",
    }

    assert template.missing_values(row) == frozenset()


def test_batch_create_starts_pending() -> None:
    batch = _build_batch()
    assert batch.status is BatchStatus.PENDING
    assert batch.completed_rows == 0
    assert batch.failed_rows == 0


def test_batch_with_progress_stays_pending_without_processed_rows() -> None:
    batch = _build_batch()
    updated = batch.with_progress(completed_rows=0, failed_rows=0)
    assert updated.status is BatchStatus.PENDING


def test_batch_with_progress_is_processing_while_incomplete() -> None:
    batch = _build_batch(total_rows=4)
    updated = batch.with_progress(completed_rows=2, failed_rows=0)
    assert updated.status is BatchStatus.PROCESSING
    assert updated.completed_at is None


def test_batch_with_progress_completes_without_failures() -> None:
    batch = _build_batch(total_rows=4)
    updated = batch.with_progress(completed_rows=4, failed_rows=0, completed_at=_now())
    assert updated.status is BatchStatus.COMPLETED
    assert updated.completed_at == _now()


def test_batch_with_progress_fails_when_all_rows_fail() -> None:
    batch = _build_batch(total_rows=4)
    updated = batch.with_progress(completed_rows=0, failed_rows=4)
    assert updated.status is BatchStatus.FAILED


def test_batch_with_progress_completes_with_errors() -> None:
    batch = _build_batch(total_rows=4)
    updated = batch.with_progress(completed_rows=3, failed_rows=1)
    assert updated.status is BatchStatus.COMPLETED_WITH_ERRORS


def test_document_create_starts_pending() -> None:
    document = _build_document()
    assert document.status is DocumentStatus.PENDING
    assert document.output_key is None


def test_document_mark_processing() -> None:
    document = _build_document().mark_processing()
    assert document.status is DocumentStatus.PROCESSING


def test_document_mark_completed_sets_output_key() -> None:
    document = _build_document().mark_completed("batches/1/0.pdf")
    assert document.status is DocumentStatus.COMPLETED
    assert document.output_key == "batches/1/0.pdf"
    assert document.error_message is None


def test_document_mark_failed_sets_error_message() -> None:
    document = _build_document().mark_failed("Fila inválida: falta canon_mensual")
    assert document.status is DocumentStatus.FAILED
    assert document.error_message == "Fila inválida: falta canon_mensual"
