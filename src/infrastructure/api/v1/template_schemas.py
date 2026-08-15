from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.generation.models import Template


class TemplateOut(BaseModel):
    id: UUID
    name: str
    placeholders: list[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, template: Template) -> TemplateOut:
        return cls(
            id=template.id,
            name=template.name,
            placeholders=list(template.placeholders),
            created_at=template.created_at,
        )
