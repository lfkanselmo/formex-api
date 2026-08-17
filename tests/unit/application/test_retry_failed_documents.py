from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.use_cases.retry_failed_documents import RetryFailedDocumentsUseCase
from src.domain.generation.exceptions import BatchNotFoundError
from src.domain.generation.models import DocumentStatus, GeneratedDocument, GenerationBatch


def _now() -> datetime:
    return datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)


class FakeBatchRepository:
    def __init__(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        self._batch = batch
        self._documents = {d.row_index: d for d in documents}
        self.updated_batches: list[GenerationBatch] = []
        self.updated_documents: list[GeneratedDocument] = []

    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        raise NotImplementedError

    async def get_by_id(self, batch_id: UUID, organization_id: UUID) -> GenerationBatch | None:
        if batch_id == self._batch.id and organization_id == self._batch.organization_id:
            return self._batch
        return None

    async def list_all(self, organization_id: UUID) -> list[GenerationBatch]:
        raise NotImplementedError

    async def update(self, batch: GenerationBatch) -> None:
        self._batch = batch
        self.updated_batches.append(batch)

    async def get_document(
        self, batch_id: UUID, row_index: int, organization_id: UUID
    ) -> GeneratedDocument | None:
        raise NotImplementedError

    async def list_documents(
        self, batch_id: UUID, organization_id: UUID
    ) -> list[GeneratedDocument]:
        return list(self._documents.values())

    async def update_document(self, document: GeneratedDocument, organization_id: UUID) -> None:
        self._documents[document.row_index] = document
        self.updated_documents.append(document)


class FakeDispatcher:
    def __init__(self) -> None:
        self.dispatched: tuple[UUID, UUID, list[int]] | None = None

    def dispatch(self, organization_id: UUID, batch_id: UUID, row_indices: list[int]) -> None:
        self.dispatched = (organization_id, batch_id, row_indices)


def _build_batch(organization_id: UUID) -> GenerationBatch:
    return GenerationBatch.create(
        organization_id=organization_id, template_id=uuid4(), total_rows=3, created_at=_now()
    )


async def test_execute_raises_when_batch_missing() -> None:
    use_case = RetryFailedDocumentsUseCase(
        FakeBatchRepository(_build_batch(uuid4()), []), FakeDispatcher()
    )

    with pytest.raises(BatchNotFoundError):
        await use_case.execute(uuid4(), uuid4())


async def test_execute_resets_failed_documents_and_dispatches_them() -> None:
    organization_id = uuid4()
    batch = _build_batch(organization_id).with_progress(completed_rows=1, failed_rows=2)
    documents = [
        GeneratedDocument.create(batch.id, 0, {}).mark_completed("batches/x/0.pdf"),
        GeneratedDocument.create(batch.id, 1, {}).mark_failed("Fila inválida"),
        GeneratedDocument.create(batch.id, 2, {}).mark_failed("Gotenberg no respondió"),
    ]
    batches = FakeBatchRepository(batch, documents)
    dispatcher = FakeDispatcher()
    use_case = RetryFailedDocumentsUseCase(batches, dispatcher)

    updated = await use_case.execute(organization_id, batch.id)

    assert updated.failed_rows == 0
    assert dispatcher.dispatched == (organization_id, batch.id, [1, 2])
    retried_1 = next(d for d in batches.updated_documents if d.row_index == 1)
    retried_2 = next(d for d in batches.updated_documents if d.row_index == 2)
    assert retried_1.status is DocumentStatus.PENDING
    assert retried_2.status is DocumentStatus.PENDING


async def test_execute_is_noop_when_no_documents_failed() -> None:
    organization_id = uuid4()
    batch = _build_batch(organization_id).with_progress(
        completed_rows=3, failed_rows=0, completed_at=_now()
    )
    documents = [
        GeneratedDocument.create(batch.id, i, {}).mark_completed(f"batches/x/{i}.pdf")
        for i in range(3)
    ]
    batches = FakeBatchRepository(batch, documents)
    dispatcher = FakeDispatcher()
    use_case = RetryFailedDocumentsUseCase(batches, dispatcher)

    updated = await use_case.execute(organization_id, batch.id)

    assert updated == batch
    assert dispatcher.dispatched is None
    assert batches.updated_documents == []
