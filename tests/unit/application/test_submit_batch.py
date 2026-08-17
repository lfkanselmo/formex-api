from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.use_cases.submit_batch import SubmitBatchUseCase
from src.domain.generation.exceptions import InvalidExcelFileError, TemplateNotFoundError
from src.domain.generation.models import (
    BatchStatus,
    DocumentStatus,
    GeneratedDocument,
    GenerationBatch,
    Template,
)


def _now() -> datetime:
    return datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def _build_template(organization_id: UUID) -> Template:
    return Template.create(
        organization_id=organization_id,
        name="Contrato_Arrendamiento_v3.docx",
        storage_key="templates/contrato.docx",
        placeholders=["arrendatario", "canon_mensual"],
        created_at=_now(),
    )


class FakeTemplateRepository:
    def __init__(self, template: Template | None = None) -> None:
        self._template = template

    async def add(self, template: Template) -> None:
        raise NotImplementedError

    async def get_by_id(self, template_id: UUID, organization_id: UUID) -> Template | None:
        if self._template and self._template.id == template_id:
            return self._template
        return None

    async def list_all(self, organization_id: UUID) -> list[Template]:
        raise NotImplementedError


class FakeBatchRepository:
    def __init__(self) -> None:
        self.added_batch: GenerationBatch | None = None
        self.added_documents: list[GeneratedDocument] = []

    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        self.added_batch = batch
        self.added_documents = documents

    async def get_by_id(self, batch_id: UUID, organization_id: UUID) -> GenerationBatch | None:
        raise NotImplementedError

    async def list_all(self, organization_id: UUID) -> list[GenerationBatch]:
        raise NotImplementedError

    async def update(self, batch: GenerationBatch) -> None:
        raise NotImplementedError

    async def get_document(
        self, batch_id: UUID, row_index: int, organization_id: UUID
    ) -> GeneratedDocument | None:
        raise NotImplementedError

    async def list_documents(
        self, batch_id: UUID, organization_id: UUID
    ) -> list[GeneratedDocument]:
        raise NotImplementedError

    async def update_document(self, document: GeneratedDocument) -> None:
        raise NotImplementedError


class FakeExcelRowParser:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self._rows = rows

    def parse(self, content: bytes) -> list[dict[str, str]]:
        return self._rows


class FailingExcelRowParser:
    def parse(self, content: bytes) -> list[dict[str, str]]:
        raise ValueError("File is not a zip file")


class FakeDispatcher:
    def __init__(self) -> None:
        self.dispatched: tuple[UUID, UUID, list[int]] | None = None

    def dispatch(self, organization_id: UUID, batch_id: UUID, row_indices: list[int]) -> None:
        self.dispatched = (organization_id, batch_id, row_indices)


async def test_execute_raises_when_template_missing() -> None:
    use_case = SubmitBatchUseCase(
        FakeTemplateRepository(), FakeBatchRepository(), FakeExcelRowParser([]), FakeDispatcher()
    )

    with pytest.raises(TemplateNotFoundError):
        await use_case.execute(uuid4(), uuid4(), b"excel-content")


async def test_execute_dispatches_all_valid_rows() -> None:
    organization_id = uuid4()
    template = _build_template(organization_id)
    rows = [
        {"arrendatario": "Maria Gonzalez", "canon_mensual": "1500000"},
        {"arrendatario": "Juan Perez", "canon_mensual": "1200000"},
    ]
    batches = FakeBatchRepository()
    dispatcher = FakeDispatcher()
    use_case = SubmitBatchUseCase(
        FakeTemplateRepository(template), batches, FakeExcelRowParser(rows), dispatcher
    )

    batch = await use_case.execute(organization_id, template.id, b"excel-content")

    assert batch.total_rows == 2
    assert batch.failed_rows == 0
    assert batches.added_documents[0].status is DocumentStatus.PENDING
    assert batches.added_documents[1].status is DocumentStatus.PENDING
    assert dispatcher.dispatched == (organization_id, batch.id, [0, 1])


async def test_execute_marks_invalid_rows_failed_and_skips_dispatching_them() -> None:
    organization_id = uuid4()
    template = _build_template(organization_id)
    rows = [
        {"arrendatario": "Maria Gonzalez", "canon_mensual": "1500000"},
        {"arrendatario": "Juan Perez"},
    ]
    batches = FakeBatchRepository()
    dispatcher = FakeDispatcher()
    use_case = SubmitBatchUseCase(
        FakeTemplateRepository(template), batches, FakeExcelRowParser(rows), dispatcher
    )

    batch = await use_case.execute(organization_id, template.id, b"excel-content")

    assert batch.total_rows == 2
    assert batch.failed_rows == 1
    assert batch.status is BatchStatus.PROCESSING
    assert batches.added_documents[0].status is DocumentStatus.PENDING
    assert batches.added_documents[1].status is DocumentStatus.FAILED
    assert "canon_mensual" in (batches.added_documents[1].error_message or "")
    assert dispatcher.dispatched == (organization_id, batch.id, [0])


async def test_execute_does_not_dispatch_when_every_row_is_invalid() -> None:
    organization_id = uuid4()
    template = _build_template(organization_id)
    rows = [{"arrendatario": "Maria Gonzalez"}]
    batches = FakeBatchRepository()
    dispatcher = FakeDispatcher()
    use_case = SubmitBatchUseCase(
        FakeTemplateRepository(template), batches, FakeExcelRowParser(rows), dispatcher
    )

    batch = await use_case.execute(organization_id, template.id, b"excel-content")

    assert batch.status is BatchStatus.FAILED
    assert dispatcher.dispatched is None


async def test_execute_raises_invalid_excel_file_when_parser_rejects_it() -> None:
    organization_id = uuid4()
    template = _build_template(organization_id)
    use_case = SubmitBatchUseCase(
        FakeTemplateRepository(template),
        FakeBatchRepository(),
        FailingExcelRowParser(),
        FakeDispatcher(),
    )

    with pytest.raises(InvalidExcelFileError):
        await use_case.execute(organization_id, template.id, b"contenido-invalido")
