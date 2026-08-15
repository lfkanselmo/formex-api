from __future__ import annotations

import zipfile
from io import BytesIO
from uuid import UUID

from src.application.ports.batch_repository import BatchRepositoryProtocol
from src.application.ports.document_storage import DocumentStorageProtocol
from src.domain.generation.exceptions import BatchNotFoundError
from src.domain.generation.models import DocumentStatus


class BuildBatchZipUseCase:
    def __init__(
        self,
        batch_repository: BatchRepositoryProtocol,
        storage: DocumentStorageProtocol,
    ) -> None:
        self._batches = batch_repository
        self._storage = storage

    async def execute(self, organization_id: UUID, batch_id: UUID) -> bytes:
        batch = await self._batches.get_by_id(batch_id, organization_id)
        if batch is None:
            raise BatchNotFoundError(batch_id)

        documents = await self._batches.list_documents(batch_id, organization_id)

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for document in documents:
                if document.status is not DocumentStatus.COMPLETED or document.output_key is None:
                    continue
                pdf_bytes = await self._storage.load(document.output_key)
                archive.writestr(f"documento_{document.row_index + 1:04d}.pdf", pdf_bytes)

        return buffer.getvalue()
