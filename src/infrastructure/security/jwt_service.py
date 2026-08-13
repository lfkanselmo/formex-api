from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt

from src.application.ports.token_service import AccessTokenClaims
from src.domain.identity.exceptions import InvalidTokenError
from src.domain.identity.models import Role

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


class JwtTokenService:
    def __init__(
        self,
        secret_key: str,
        access_token_expire_minutes: int,
        refresh_token_expire_minutes: int,
    ) -> None:
        self._secret_key = secret_key
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_minutes = refresh_token_expire_minutes

    def create_access_token(self, claims: AccessTokenClaims) -> str:
        return self._encode(
            {
                "sub": str(claims.user_id),
                "org": str(claims.organization_id),
                "role": claims.role.value,
                "type": _ACCESS_TOKEN_TYPE,
            },
            self._access_token_expire_minutes,
        )

    def create_refresh_token(self, user_id: UUID) -> str:
        return self._encode(
            {"sub": str(user_id), "type": _REFRESH_TOKEN_TYPE},
            self._refresh_token_expire_minutes,
        )

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        payload = self._decode(token, expected_type=_ACCESS_TOKEN_TYPE)
        try:
            return AccessTokenClaims(
                user_id=UUID(payload["sub"]),
                organization_id=UUID(payload["org"]),
                role=Role(payload["role"]),
            )
        except (KeyError, ValueError) as error:
            raise InvalidTokenError() from error

    def verify_refresh_token(self, token: str) -> UUID:
        payload = self._decode(token, expected_type=_REFRESH_TOKEN_TYPE)
        try:
            return UUID(payload["sub"])
        except (KeyError, ValueError) as error:
            raise InvalidTokenError() from error

    def _encode(self, claims: dict[str, str], expire_minutes: int) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=expire_minutes)
        payload: dict[str, Any] = {
            **claims,
            "jti": str(uuid4()),
            "iat": now,
            "exp": expires_at,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")

    def _decode(self, token: str, expected_type: str) -> dict[str, Any]:
        try:
            payload: dict[str, Any] = jwt.decode(token, self._secret_key, algorithms=["HS256"])
        except jwt.PyJWTError as error:
            raise InvalidTokenError() from error
        if payload.get("type") != expected_type:
            raise InvalidTokenError()
        return payload
