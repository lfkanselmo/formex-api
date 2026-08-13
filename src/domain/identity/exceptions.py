from __future__ import annotations

from src.domain.errors import DomainError


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"User already exists: {email}")


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InvalidTokenError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid or expired token")
