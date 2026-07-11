from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.utils.ids import new_resource_id, new_resource_version


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class Base(DeclarativeBase):
    pass


class ResourceMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_resource_id)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    annotations: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    spec: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    resource_version: Mapped[str] = mapped_column(String(36), nullable=False, default=new_resource_version)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now, onupdate=utc_now)
    deleted_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    def touch_resource_version(self) -> None:
        self.resource_version = new_resource_version()
        self.updated_at = utc_now()

    def mark_deleted(self) -> None:
        self.deleted_at = utc_now()
        self.touch_resource_version()
