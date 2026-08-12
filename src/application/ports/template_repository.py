from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.domain.generation.models import Template


class TemplateRepositoryProtocol(Protocol):
    def add(self, template: Template) -> None: ...

    def get_by_id(self, template_id: UUID, organization_id: UUID) -> Template | None: ...

    def list_all(self, organization_id: UUID) -> list[Template]: ...
