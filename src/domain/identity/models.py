from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class Role(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


@dataclass(frozen=True, slots=True)
class Organization:
    id: UUID
    name: str
    created_at: datetime

    @classmethod
    def create(cls, name: str, created_at: datetime) -> Organization:
        return cls(id=uuid4(), name=name, created_at=created_at)


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    organization_id: UUID
    email: str
    hashed_password: str
    role: Role
    created_at: datetime

    @classmethod
    def create_owner(
        cls,
        organization_id: UUID,
        email: str,
        hashed_password: str,
        created_at: datetime,
    ) -> User:
        return cls(
            id=uuid4(),
            organization_id=organization_id,
            email=email,
            hashed_password=hashed_password,
            role=Role.OWNER,
            created_at=created_at,
        )

    @property
    def is_owner(self) -> bool:
        return self.role is Role.OWNER

    def belongs_to(self, organization_id: UUID) -> bool:
        return self.organization_id == organization_id
