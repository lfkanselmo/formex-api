from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.password_hasher import PasswordHasherProtocol
from src.application.ports.token_service import AccessTokenClaims, TokenServiceProtocol
from src.application.ports.user_repository import UserRepositoryProtocol
from src.domain.identity.exceptions import InvalidCredentialsError


@dataclass(frozen=True, slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str


class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_hasher: PasswordHasherProtocol,
        token_service: TokenServiceProtocol,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def execute(self, email: str, plain_password: str) -> AuthTokens:
        user = await self._user_repository.get_by_email(email)
        if user is None or not self._password_hasher.verify(
            plain_password, user.hashed_password
        ):
            raise InvalidCredentialsError()

        claims = AccessTokenClaims(
            user_id=user.id, organization_id=user.organization_id, role=user.role
        )
        return AuthTokens(
            access_token=self._token_service.create_access_token(claims),
            refresh_token=self._token_service.create_refresh_token(user.id),
        )
