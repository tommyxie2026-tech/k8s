from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from app.db.base import Base
from app.db import models  # noqa: F401


def test_metadata_defines_required_core_tables() -> None:
    expected_tables = {
        "workflows",
        "tasks",
        "audit_events",
        "resource_events",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_schema_compiles_for_sqlite_and_postgresql() -> None:
    """Guard SQLite-first / PostgreSQL-later compatibility from FROZEN-P2-03."""

    for table in Base.metadata.sorted_tables:
        sqlite_sql = str(CreateTable(table).compile(dialect=sqlite.dialect()))
        postgres_sql = str(CreateTable(table).compile(dialect=postgresql.dialect()))

        assert "CREATE TABLE" in sqlite_sql
        assert "CREATE TABLE" in postgres_sql
