from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.application.ports.batch_dispatcher import BatchDispatcherProtocol
from src.application.ports.batch_repository import BatchRepositoryProtocol
from src.application.ports.excel_row_parser import ExcelRowParserProtocol
from src.application.ports.template_repository import TemplateRepositoryProtocol
from src.domain.generation.exceptions import InvalidExcelFileError, TemplateNotFoundError
from src.domain.generation.models import GeneratedDocument, GenerationBatch


class SubmitBatchUseCase:
    def __init__(
        self,
        template_repository: TemplateRepositoryProtocol,
        batch_repository: BatchRepositoryProtocol,
        excel_parser: ExcelRowParserProtocol,
        dispatcher: BatchDispatcherProtocol,
    ) -> None:
        self._templates = template_repository
        self._batches = batch_repository
        self._excel_parser = excel_parser
        self._dispatcher = dispatcher

    async def execute(
        self, organization_id: UUID, template_id: UUID, excel_content: bytes
    ) -> GenerationBatch:
        template = await self._templates.get_by_id(template_id, organization_id)
        if template is None:
            raise TemplateNotFoundError(template_id)

        try:
            rows = self._excel_parser.parse(excel_content)
        except Exception as error:
            # Same reasoning as UploadTemplateUseCase: a malformed/non-xlsx
            # upload fails inside openpyxl with a library-specific
            # exception, normalized here to a domain error.
            raise InvalidExcelFileError(str(error)) from error

        batch = GenerationBatch.create(
            organization_id=organization_id,
            template_id=template_id,
            total_rows=len(rows),
            created_at=datetime.now(UTC),
        )

        documents: list[GeneratedDocument] = []
        pending_indices: list[int] = []
        failed_count = 0
        for row_index, row in enumerate(rows):
            document = GeneratedDocument.create(batch.id, row_index, row)
            missing = template.missing_values(row)
            if missing:
                reason = f"Faltan valores: {', '.join(sorted(missing))}"
                document = document.mark_failed(reason)
                failed_count += 1
            else:
                pending_indices.append(row_index)
            documents.append(document)

        if failed_count:
            batch = batch.with_progress(completed_rows=0, failed_rows=failed_count)

        await self._batches.add(batch, documents)

        if pending_indices:
            self._dispatcher.dispatch(organization_id, batch.id, pending_indices)

        return batch
