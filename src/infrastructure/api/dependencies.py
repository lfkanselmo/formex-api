from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.token_service import AccessTokenClaims
from src.domain.identity.exceptions import InvalidTokenError
from src.infrastructure.config import settings
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.postgres_organization_repository import (
    PostgresOrganizationRepository,
)
from src.infrastructure.persistence.postgres_user_repository import PostgresUserRepository
from src.infrastructure.security.jwt_service import JwtTokenService
from src.infrastructure.security.password_hasher import Argon2PasswordHasher

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_organization_repository(session: SessionDep) -> PostgresOrganizationRepository:
    return PostgresOrganizationRepository(session)


def get_user_repository(session: SessionDep) -> PostgresUserRepository:
    return PostgresUserRepository(session)


OrganizationRepoDep = Annotated[
    PostgresOrganizationRepository, Depends(get_organization_repository)
]
UserRepoDep = Annotated[PostgresUserRepository, Depends(get_user_repository)]


def get_password_hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service() -> JwtTokenService:
    return JwtTokenService(
        settings.secret_key,
        settings.access_token_expire_minutes,
        settings.refresh_token_expire_minutes,
    )


PasswordHasherDep = Annotated[Argon2PasswordHasher, Depends(get_password_hasher)]
TokenServiceDep = Annotated[JwtTokenService, Depends(get_token_service)]

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    token_service: TokenServiceDep,
) -> AccessTokenClaims:
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return token_service.verify_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


CurrentClaimsDep = Annotated[AccessTokenClaims, Depends(get_current_claims)]
