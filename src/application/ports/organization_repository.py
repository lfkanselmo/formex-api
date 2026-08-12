from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.domain.identity.models import Organization


class OrganizationRepositoryProtocol(Protocol):
    def add(self, organization: Organization) -> None: ...

    def get_by_id(self, organization_id: UUID) -> Organization | None: ...
