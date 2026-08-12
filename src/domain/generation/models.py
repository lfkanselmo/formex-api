from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from src.domain.generation.exceptions import MissingPlaceholdersError


class BatchStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Template:
    id: UUID
    organization_id: UUID
    name: str
    storage_key: str
    placeholders: tuple[str, ...]
    created_at: datetime

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        name: str,
        storage_key: str,
        placeholders: Iterable[str],
        created_at: datetime,
    ) -> Template:
        return cls(
            id=uuid4(),
            organization_id=organization_id,
            name=name,
            storage_key=storage_key,
            placeholders=tuple(placeholders),
            created_at=created_at,
        )

    def missing_placeholders(self, available_columns: Iterable[str]) -> frozenset[str]:
        return frozenset(self.placeholders) - frozenset(available_columns)

    def ensure_columns_cover_placeholders(self, available_columns: Iterable[str]) -> None:
        missing = self.missing_placeholders(available_columns)
        if missing:
            raise MissingPlaceholdersError(missing)


@dataclass(frozen=True, slots=True)
class GenerationBatch:
    id: UUID
    organization_id: UUID
    template_id: UUID
    status: BatchStatus
    total_rows: int
    completed_rows: int
    failed_rows: int
    created_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        template_id: UUID,
        total_rows: int,
        created_at: datetime,
    ) -> GenerationBatch:
        return cls(
            id=uuid4(),
            organization_id=organization_id,
            template_id=template_id,
            status=BatchStatus.PENDING,
            total_rows=total_rows,
            completed_rows=0,
            failed_rows=0,
            created_at=created_at,
        )

    def with_progress(
        self,
        completed_rows: int,
        failed_rows: int,
        completed_at: datetime | None = None,
    ) -> GenerationBatch:
        return replace(
            self,
            completed_rows=completed_rows,
            failed_rows=failed_rows,
            status=self._status_for(completed_rows, failed_rows),
            completed_at=completed_at,
        )

    def _status_for(self, completed_rows: int, failed_rows: int) -> BatchStatus:
        processed = completed_rows + failed_rows
        if processed == 0:
            return BatchStatus.PENDING
        if processed < self.total_rows:
            return BatchStatus.PROCESSING
        if failed_rows == 0:
            return BatchStatus.COMPLETED
        if completed_rows == 0:
            return BatchStatus.FAILED
        return BatchStatus.COMPLETED_WITH_ERRORS


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    id: UUID
    batch_id: UUID
    row_index: int
    status: DocumentStatus
    row_data: dict[str, str]
    output_key: str | None = None
    error_message: str | None = None

    @classmethod
    def create(cls, batch_id: UUID, row_index: int, row_data: dict[str, str]) -> GeneratedDocument:
        return cls(
            id=uuid4(),
            batch_id=batch_id,
            row_index=row_index,
            status=DocumentStatus.PENDING,
            row_data=row_data,
        )

    def mark_processing(self) -> GeneratedDocument:
        return replace(self, status=DocumentStatus.PROCESSING)

    def mark_completed(self, output_key: str) -> GeneratedDocument:
        return replace(
            self, status=DocumentStatus.COMPLETED, output_key=output_key, error_message=None
        )

    def mark_failed(self, error_message: str) -> GeneratedDocument:
        return replace(self, status=DocumentStatus.FAILED, error_message=error_message)
