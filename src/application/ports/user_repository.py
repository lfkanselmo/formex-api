from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.domain.identity.models import User


class UserRepositoryProtocol(Protocol):
    def add(self, user: User) -> None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: UUID, organization_id: UUID) -> User | None: ...
