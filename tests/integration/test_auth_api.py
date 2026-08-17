from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from src.infrastructure.api.main import app
from src.infrastructure.persistence.database import engine
from src.infrastructure.persistence.orm_models import Base

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _clean_database() -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            await connection.execute(table.delete())


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _register(
    client: TestClient, organization_name: str, email: str, password: str = "supersecret1"
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"organization_name": organization_name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_returns_access_and_refresh_tokens(client: TestClient) -> None:
    tokens = _register(client, "Restrepo & Asociados", "ana@restrepo.co")

    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _register(client, "Restrepo & Asociados", "repetida@restrepo.co")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Otra Firma",
            "email": "repetida@restrepo.co",
            "password": "otra-clave-1",
        },
    )

    assert response.status_code == 409


def test_login_returns_tokens_for_correct_credentials(client: TestClient) -> None:
    _register(client, "Restrepo & Asociados", "ana@restrepo.co", "supersecret1")

    response = client.post(
        "/api/v1/auth/login", json={"email": "ana@restrepo.co", "password": "supersecret1"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    _register(client, "Restrepo & Asociados", "ana@restrepo.co", "supersecret1")

    response = client.post(
        "/api/v1/auth/login", json={"email": "ana@restrepo.co", "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_is_rate_limited(client: TestClient) -> None:
    _register(client, "Restrepo & Asociados", "limite@restrepo.co", "supersecret1")

    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "limite@restrepo.co", "password": "wrong-password"},
        )
        for _ in range(21)
    ]

    assert responses[-1].status_code == 429


def test_refresh_mints_new_access_token(client: TestClient) -> None:
    tokens = _register(client, "Restrepo & Asociados", "ana@restrepo.co")

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["access_token"] != tokens["access_token"]


def test_refresh_rejects_garbage_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage"})

    assert response.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh_token(client: TestClient) -> None:
    tokens = _register(client, "Restrepo & Asociados", "ana@restrepo.co")

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )

    assert response.status_code == 401


def test_me_returns_current_user_profile(client: TestClient) -> None:
    tokens = _register(client, "Restrepo & Asociados", "ana@restrepo.co")

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ana@restrepo.co"
    assert body["role"] == "owner"


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_reflects_own_organization_only(client: TestClient) -> None:
    tokens_a = _register(client, "Restrepo & Asociados", "ana@restrepo.co")
    tokens_b = _register(client, "Gomez Consultores", "bruno@gomez.co")

    me_a = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens_a['access_token']}"}
    ).json()
    me_b = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens_b['access_token']}"}
    ).json()

    assert me_a["organization_id"] != me_b["organization_id"]
    assert me_a["email"] == "ana@restrepo.co"
    assert me_b["email"] == "bruno@gomez.co"
