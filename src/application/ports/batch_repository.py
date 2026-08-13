from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.domain.generation.models import GeneratedDocument, GenerationBatch


class BatchRepositoryProtocol(Protocol):
    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None: ...

    async def get_by_id(self, batch_id: UUID, organization_id: UUID) -> GenerationBatch | None: ...

    async def list_all(self, organization_id: UUID) -> list[GenerationBatch]: ...

    async def update(self, batch: GenerationBatch) -> None: ...

    async def get_document(
        self, batch_id: UUID, row_index: int, organization_id: UUID
    ) -> GeneratedDocument | None: ...

    async def list_documents(
        self, batch_id: UUID, organization_id: UUID
    ) -> list[GeneratedDocument]: ...

    async def update_document(self, document: GeneratedDocument) -> None: ...
