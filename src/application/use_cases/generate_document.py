from __future__ import annotations

from uuid import UUID

from src.application.ports.batch_repository import BatchRepositoryProtocol
from src.application.ports.document_storage import DocumentStorageProtocol
from src.application.ports.pdf_converter import PdfConverterProtocol
from src.application.ports.render_engine import RenderEngineProtocol
from src.application.ports.template_repository import TemplateRepositoryProtocol
from src.domain.generation.exceptions import (
    BatchNotFoundError,
    DocumentNotFoundError,
    TemplateNotFoundError,
)


class GenerateDocumentUseCase:
    def __init__(
        self,
        template_repository: TemplateRepositoryProtocol,
        batch_repository: BatchRepositoryProtocol,
        render_engine: RenderEngineProtocol,
        pdf_converter: PdfConverterProtocol,
        storage: DocumentStorageProtocol,
    ) -> None:
        self._templates = template_repository
        self._batches = batch_repository
        self._render_engine = render_engine
        self._pdf_converter = pdf_converter
        self._storage = storage

    async def execute(self, organization_id: UUID, batch_id: UUID, row_index: int) -> None:
        batch = await self._batches.get_by_id(batch_id, organization_id)
        if batch is None:
            raise BatchNotFoundError(batch_id)

        document = await self._batches.get_document(batch_id, row_index, organization_id)
        if document is None:
            raise DocumentNotFoundError(batch_id, row_index)

        template = await self._templates.get_by_id(batch.template_id, organization_id)
        if template is None:
            raise TemplateNotFoundError(batch.template_id)

        document = document.mark_processing()
        await self._batches.update_document(document)

        try:
            template_bytes = await self._storage.load(template.storage_key)
            rendered = self._render_engine.render(template_bytes, dict(document.row_data))
            pdf_bytes = await self._pdf_converter.convert(rendered)
            output_key = f"batches/{batch_id}/{row_index}.pdf"
            await self._storage.save(output_key, pdf_bytes)
            document = document.mark_completed(output_key)
        except Exception as error:
            # A single row's failure (bad data, a down converter, a storage
            # hiccup) must never abort the rest of the batch (RNF-01) — so
            # any failure here is captured and translated to domain state.
            document = document.mark_failed(str(error))

        await self._batches.update_document(document)
