from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


PLATFORM_API_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "alembic_version",
    "workflows",
    "workflow_steps",
    "tasks",
    "audit_events",
    "resource_events",
}


def test_empty_sqlite_database_upgrades_to_head(tmp_path: Path) -> None:
    database_path = tmp_path / "cpp-test.db"
    database_url = f"sqlite:///{database_path}"

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PLATFORM_API_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Alembic migration failed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert database_path.exists()

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert EXPECTED_TABLES <= table_names
