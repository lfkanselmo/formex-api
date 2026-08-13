from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.identity.models import Role, User
from src.infrastructure.persistence.orm_models import UserOrm


class PostgresUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(
            UserOrm(
                id=user.id,
                organization_id=user.organization_id,
                email=user.email,
                hashed_password=user.hashed_password,
                role=user.role.value,
                created_at=user.created_at,
            )
        )
        await self._session.commit()

    async def get_by_email(self, email: str) -> User | None:
        row = (
            await self._session.execute(select(UserOrm).where(UserOrm.email == email))
        ).scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserOrm, user_id)
        return _to_domain(row) if row is not None else None


def _to_domain(row: UserOrm) -> User:
    return User(
        id=row.id,
        organization_id=row.organization_id,
        email=row.email,
        hashed_password=row.hashed_password,
        role=Role(row.role),
        created_at=row.created_at,
    )
