from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.domain.identity.models import Role


class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class AuthTokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class CurrentUserOut(BaseModel):
    id: UUID
    organization_id: UUID
    email: EmailStr
    role: Role
    created_at: datetime
