from pathlib import Path
from uuid import UUID

from sqlalchemy import inspect

from app.db.base import Base, ResourceMixin
from app.db.session import create_database_engine
from app.utils.ids import new_resource_id, new_resource_version


class ExampleResource(ResourceMixin, Base):
    __tablename__ = "example_resources"


def test_uuid7_compatible_identifiers_are_valid_uuid_version_7() -> None:
    resource_id = UUID(new_resource_id())
    resource_version = UUID(new_resource_version())

    assert resource_id.version == 7
    assert resource_version.version == 7
    assert resource_id.variant == "specified in RFC 4122"


def test_create_database_engine_creates_sqlite_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "platform.db"

    engine = create_database_engine(f"sqlite:///{db_path}")

    assert db_path.parent.exists()
    assert str(engine.url).endswith(str(db_path))


def test_resource_mixin_exposes_frozen_common_columns() -> None:
    columns = {column.name for column in inspect(ExampleResource).columns}

    assert {
        "id",
        "kind",
        "name",
        "display_name",
        "description",
        "labels",
        "annotations",
        "spec",
        "status",
        "generation",
        "resource_version",
        "created_at",
        "updated_at",
        "deleted_at",
    }.issubset(columns)
