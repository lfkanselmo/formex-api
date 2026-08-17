from fastapi import APIRouter, HTTPException, Request, status

from src.application.ports.token_service import AccessTokenClaims
from src.application.use_cases.login import LoginUseCase
from src.application.use_cases.refresh_access_token import RefreshAccessTokenUseCase
from src.application.use_cases.register_organization import RegisterOrganizationUseCase
from src.domain.identity.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from src.infrastructure.api.dependencies import (
    CurrentClaimsDep,
    OrganizationRepoDep,
    PasswordHasherDep,
    TokenServiceDep,
    UserRepoDep,
)
from src.infrastructure.api.rate_limiting import limiter
from src.infrastructure.api.v1.auth_schemas import (
    AccessTokenOut,
    AuthTokensOut,
    CurrentUserOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokensOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def register(
    request: Request,
    payload: RegisterIn,
    organization_repository: OrganizationRepoDep,
    user_repository: UserRepoDep,
    password_hasher: PasswordHasherDep,
    token_service: TokenServiceDep,
) -> AuthTokensOut:
    try:
        use_case = RegisterOrganizationUseCase(
            organization_repository, user_repository, password_hasher
        )
        owner = await use_case.execute(payload.organization_name, payload.email, payload.password)
    except UserAlreadyExistsError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    claims = AccessTokenClaims(
        user_id=owner.id, organization_id=owner.organization_id, role=owner.role
    )
    return AuthTokensOut(
        access_token=token_service.create_access_token(claims),
        refresh_token=token_service.create_refresh_token(owner.id),
    )


@router.post("/login", response_model=AuthTokensOut)
@limiter.limit("20/minute")
async def login(
    request: Request,
    payload: LoginIn,
    user_repository: UserRepoDep,
    password_hasher: PasswordHasherDep,
    token_service: TokenServiceDep,
) -> AuthTokensOut:
    try:
        use_case = LoginUseCase(user_repository, password_hasher, token_service)
        tokens = await use_case.execute(payload.email, payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from error
    return AuthTokensOut(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh(
    payload: RefreshIn,
    user_repository: UserRepoDep,
    token_service: TokenServiceDep,
) -> AccessTokenOut:
    try:
        use_case = RefreshAccessTokenUseCase(user_repository, token_service)
        access_token = await use_case.execute(payload.refresh_token)
    except InvalidTokenError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from error
    return AccessTokenOut(access_token=access_token)


@router.get("/me", response_model=CurrentUserOut)
async def me(claims: CurrentClaimsDep, user_repository: UserRepoDep) -> CurrentUserOut:
    user = await user_repository.get_by_id(claims.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return CurrentUserOut(
        id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )
