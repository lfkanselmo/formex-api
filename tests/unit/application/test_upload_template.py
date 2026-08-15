from uuid import UUID, uuid4

from src.application.use_cases.upload_template import UploadTemplateUseCase
from src.domain.generation.models import Template


class FakeTemplateRepository:
    def __init__(self) -> None:
        self.added: Template | None = None

    async def add(self, template: Template) -> None:
        self.added = template

    async def get_by_id(self, template_id: UUID, organization_id: UUID) -> Template | None:
        return self.added if self.added and self.added.id == template_id else None

    async def list_all(self, organization_id: UUID) -> list[Template]:
        return [self.added] if self.added else []


class FakeDocumentStorage:
    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    async def save(self, key: str, content: bytes) -> None:
        self.saved[key] = content

    async def load(self, key: str) -> bytes:
        return self.saved[key]


class FakeRenderEngine:
    def render(self, template: bytes, context: dict[str, object]) -> bytes:
        raise NotImplementedError

    def detect_placeholders(self, template: bytes) -> frozenset[str]:
        return frozenset({"arrendatario", "fecha_inicio"})


async def test_execute_stores_content_and_creates_template_with_detected_placeholders() -> None:
    organization_id = uuid4()
    templates = FakeTemplateRepository()
    storage = FakeDocumentStorage()
    use_case = UploadTemplateUseCase(templates, storage, FakeRenderEngine())

    template = await use_case.execute(organization_id, "Contrato.docx", b"contenido-docx")

    assert template.organization_id == organization_id
    assert template.name == "Contrato.docx"
    assert template.placeholders == ("arrendatario", "fecha_inicio")
    assert storage.saved[template.storage_key] == b"contenido-docx"
    assert templates.added == template
