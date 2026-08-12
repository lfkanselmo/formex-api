from __future__ import annotations

from typing import Protocol


class RenderEngineProtocol(Protocol):
    def render(self, template: bytes, context: dict[str, str]) -> bytes: ...
