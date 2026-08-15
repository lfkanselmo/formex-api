from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status

from src.application.use_cases.submit_batch import SubmitBatchUseCase
from src.application.use_cases.upload_template import UploadTemplateUseCase
from src.domain.generation.exceptions import TemplateNotFoundError
from src.infrastructure.api.dependencies import (
    BatchDispatcherDep,
    BatchRepoDep,
    CurrentClaimsDep,
    DocumentStorageDep,
    ExcelRowParserDep,
    RenderEngineDep,
    TemplateRepoDep,
)
from src.infrastructure.api.v1.batch_schemas import BatchOut
from src.infrastructure.api.v1.template_schemas import TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile,
    claims: CurrentClaimsDep,
    template_repository: TemplateRepoDep,
    storage: DocumentStorageDep,
    render_engine: RenderEngineDep,
) -> TemplateOut:
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"El archivo supera el tamaño máximo permitido ({max_mb} MB)",
        )

    use_case = UploadTemplateUseCase(template_repository, storage, render_engine)
    template = await use_case.execute(
        claims.organization_id, file.filename or "plantilla.docx", content
    )
    return TemplateOut.from_domain(template)


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    claims: CurrentClaimsDep, template_repository: TemplateRepoDep
) -> list[TemplateOut]:
    templates = await template_repository.list_all(claims.organization_id)
    return [TemplateOut.from_domain(template) for template in templates]


@router.post(
    "/{template_id}/batches", response_model=BatchOut, status_code=status.HTTP_201_CREATED
)
async def submit_batch(
    template_id: UUID,
    file: UploadFile,
    claims: CurrentClaimsDep,
    template_repository: TemplateRepoDep,
    batch_repository: BatchRepoDep,
    excel_row_parser: ExcelRowParserDep,
    dispatcher: BatchDispatcherDep,
) -> BatchOut:
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"El archivo supera el tamaño máximo permitido ({max_mb} MB)",
        )

    use_case = SubmitBatchUseCase(
        template_repository, batch_repository, excel_row_parser, dispatcher
    )
    try:
        batch = await use_case.execute(claims.organization_id, template_id, content)
    except TemplateNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return BatchOut.from_domain(batch)
