from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.use_cases.register_organization import RegisterOrganizationUseCase
from src.domain.identity.exceptions import UserAlreadyExistsError
from src.domain.identity.models import Organization, Role, User


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self.added: Organization | None = None

    async def add(self, organization: Organization) -> None:
        self.added = organization

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        if self.added is not None and self.added.id == organization_id:
            return self.added
        return None


class FakeUserRepository:
    def __init__(self, users: list[User] | None = None) -> None:
        self._by_email = {u.email: u for u in (users or [])}
        self.added: User | None = None

    async def add(self, user: User) -> None:
        self.added = user
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


async def test_execute_creates_organization_and_owner() -> None:
    org_repo = FakeOrganizationRepository()
    user_repo = FakeUserRepository()
    use_case = RegisterOrganizationUseCase(org_repo, user_repo, FakePasswordHasher())

    owner = await use_case.execute("Restrepo & Asociados", "ana@restrepo.co", "supersecret")

    assert org_repo.added is not None
    assert org_repo.added.name == "Restrepo & Asociados"
    assert owner.organization_id == org_repo.added.id
    assert owner.role is Role.OWNER
    assert owner.hashed_password == "hashed:supersecret"
    assert user_repo.added == owner


async def test_execute_rejects_duplicate_email() -> None:
    existing = User.create_owner(
        organization_id=uuid4(),
        email="ya@restrepo.co",
        hashed_password="x",
        created_at=datetime.now(UTC),
    )
    use_case = RegisterOrganizationUseCase(
        FakeOrganizationRepository(), FakeUserRepository([existing]), FakePasswordHasher()
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute("Otra Firma", "ya@restrepo.co", "supersecret")
