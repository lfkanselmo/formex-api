from __future__ import annotations

from typing import Protocol


class RenderEngineProtocol(Protocol):
    def render(self, template: bytes, context: dict[str, object]) -> bytes: ...

    def detect_placeholders(self, template: bytes) -> frozenset[str]: ...
