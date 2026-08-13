from __future__ import annotations

from dataclasses import dataclass

from src.domain.generation.models import Template


@dataclass(frozen=True, slots=True)
class RowValidationError:
    row_number: int
    reason: str


@dataclass(frozen=True, slots=True)
class BatchRowsValidation:
    valid_rows: tuple[dict[str, str], ...]
    errors: tuple[RowValidationError, ...]


class BatchRowValidator:
    def validate(self, template: Template, rows: list[dict[str, str]]) -> BatchRowsValidation:
        valid_rows: list[dict[str, str]] = []
        errors: list[RowValidationError] = []
        for row_number, row in enumerate(rows, start=1):
            missing = template.missing_placeholders(row.keys())
            if missing:
                reason = f"Faltan columnas: {', '.join(sorted(missing))}"
                errors.append(RowValidationError(row_number, reason))
                continue
            valid_rows.append(row)
        return BatchRowsValidation(tuple(valid_rows), tuple(errors))
