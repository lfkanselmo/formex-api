from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.generation.models import (
    DocumentStatus,
    GeneratedDocument,
    GenerationBatch,
    Template,
)
from src.domain.identity.models import Organization
from src.infrastructure.persistence.database import async_session_factory, engine
from src.infrastructure.persistence.orm_models import Base
from src.infrastructure.persistence.postgres_batch_repository import PostgresBatchRepository
from src.infrastructure.persistence.postgres_organization_repository import (
    PostgresOrganizationRepository,
)
from src.infrastructure.persistence.postgres_template_repository import (
    PostgresTemplateRepository,
)

pytestmark = pytest.mark.integration


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_session_factory() as db_session:
        yield db_session
    async with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            await connection.execute(table.delete())


def _now() -> datetime:
    return datetime.now(UTC)


async def _seed_organization(session: AsyncSession) -> Organization:
    organization = Organization.create(name="Restrepo & Asociados", created_at=_now())
    await PostgresOrganizationRepository(session).add(organization)
    return organization


async def test_template_repository_roundtrip(session: AsyncSession) -> None:
    organization = await _seed_organization(session)
    repo = PostgresTemplateRepository(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato_Arrendamiento.docx",
        storage_key="templates/contrato.docx",
        placeholders=["arrendatario", "fecha_inicio"],
        created_at=_now(),
    )

    await repo.add(template)

    persisted = await repo.get_by_id(template.id, organization.id)
    assert persisted == template


async def test_template_repository_get_by_id_is_scoped_by_organization(
    session: AsyncSession,
) -> None:
    organization = await _seed_organization(session)
    repo = PostgresTemplateRepository(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=[],
        created_at=_now(),
    )
    await repo.add(template)

    assert await repo.get_by_id(template.id, uuid4()) is None


async def test_template_repository_list_all_orders_by_recent_first(
    session: AsyncSession,
) -> None:
    organization = await _seed_organization(session)
    repo = PostgresTemplateRepository(session)
    older = Template.create(
        organization_id=organization.id,
        name="Older.docx",
        storage_key="templates/older.docx",
        placeholders=[],
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer = Template.create(
        organization_id=organization.id,
        name="Newer.docx",
        storage_key="templates/newer.docx",
        placeholders=[],
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    await repo.add(older)
    await repo.add(newer)

    templates = await repo.list_all(organization.id)

    assert [t.name for t in templates] == ["Newer.docx", "Older.docx"]


async def test_batch_repository_add_persists_batch_and_documents(session: AsyncSession) -> None:
    organization = await _seed_organization(session)
    template_repo = PostgresTemplateRepository(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=["arrendatario"],
        created_at=_now(),
    )
    await template_repo.add(template)

    batch_repo = PostgresBatchRepository(session)
    batch = GenerationBatch.create(
        organization_id=organization.id,
        template_id=template.id,
        total_rows=2,
        created_at=_now(),
    )
    documents = [
        GeneratedDocument.create(batch.id, 0, {"arrendatario": "Maria Gonzalez"}),
        GeneratedDocument.create(batch.id, 1, {"arrendatario": "Juan Perez"}),
    ]

    await batch_repo.add(batch, documents)

    persisted_batch = await batch_repo.get_by_id(batch.id, organization.id)
    assert persisted_batch == batch

    persisted_documents = await batch_repo.list_documents(batch.id, organization.id)
    assert [d.row_data for d in persisted_documents] == [
        {"arrendatario": "Maria Gonzalez"},
        {"arrendatario": "Juan Perez"},
    ]


async def test_batch_repository_get_document_is_scoped_by_organization(
    session: AsyncSession,
) -> None:
    organization = await _seed_organization(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=[],
        created_at=_now(),
    )
    await PostgresTemplateRepository(session).add(template)

    batch_repo = PostgresBatchRepository(session)
    batch = GenerationBatch.create(
        organization_id=organization.id, template_id=template.id, total_rows=1, created_at=_now()
    )
    document = GeneratedDocument.create(batch.id, 0, {})
    await batch_repo.add(batch, [document])

    assert await batch_repo.get_document(batch.id, 0, organization.id) == document
    assert await batch_repo.get_document(batch.id, 0, uuid4()) is None


async def test_batch_repository_update_persists_status_and_counts(session: AsyncSession) -> None:
    organization = await _seed_organization(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=[],
        created_at=_now(),
    )
    await PostgresTemplateRepository(session).add(template)

    batch_repo = PostgresBatchRepository(session)
    batch = GenerationBatch.create(
        organization_id=organization.id, template_id=template.id, total_rows=2, created_at=_now()
    )
    await batch_repo.add(batch, [])

    completed_at = _now()
    updated = batch.with_progress(completed_rows=2, failed_rows=0, completed_at=completed_at)
    await batch_repo.update(updated)

    persisted = await batch_repo.get_by_id(batch.id, organization.id)
    assert persisted is not None
    assert persisted.completed_rows == 2
    assert persisted.completed_at == completed_at


async def test_batch_repository_update_document_persists_completion(
    session: AsyncSession,
) -> None:
    organization = await _seed_organization(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=[],
        created_at=_now(),
    )
    await PostgresTemplateRepository(session).add(template)

    batch_repo = PostgresBatchRepository(session)
    batch = GenerationBatch.create(
        organization_id=organization.id, template_id=template.id, total_rows=1, created_at=_now()
    )
    document = GeneratedDocument.create(batch.id, 0, {})
    await batch_repo.add(batch, [document])

    completed = document.mark_completed("batches/x/0.pdf")
    await batch_repo.update_document(completed, organization.id)

    persisted = await batch_repo.get_document(batch.id, 0, organization.id)
    assert persisted is not None
    assert persisted.status is DocumentStatus.COMPLETED
    assert persisted.output_key == "batches/x/0.pdf"


async def test_batch_repository_update_document_ignores_other_organization(
    session: AsyncSession,
) -> None:
    organization = await _seed_organization(session)
    other_organization = await _seed_organization(session)
    template = Template.create(
        organization_id=organization.id,
        name="Contrato.docx",
        storage_key="templates/contrato.docx",
        placeholders=[],
        created_at=_now(),
    )
    await PostgresTemplateRepository(session).add(template)

    batch_repo = PostgresBatchRepository(session)
    batch = GenerationBatch.create(
        organization_id=organization.id, template_id=template.id, total_rows=1, created_at=_now()
    )
    document = GeneratedDocument.create(batch.id, 0, {})
    await batch_repo.add(batch, [document])

    completed = document.mark_completed("batches/x/0.pdf")
    await batch_repo.update_document(completed, other_organization.id)

    persisted = await batch_repo.get_document(batch.id, 0, organization.id)
    assert persisted is not None
    assert persisted.status is DocumentStatus.PENDING
