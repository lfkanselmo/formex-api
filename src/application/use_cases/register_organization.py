from __future__ import annotations

from datetime import UTC, datetime

from src.application.ports.organization_repository import OrganizationRepositoryProtocol
from src.application.ports.password_hasher import PasswordHasherProtocol
from src.application.ports.user_repository import UserRepositoryProtocol
from src.domain.identity.exceptions import UserAlreadyExistsError
from src.domain.identity.models import Organization, User


class RegisterOrganizationUseCase:
    def __init__(
        self,
        organization_repository: OrganizationRepositoryProtocol,
        user_repository: UserRepositoryProtocol,
        password_hasher: PasswordHasherProtocol,
    ) -> None:
        self._organization_repository = organization_repository
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, organization_name: str, email: str, plain_password: str) -> User:
        if await self._user_repository.get_by_email(email) is not None:
            raise UserAlreadyExistsError(email)

        now = datetime.now(UTC)
        organization = Organization.create(name=organization_name, created_at=now)
        await self._organization_repository.add(organization)

        owner = User.create_owner(
            organization_id=organization.id,
            email=email,
            hashed_password=self._password_hasher.hash(plain_password),
            created_at=now,
        )
        await self._user_repository.add(owner)
        return owner
