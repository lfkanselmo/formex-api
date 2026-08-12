from __future__ import annotations

from src.domain.errors import DomainError


class MissingPlaceholdersError(DomainError):
    def __init__(self, missing: frozenset[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing placeholders: {', '.join(sorted(missing))}")
