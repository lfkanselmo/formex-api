from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.domain.identity.models import Role


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    organization_id: UUID
    role: Role


class TokenServiceProtocol(Protocol):
    def create_access_token(self, claims: AccessTokenClaims) -> str: ...

    def create_refresh_token(self, user_id: UUID) -> str: ...

    def verify_access_token(self, token: str) -> AccessTokenClaims: ...

    def verify_refresh_token(self, token: str) -> UUID: ...
