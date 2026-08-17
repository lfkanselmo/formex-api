from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.generation.models import (
    BatchStatus,
    DocumentStatus,
    GeneratedDocument,
    GenerationBatch,
)
from src.infrastructure.persistence.orm_models import GeneratedDocumentOrm, GenerationBatchOrm


class PostgresBatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, batch: GenerationBatch, documents: list[GeneratedDocument]) -> None:
        self._session.add(_batch_to_orm(batch))
        # generated_documents has a FK to generation_batches — flushing the
        # batch first guarantees insertion order regardless of how the unit
        # of work would otherwise batch these statements.
        await self._session.flush()
        for document in documents:
            self._session.add(_document_to_orm(document))
        await self._session.commit()

    async def get_by_id(self, batch_id: UUID, organization_id: UUID) -> GenerationBatch | None:
        row = (
            await self._session.execute(
                select(GenerationBatchOrm).where(
                    GenerationBatchOrm.id == batch_id,
                    GenerationBatchOrm.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        return _batch_to_domain(row) if row is not None else None

    async def list_all(self, organization_id: UUID) -> list[GenerationBatch]:
        rows = (
            (
                await self._session.execute(
                    select(GenerationBatchOrm)
                    .where(GenerationBatchOrm.organization_id == organization_id)
                    .order_by(GenerationBatchOrm.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [_batch_to_domain(row) for row in rows]

    async def update(self, batch: GenerationBatch) -> None:
        row = await self._session.get(GenerationBatchOrm, batch.id)
        if row is None or row.organization_id != batch.organization_id:
            return
        row.status = batch.status.value
        row.completed_rows = batch.completed_rows
        row.failed_rows = batch.failed_rows
        row.completed_at = batch.completed_at
        await self._session.commit()

    async def get_document(
        self, batch_id: UUID, row_index: int, organization_id: UUID
    ) -> GeneratedDocument | None:
        row = (
            await self._session.execute(
                select(GeneratedDocumentOrm)
                .join(GenerationBatchOrm, GeneratedDocumentOrm.batch_id == GenerationBatchOrm.id)
                .where(
                    GeneratedDocumentOrm.batch_id == batch_id,
                    GeneratedDocumentOrm.row_index == row_index,
                    GenerationBatchOrm.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        return _document_to_domain(row) if row is not None else None

    async def list_documents(
        self, batch_id: UUID, organization_id: UUID
    ) -> list[GeneratedDocument]:
        rows = (
            (
                await self._session.execute(
                    select(GeneratedDocumentOrm)
                    .join(
                        GenerationBatchOrm, GeneratedDocumentOrm.batch_id == GenerationBatchOrm.id
                    )
                    .where(
                        GeneratedDocumentOrm.batch_id == batch_id,
                        GenerationBatchOrm.organization_id == organization_id,
                    )
                    .order_by(GeneratedDocumentOrm.row_index)
                )
            )
            .scalars()
            .all()
        )
        return [_document_to_domain(row) for row in rows]

    async def update_document(
        self, document: GeneratedDocument, organization_id: UUID
    ) -> None:
        row = (
            await self._session.execute(
                select(GeneratedDocumentOrm)
                .join(GenerationBatchOrm, GeneratedDocumentOrm.batch_id == GenerationBatchOrm.id)
                .where(
                    GeneratedDocumentOrm.id == document.id,
                    GenerationBatchOrm.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return
        row.status = document.status.value
        row.output_key = document.output_key
        row.error_message = document.error_message
        await self._session.commit()


def _batch_to_orm(batch: GenerationBatch) -> GenerationBatchOrm:
    return GenerationBatchOrm(
        id=batch.id,
        organization_id=batch.organization_id,
        template_id=batch.template_id,
        status=batch.status.value,
        total_rows=batch.total_rows,
        completed_rows=batch.completed_rows,
        failed_rows=batch.failed_rows,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


def _batch_to_domain(row: GenerationBatchOrm) -> GenerationBatch:
    return GenerationBatch(
        id=row.id,
        organization_id=row.organization_id,
        template_id=row.template_id,
        status=BatchStatus(row.status),
        total_rows=row.total_rows,
        completed_rows=row.completed_rows,
        failed_rows=row.failed_rows,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


def _document_to_orm(document: GeneratedDocument) -> GeneratedDocumentOrm:
    return GeneratedDocumentOrm(
        id=document.id,
        batch_id=document.batch_id,
        row_index=document.row_index,
        status=document.status.value,
        row_data=document.row_data,
        output_key=document.output_key,
        error_message=document.error_message,
    )


def _document_to_domain(row: GeneratedDocumentOrm) -> GeneratedDocument:
    return GeneratedDocument(
        id=row.id,
        batch_id=row.batch_id,
        row_index=row.row_index,
        status=DocumentStatus(row.status),
        row_data=dict(row.row_data),
        output_key=row.output_key,
        error_message=row.error_message,
    )
