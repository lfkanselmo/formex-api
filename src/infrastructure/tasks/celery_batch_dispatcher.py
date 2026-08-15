from __future__ import annotations

from uuid import UUID

from celery import chord, group

from src.infrastructure.tasks.jobs import finalize_batch_task, generate_document_task


class CeleryBatchDispatcher:
    def dispatch(self, organization_id: UUID, batch_id: UUID, row_indices: list[int]) -> None:
        header = group(
            generate_document_task.s(str(organization_id), str(batch_id), row_index)
            for row_index in row_indices
        )
        chord(header)(finalize_batch_task.s(str(organization_id), str(batch_id)))
