from __future__ import annotations

from src.application.ports.token_service import AccessTokenClaims, TokenServiceProtocol
from src.application.ports.user_repository import UserRepositoryProtocol
from src.domain.identity.exceptions import InvalidTokenError


class RefreshAccessTokenUseCase:
    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        token_service: TokenServiceProtocol,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service

    async def execute(self, refresh_token: str) -> str:
        user_id = self._token_service.verify_refresh_token(refresh_token)
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError()

        claims = AccessTokenClaims(
            user_id=user.id, organization_id=user.organization_id, role=user.role
        )
        return self._token_service.create_access_token(claims)
