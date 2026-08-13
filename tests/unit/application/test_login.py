from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.ports.token_service import AccessTokenClaims
from src.application.use_cases.login import LoginUseCase
from src.domain.identity.exceptions import InvalidCredentialsError
from src.domain.identity.models import User


class FakeUserRepository:
    def __init__(self, users: list[User]) -> None:
        self._by_email = {u.email: u for u in users}

    async def add(self, user: User) -> None:
        self._by_email[user.email] = user

    async def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((u for u in self._by_email.values() if u.id == user_id), None)


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeTokenService:
    def create_access_token(self, claims: AccessTokenClaims) -> str:
        return f"access-for-{claims.user_id}"

    def create_refresh_token(self, user_id: UUID) -> str:
        return f"refresh-for-{user_id}"

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        raise NotImplementedError

    def verify_refresh_token(self, token: str) -> UUID:
        raise NotImplementedError


def _user(email: str, password: str) -> User:
    return User.create_owner(
        organization_id=uuid4(),
        email=email,
        hashed_password=f"hashed:{password}",
        created_at=datetime.now(UTC),
    )


async def test_execute_returns_tokens_for_correct_credentials() -> None:
    user = _user("ana@restrepo.co", "supersecret")
    use_case = LoginUseCase(FakeUserRepository([user]), FakePasswordHasher(), FakeTokenService())

    tokens = await use_case.execute("ana@restrepo.co", "supersecret")

    assert tokens.access_token == f"access-for-{user.id}"
    assert tokens.refresh_token == f"refresh-for-{user.id}"


async def test_execute_raises_for_unknown_email() -> None:
    use_case = LoginUseCase(FakeUserRepository([]), FakePasswordHasher(), FakeTokenService())

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute("fantasma@restrepo.co", "cualquiera")


async def test_execute_raises_for_wrong_password() -> None:
    user = _user("ana@restrepo.co", "supersecret")
    use_case = LoginUseCase(FakeUserRepository([user]), FakePasswordHasher(), FakeTokenService())

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute("ana@restrepo.co", "wrong-password")
