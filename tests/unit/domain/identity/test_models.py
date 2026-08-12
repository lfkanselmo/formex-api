from datetime import datetime
from uuid import UUID, uuid4

from src.domain.identity.models import Organization, Role, User


def _now() -> datetime:
    return datetime(2026, 8, 11, 12, 0, 0)


def _build_owner(organization_id: UUID) -> User:
    return User.create_owner(
        organization_id=organization_id,
        email="ana@restrepo.co",
        hashed_password="hashed",
        created_at=_now(),
    )


def test_organization_create_generates_id() -> None:
    organization = Organization.create(name="Restrepo & Asociados", created_at=_now())
    assert organization.name == "Restrepo & Asociados"
    assert organization.id is not None


def test_user_create_owner_has_owner_role() -> None:
    organization_id = uuid4()
    user = _build_owner(organization_id)

    assert user.role is Role.OWNER
    assert user.is_owner
    assert user.organization_id == organization_id


def test_user_belongs_to_own_organization_only() -> None:
    organization_id = uuid4()
    user = _build_owner(organization_id)

    assert user.belongs_to(organization_id)
    assert not user.belongs_to(uuid4())


def test_member_is_not_owner() -> None:
    user = User(
        id=uuid4(),
        organization_id=uuid4(),
        email="miembro@restrepo.co",
        hashed_password="hashed",
        role=Role.MEMBER,
        created_at=_now(),
    )

    assert not user.is_owner
