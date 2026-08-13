from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.identity.models import Organization, Role, User
from src.infrastructure.persistence.database import async_session_factory, engine
from src.infrastructure.persistence.orm_models import Base
from src.infrastructure.persistence.postgres_organization_repository import (
    PostgresOrganizationRepository,
)
from src.infrastructure.persistence.postgres_user_repository import PostgresUserRepository

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


async def test_organization_repository_roundtrip(session: AsyncSession) -> None:
    repo = PostgresOrganizationRepository(session)
    organization = Organization.create(name="Restrepo & Asociados", created_at=_now())

    await repo.add(organization)

    persisted = await repo.get_by_id(organization.id)
    assert persisted == organization


async def test_organization_repository_get_by_id_returns_none_when_missing(
    session: AsyncSession,
) -> None:
    repo = PostgresOrganizationRepository(session)
    assert await repo.get_by_id(uuid4()) is None


async def test_user_repository_roundtrip(session: AsyncSession) -> None:
    organization = Organization.create(name="Restrepo & Asociados", created_at=_now())
    await PostgresOrganizationRepository(session).add(organization)

    user_repo = PostgresUserRepository(session)
    user = User.create_owner(
        organization_id=organization.id,
        email="ana@restrepo.co",
        hashed_password="hashed",
        created_at=_now(),
    )
    await user_repo.add(user)

    by_email = await user_repo.get_by_email("ana@restrepo.co")
    by_id = await user_repo.get_by_id(user.id)

    assert by_email == user
    assert by_id == user
    assert by_email is not None
    assert by_email.role is Role.OWNER


async def test_user_repository_get_by_email_returns_none_when_missing(
    session: AsyncSession,
) -> None:
    repo = PostgresUserRepository(session)
    assert await repo.get_by_email("fantasma@restrepo.co") is None


async def test_user_repository_enforces_unique_email(session: AsyncSession) -> None:
    organization = Organization.create(name="Restrepo & Asociados", created_at=_now())
    await PostgresOrganizationRepository(session).add(organization)

    user_repo = PostgresUserRepository(session)
    await user_repo.add(
        User.create_owner(
            organization_id=organization.id,
            email="duplicada@restrepo.co",
            hashed_password="hashed",
            created_at=_now(),
        )
    )

    with pytest.raises(IntegrityError):
        await user_repo.add(
            User.create_owner(
                organization_id=organization.id,
                email="duplicada@restrepo.co",
                hashed_password="otro-hash",
                created_at=_now(),
            )
        )
