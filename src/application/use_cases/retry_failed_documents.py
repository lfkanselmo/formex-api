from __future__ import annotations

from uuid import UUID

from src.application.ports.batch_dispatcher import BatchDispatcherProtocol
from src.application.ports.batch_repository import BatchRepositoryProtocol
from src.domain.generation.exceptions import BatchNotFoundError
from src.domain.generation.models import DocumentStatus, GenerationBatch


class RetryFailedDocumentsUseCase:
    def __init__(
        self,
        batch_repository: BatchRepositoryProtocol,
        dispatcher: BatchDispatcherProtocol,
    ) -> None:
        self._batches = batch_repository
        self._dispatcher = dispatcher

    async def execute(self, organization_id: UUID, batch_id: UUID) -> GenerationBatch:
        batch = await self._batches.get_by_id(batch_id, organization_id)
        if batch is None:
            raise BatchNotFoundError(batch_id)

        documents = await self._batches.list_documents(batch_id, organization_id)
        failed_documents = [d for d in documents if d.status is DocumentStatus.FAILED]
        if not failed_documents:
            return batch

        retried_indices: list[int] = []
        for document in failed_documents:
            retried = document.retry()
            await self._batches.update_document(retried, organization_id)
            retried_indices.append(retried.row_index)

        updated_batch = batch.with_progress(
            completed_rows=batch.completed_rows,
            failed_rows=batch.failed_rows - len(failed_documents),
        )
        await self._batches.update(updated_batch)

        self._dispatcher.dispatch(organization_id, batch.id, retried_indices)
        return updated_batch
