from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.generation.models import GeneratedDocument, GenerationBatch


class BatchOut(BaseModel):
    id: UUID
    template_id: UUID
    status: str
    total_rows: int
    completed_rows: int
    failed_rows: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, batch: GenerationBatch) -> BatchOut:
        return cls(
            id=batch.id,
            template_id=batch.template_id,
            status=batch.status.value,
            total_rows=batch.total_rows,
            completed_rows=batch.completed_rows,
            failed_rows=batch.failed_rows,
            created_at=batch.created_at,
            completed_at=batch.completed_at,
        )


class DocumentOut(BaseModel):
    row_index: int
    status: str
    output_key: str | None
    error_message: str | None

    @classmethod
    def from_domain(cls, document: GeneratedDocument) -> DocumentOut:
        return cls(
            row_index=document.row_index,
            status=document.status.value,
            output_key=document.output_key,
            error_message=document.error_message,
        )
