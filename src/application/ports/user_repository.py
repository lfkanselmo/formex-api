from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.domain.identity.models import User


class UserRepositoryProtocol(Protocol):
    async def add(self, user: User) -> None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...
