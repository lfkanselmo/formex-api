from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.identity.models import Organization
from src.infrastructure.persistence.orm_models import OrganizationOrm


class PostgresOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, organization: Organization) -> None:
        self._session.add(
            OrganizationOrm(
                id=organization.id,
                name=organization.name,
                created_at=organization.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        row = await self._session.get(OrganizationOrm, organization_id)
        return _to_domain(row) if row is not None else None


def _to_domain(row: OrganizationOrm) -> Organization:
    return Organization(id=row.id, name=row.name, created_at=row.created_at)
