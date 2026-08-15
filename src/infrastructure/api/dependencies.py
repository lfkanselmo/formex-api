from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.token_service import AccessTokenClaims
from src.domain.identity.exceptions import InvalidTokenError
from src.infrastructure.config import settings
from src.infrastructure.parsing.openpyxl_row_parser import OpenpyxlRowParser
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.postgres_batch_repository import PostgresBatchRepository
from src.infrastructure.persistence.postgres_organization_repository import (
    PostgresOrganizationRepository,
)
from src.infrastructure.persistence.postgres_template_repository import (
    PostgresTemplateRepository,
)
from src.infrastructure.persistence.postgres_user_repository import PostgresUserRepository
from src.infrastructure.rendering.docxtpl_render_engine import DocxtplRenderEngine
from src.infrastructure.security.jwt_service import JwtTokenService
from src.infrastructure.security.password_hasher import Argon2PasswordHasher
from src.infrastructure.storage.s3_document_storage import S3DocumentStorage
from src.infrastructure.tasks.celery_batch_dispatcher import CeleryBatchDispatcher

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_organization_repository(session: SessionDep) -> PostgresOrganizationRepository:
    return PostgresOrganizationRepository(session)


def get_user_repository(session: SessionDep) -> PostgresUserRepository:
    return PostgresUserRepository(session)


OrganizationRepoDep = Annotated[
    PostgresOrganizationRepository, Depends(get_organization_repository)
]
UserRepoDep = Annotated[PostgresUserRepository, Depends(get_user_repository)]


def get_template_repository(session: SessionDep) -> PostgresTemplateRepository:
    return PostgresTemplateRepository(session)


def get_batch_repository(session: SessionDep) -> PostgresBatchRepository:
    return PostgresBatchRepository(session)


TemplateRepoDep = Annotated[PostgresTemplateRepository, Depends(get_template_repository)]
BatchRepoDep = Annotated[PostgresBatchRepository, Depends(get_batch_repository)]


def get_render_engine() -> DocxtplRenderEngine:
    return DocxtplRenderEngine()


def get_excel_row_parser() -> OpenpyxlRowParser:
    return OpenpyxlRowParser()


def get_document_storage() -> S3DocumentStorage:
    return S3DocumentStorage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
    )


def get_batch_dispatcher() -> CeleryBatchDispatcher:
    return CeleryBatchDispatcher()


RenderEngineDep = Annotated[DocxtplRenderEngine, Depends(get_render_engine)]
ExcelRowParserDep = Annotated[OpenpyxlRowParser, Depends(get_excel_row_parser)]
DocumentStorageDep = Annotated[S3DocumentStorage, Depends(get_document_storage)]
BatchDispatcherDep = Annotated[CeleryBatchDispatcher, Depends(get_batch_dispatcher)]


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
