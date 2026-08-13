from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.ports.token_service import AccessTokenClaims
from src.application.use_cases.refresh_access_token import RefreshAccessTokenUseCase
from src.domain.identity.exceptions import InvalidTokenError
from src.domain.identity.models import User


class FakeUserRepository:
    def __init__(self, users: list[User]) -> None:
        self._by_id = {u.id: u for u in users}

    async def add(self, user: User) -> None:
        self._by_id[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)


class FakeTokenService:
    def __init__(self, user_id_for_refresh_token: UUID | None = None) -> None:
        self._user_id_for_refresh_token = user_id_for_refresh_token

    def create_access_token(self, claims: AccessTokenClaims) -> str:
        return f"access-for-{claims.user_id}"

    def create_refresh_token(self, user_id: UUID) -> str:
        return f"refresh-for-{user_id}"

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        raise NotImplementedError

    def verify_refresh_token(self, token: str) -> UUID:
        if self._user_id_for_refresh_token is None:
            raise InvalidTokenError()
        return self._user_id_for_refresh_token


def _user() -> User:
    return User.create_owner(
        organization_id=uuid4(),
        email="ana@restrepo.co",
        hashed_password="hashed",
        created_at=datetime.now(UTC),
    )


async def test_execute_mints_new_access_token_for_valid_refresh_token() -> None:
    user = _user()
    use_case = RefreshAccessTokenUseCase(
        FakeUserRepository([user]), FakeTokenService(user_id_for_refresh_token=user.id)
    )

    access_token = await use_case.execute("a-refresh-token")

    assert access_token == f"access-for-{user.id}"


async def test_execute_raises_when_refresh_token_is_invalid() -> None:
    use_case = RefreshAccessTokenUseCase(FakeUserRepository([]), FakeTokenService())

    with pytest.raises(InvalidTokenError):
        await use_case.execute("garbage")


async def test_execute_raises_when_user_no_longer_exists() -> None:
    missing_user_id = uuid4()
    use_case = RefreshAccessTokenUseCase(
        FakeUserRepository([]), FakeTokenService(user_id_for_refresh_token=missing_user_id)
    )

    with pytest.raises(InvalidTokenError):
        await use_case.execute("a-refresh-token")
