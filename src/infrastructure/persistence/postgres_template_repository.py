from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.generation.models import Template
from src.infrastructure.persistence.orm_models import TemplateOrm


class PostgresTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, template: Template) -> None:
        self._session.add(
            TemplateOrm(
                id=template.id,
                organization_id=template.organization_id,
                name=template.name,
                storage_key=template.storage_key,
                placeholders=list(template.placeholders),
                created_at=template.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, template_id: UUID, organization_id: UUID) -> Template | None:
        row = (
            await self._session.execute(
                select(TemplateOrm).where(
                    TemplateOrm.id == template_id,
                    TemplateOrm.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def list_all(self, organization_id: UUID) -> list[Template]:
        rows = (
            (
                await self._session.execute(
                    select(TemplateOrm)
                    .where(TemplateOrm.organization_id == organization_id)
                    .order_by(TemplateOrm.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(row: TemplateOrm) -> Template:
    return Template(
        id=row.id,
        organization_id=row.organization_id,
        name=row.name,
        storage_key=row.storage_key,
        placeholders=tuple(row.placeholders),
        created_at=row.created_at,
    )
