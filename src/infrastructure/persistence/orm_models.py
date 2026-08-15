from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


class OrganizationOrm(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    created_at: Mapped[datetime]


class UserOrm(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    role: Mapped[str]
    created_at: Mapped[datetime]


class TemplateOrm(Base):
    __tablename__ = "templates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str]
    storage_key: Mapped[str]
    placeholders: Mapped[list[str]] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime]


class GenerationBatchOrm(Base):
    __tablename__ = "generation_batches"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    template_id: Mapped[UUID] = mapped_column(ForeignKey("templates.id"))
    status: Mapped[str]
    total_rows: Mapped[int]
    completed_rows: Mapped[int]
    failed_rows: Mapped[int]
    created_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]


class GeneratedDocumentOrm(Base):
    __tablename__ = "generated_documents"
    __table_args__ = (UniqueConstraint("batch_id", "row_index"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("generation_batches.id"))
    row_index: Mapped[int]
    status: Mapped[str]
    row_data: Mapped[dict[str, str]] = mapped_column(JSONB)
    output_key: Mapped[str | None]
    error_message: Mapped[str | None]
