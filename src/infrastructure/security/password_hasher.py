from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self._hasher.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
