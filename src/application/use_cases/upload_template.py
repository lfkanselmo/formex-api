from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.application.ports.document_storage import DocumentStorageProtocol
from src.application.ports.render_engine import RenderEngineProtocol
from src.application.ports.template_repository import TemplateRepositoryProtocol
from src.domain.generation.models import Template


class UploadTemplateUseCase:
    def __init__(
        self,
        template_repository: TemplateRepositoryProtocol,
        storage: DocumentStorageProtocol,
        render_engine: RenderEngineProtocol,
    ) -> None:
        self._templates = template_repository
        self._storage = storage
        self._render_engine = render_engine

    async def execute(self, organization_id: UUID, name: str, content: bytes) -> Template:
        placeholders = self._render_engine.detect_placeholders(content)
        storage_key = f"templates/{organization_id}/{uuid4()}.docx"
        await self._storage.save(storage_key, content)

        template = Template.create(
            organization_id=organization_id,
            name=name,
            storage_key=storage_key,
            placeholders=sorted(placeholders),
            created_at=datetime.now(UTC),
        )
        await self._templates.add(template)
        return template
