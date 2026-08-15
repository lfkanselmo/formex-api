import zipfile
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from src.application.use_cases.build_batch_zip import BuildBatchZipUseCase
from src.domain.generation.exceptions import BatchNotFoundError
from src.domain.generation.models import GeneratedDocument, GenerationBatch


def _now() -> datetime:
    return datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)


class FakeBatchRepository:
    def __init__(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        self._batch = batch
        self._documents = documents

    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        raise NotImplementedError

    async def get_by_id(self, batch_id: UUID, organization_id: UUID) -> GenerationBatch | None:
        if batch_id == self._batch.id and organization_id == self._batch.organization_id:
            return self._batch
        return None

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
        return self._documents

    async def update_document(self, document: GeneratedDocument) -> None:
        raise NotImplementedError


class FakeDocumentStorage:
    def __init__(self, files: dict[str, bytes]) -> None:
        self._files = files

    async def save(self, key: str, content: bytes) -> None:
        raise NotImplementedError

    async def load(self, key: str) -> bytes:
        return self._files[key]


def _build_batch(organization_id: UUID) -> GenerationBatch:
    return GenerationBatch.create(
        organization_id=organization_id, template_id=uuid4(), total_rows=3, created_at=_now()
    )


async def test_execute_raises_when_batch_missing() -> None:
    use_case = BuildBatchZipUseCase(
        FakeBatchRepository(_build_batch(uuid4()), []), FakeDocumentStorage({})
    )

    with pytest.raises(BatchNotFoundError):
        await use_case.execute(uuid4(), uuid4())


async def test_execute_zips_only_completed_documents() -> None:
    organization_id = uuid4()
    batch = _build_batch(organization_id)
    documents = [
        GeneratedDocument.create(batch.id, 0, {}).mark_completed("batches/x/0.pdf"),
        GeneratedDocument.create(batch.id, 1, {}).mark_failed("Fila inválida"),
        GeneratedDocument.create(batch.id, 2, {}).mark_completed("batches/x/2.pdf"),
    ]
    storage = FakeDocumentStorage(
        {"batches/x/0.pdf": b"%PDF-primero", "batches/x/2.pdf": b"%PDF-tercero"}
    )
    use_case = BuildBatchZipUseCase(FakeBatchRepository(batch, documents), storage)

    zip_bytes = await use_case.execute(organization_id, batch.id)

    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        assert set(archive.namelist()) == {"documento_0001.pdf", "documento_0003.pdf"}
        assert archive.read("documento_0001.pdf") == b"%PDF-primero"
        assert archive.read("documento_0003.pdf") == b"%PDF-tercero"


async def test_execute_returns_empty_zip_when_nothing_completed() -> None:
    organization_id = uuid4()
    batch = _build_batch(organization_id)
    documents = [GeneratedDocument.create(batch.id, 0, {}).mark_failed("Fila inválida")]
    use_case = BuildBatchZipUseCase(FakeBatchRepository(batch, documents), FakeDocumentStorage({}))

    zip_bytes = await use_case.execute(organization_id, batch.id)

    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        assert archive.namelist() == []
