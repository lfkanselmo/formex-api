from __future__ import annotations

from src.domain.errors import DomainError


class MissingPlaceholdersError(DomainError):
    def __init__(self, missing: frozenset[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing placeholders: {', '.join(sorted(missing))}")


class TemplateNotFoundError(DomainError):
    def __init__(self, template_id: object) -> None:
        super().__init__(f"Template not found: {template_id}")


class BatchNotFoundError(DomainError):
    def __init__(self, batch_id: object) -> None:
        super().__init__(f"Batch not found: {batch_id}")


class DocumentNotFoundError(DomainError):
    def __init__(self, batch_id: object, row_index: int) -> None:
        super().__init__(f"Document not found: batch {batch_id}, row {row_index}")
