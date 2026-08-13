from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.use_cases.generate_document import GenerateDocumentUseCase
from src.domain.generation.exceptions import (
    BatchNotFoundError,
    DocumentNotFoundError,
    TemplateNotFoundError,
)
from src.domain.generation.models import (
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
        placeholders=["arrendatario"],
        created_at=_now(),
    )


class FakeTemplateRepository:
    def __init__(self, templates: list[Template] | None = None) -> None:
        self._templates = {t.id: t for t in (templates or [])}

    async def add(self, template: Template) -> None:
        self._templates[template.id] = template

    async def get_by_id(self, template_id: UUID, organization_id: UUID) -> Template | None:
        template = self._templates.get(template_id)
        if template is None or template.organization_id != organization_id:
            return None
        return template

    async def list_all(self, organization_id: UUID) -> list[Template]:
        return [t for t in self._templates.values() if t.organization_id == organization_id]


class FakeBatchRepository:
    def __init__(
        self,
        batches: list[GenerationBatch] | None = None,
        documents: list[GeneratedDocument] | None = None,
    ) -> None:
        self._batches = {b.id: b for b in (batches or [])}
        self._documents = {(d.batch_id, d.row_index): d for d in (documents or [])}
        self.updated_documents: list[GeneratedDocument] = []

    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        self._batches[batch.id] = batch
        for document in documents:
            self._documents[(document.batch_id, document.row_index)] = document

    async def get_by_id(
        self, batch_id: UUID, organization_id: UUID
    ) -> GenerationBatch | None:
        batch = self._batches.get(batch_id)
        if batch is None or batch.organization_id != organization_id:
            return None
        return batch

    async def list_all(self, organization_id: UUID) -> list[GenerationBatch]:
        return [b for b in self._batches.values() if b.organization_id == organization_id]

    async def update(self, batch: GenerationBatch) -> None:
        self._batches[batch.id] = batch

    async def get_document(
        self, batch_id: UUID, row_index: int, organization_id: UUID
    ) -> GeneratedDocument | None:
        batch = await self.get_by_id(batch_id, organization_id)
        if batch is None:
            return None
        return self._documents.get((batch_id, row_index))

    async def list_documents(
        self, batch_id: UUID, organization_id: UUID
    ) -> list[GeneratedDocument]:
        return [d for (b, _), d in self._documents.items() if b == batch_id]

    async def update_document(self, document: GeneratedDocument) -> None:
        self._documents[(document.batch_id, document.row_index)] = document
        self.updated_documents.append(document)


class FakeRenderEngine:
    def render(self, template: bytes, context: dict[str, object]) -> bytes:
        return b"rendered:" + template


class FailingRenderEngine:
    def render(self, template: bytes, context: dict[str, object]) -> bytes:
        raise ValueError("Fila inválida: falta arrendatario")


class FakePdfConverter:
    async def convert(self, document: bytes) -> bytes:
        return b"pdf:" + document


class FakeDocumentStorage:
    def __init__(self, files: dict[str, bytes] | None = None) -> None:
        self.files = files or {}

    async def save(self, key: str, content: bytes) -> None:
        self.files[key] = content

    async def load(self, key: str) -> bytes:
        return self.files[key]


def _setup(
    render_engine: object = None,
) -> tuple[GenerateDocumentUseCase, UUID, UUID, FakeBatchRepository, FakeDocumentStorage]:
    organization_id = uuid4()
    template = _build_template(organization_id)
    batch = GenerationBatch.create(
        organization_id=organization_id,
        template_id=template.id,
        total_rows=1,
        created_at=_now(),
    )
    document = GeneratedDocument.create(
        batch_id=batch.id, row_index=0, row_data={"arrendatario": "Maria Gonzalez"}
    )
    templates = FakeTemplateRepository([template])
    batches = FakeBatchRepository([batch], [document])
    storage = FakeDocumentStorage({template.storage_key: b"plantilla original"})
    use_case = GenerateDocumentUseCase(
        template_repository=templates,
        batch_repository=batches,
        render_engine=render_engine or FakeRenderEngine(),
        pdf_converter=FakePdfConverter(),
        storage=storage,
    )
    return use_case, organization_id, batch.id, batches, storage


async def test_execute_marks_document_completed_and_stores_pdf() -> None:
    use_case, organization_id, batch_id, batches, storage = _setup()

    await use_case.execute(organization_id, batch_id, 0)

    final = batches.updated_documents[-1]
    assert final.status is DocumentStatus.COMPLETED
    assert final.output_key == f"batches/{batch_id}/0.pdf"
    assert storage.files[final.output_key] == b"pdf:rendered:plantilla original"


async def test_execute_marks_document_processing_before_completing() -> None:
    use_case, organization_id, batch_id, batches, _ = _setup()

    await use_case.execute(organization_id, batch_id, 0)

    assert batches.updated_documents[0].status is DocumentStatus.PROCESSING
    assert batches.updated_documents[-1].status is DocumentStatus.COMPLETED


async def test_execute_marks_document_failed_when_render_raises() -> None:
    use_case, organization_id, batch_id, batches, _ = _setup(render_engine=FailingRenderEngine())

    await use_case.execute(organization_id, batch_id, 0)

    final = batches.updated_documents[-1]
    assert final.status is DocumentStatus.FAILED
    assert final.error_message == "Fila inválida: falta arrendatario"


async def test_execute_raises_when_document_missing() -> None:
    use_case, organization_id, batch_id, _, _ = _setup()

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(organization_id, batch_id, 99)


async def test_execute_raises_when_batch_missing() -> None:
    use_case, organization_id, _, _, _ = _setup()

    with pytest.raises(BatchNotFoundError):
        await use_case.execute(organization_id, uuid4(), 0)


async def test_execute_raises_when_template_missing() -> None:
    organization_id = uuid4()
    batch = GenerationBatch.create(
        organization_id=organization_id,
        template_id=uuid4(),
        total_rows=1,
        created_at=_now(),
    )
    document = GeneratedDocument.create(batch_id=batch.id, row_index=0, row_data={})
    use_case = GenerateDocumentUseCase(
        template_repository=FakeTemplateRepository(),
        batch_repository=FakeBatchRepository([batch], [document]),
        render_engine=FakeRenderEngine(),
        pdf_converter=FakePdfConverter(),
        storage=FakeDocumentStorage(),
    )

    with pytest.raises(TemplateNotFoundError):
        await use_case.execute(organization_id, batch.id, 0)


async def test_execute_raises_when_batch_belongs_to_other_organization() -> None:
    use_case, _, batch_id, _, _ = _setup()

    with pytest.raises(BatchNotFoundError):
        await use_case.execute(uuid4(), batch_id, 0)
