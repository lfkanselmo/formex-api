from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.infrastructure.api.dependencies import BatchRepoDep, CurrentClaimsDep
from src.infrastructure.api.v1.batch_schemas import BatchOut, DocumentOut

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("", response_model=list[BatchOut])
async def list_batches(claims: CurrentClaimsDep, batch_repository: BatchRepoDep) -> list[BatchOut]:
    batches = await batch_repository.list_all(claims.organization_id)
    return [BatchOut.from_domain(batch) for batch in batches]


@router.get("/{batch_id}", response_model=BatchOut)
async def get_batch(
    batch_id: UUID, claims: CurrentClaimsDep, batch_repository: BatchRepoDep
) -> BatchOut:
    batch = await batch_repository.get_by_id(batch_id, claims.organization_id)
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    return BatchOut.from_domain(batch)


@router.get("/{batch_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    batch_id: UUID, claims: CurrentClaimsDep, batch_repository: BatchRepoDep
) -> list[DocumentOut]:
    batch = await batch_repository.get_by_id(batch_id, claims.organization_id)
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    documents = await batch_repository.list_documents(batch_id, claims.organization_id)
    return [DocumentOut.from_domain(document) for document in documents]
