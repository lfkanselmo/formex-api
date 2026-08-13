from __future__ import annotations

from typing import Protocol


class ExcelRowParserProtocol(Protocol):
    def parse(self, content: bytes) -> list[dict[str, str]]: ...
