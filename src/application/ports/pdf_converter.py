from __future__ import annotations

from typing import Protocol


class PdfConverterProtocol(Protocol):
    async def convert(self, document: bytes) -> bytes: ...
