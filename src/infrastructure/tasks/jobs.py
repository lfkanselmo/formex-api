from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from src.application.use_cases.generate_document import GenerateDocumentUseCase
from src.domain.generation.models import DocumentStatus
from src.infrastructure.config import settings
from src.infrastructure.pdf.gotenberg_pdf_converter import GotenbergPdfConverter
from src.infrastructure.persistence.database import async_session_factory
from src.infrastructure.persistence.postgres_batch_repository import PostgresBatchRepository
from src.infrastructure.persistence.postgres_template_repository import (
    PostgresTemplateRepository,
)
from src.infrastructure.rendering.docxtpl_render_engine import DocxtplRenderEngine
from src.infrastructure.storage.s3_document_storage import S3DocumentStorage
from src.infrastructure.tasks.celery_app import celery_app


def _build_storage() -> S3DocumentStorage:
    return S3DocumentStorage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
    )


@celery_app.task(name="formex.generate_document")
def generate_document_task(organization_id: str, batch_id: str, row_index: int) -> None:
    asyncio.run(_generate_document(UUID(organization_id), UUID(batch_id), row_index))


async def _generate_document(organization_id: UUID, batch_id: UUID, row_index: int) -> None:
    async with async_session_factory() as session:
        use_case = GenerateDocumentUseCase(
            template_repository=PostgresTemplateRepository(session),
            batch_repository=PostgresBatchRepository(session),
            render_engine=DocxtplRenderEngine(),
            pdf_converter=GotenbergPdfConverter(settings.gotenberg_url),
            storage=_build_storage(),
        )
        await use_case.execute(organization_id, batch_id, row_index)


@celery_app.task(name="formex.finalize_batch")
def finalize_batch_task(_results: list[None], organization_id: str, batch_id: str) -> None:
    asyncio.run(_finalize_batch(UUID(organization_id), UUID(batch_id)))


async def _finalize_batch(organization_id: UUID, batch_id: UUID) -> None:
    async with async_session_factory() as session:
        batches = PostgresBatchRepository(session)
        batch = await batches.get_by_id(batch_id, organization_id)
        if batch is None:
            return

        documents = await batches.list_documents(batch_id, organization_id)
        completed = sum(1 for d in documents if d.status is DocumentStatus.COMPLETED)
        failed = sum(1 for d in documents if d.status is DocumentStatus.FAILED)
        updated = batch.with_progress(
            completed_rows=completed, failed_rows=failed, completed_at=datetime.now(UTC)
        )
        await batches.update(updated)
