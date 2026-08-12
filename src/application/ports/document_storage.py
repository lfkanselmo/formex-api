from __future__ import annotations

from typing import Protocol


class DocumentStorageProtocol(Protocol):
    async def save(self, key: str, content: bytes) -> None: ...

    async def load(self, key: str) -> bytes: ...
