from __future__ import annotations

import ast
from pathlib import Path


ROUTERS_DIR = Path(__file__).resolve().parents[1] / "app" / "routers"

# Transitional violations that already exist before Runtime convergence.
# This allowlist prevents new router-to-executor dependencies while M2 removes
# these legacy call sites one by one.
LEGACY_EXECUTOR_ROUTERS = {
    "backup.py",
    "clusters.py",
    "governance.py",
    "kubevirt.py",
    "nodepools.py",
    "observability.py",
    "storagepools.py",
}

FORBIDDEN_EXECUTOR_MODULES = {
    "app.core.executor",
    "app.services.executor",
}


def _executor_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_EXECUTOR_MODULES:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_EXECUTOR_MODULES:
                    imports.add(alias.name)

    return imports


def test_no_new_router_to_executor_dependencies() -> None:
    """Block new API Plane -> Executor dependencies during incremental migration."""
    violations = {
        path.name: sorted(_executor_imports(path))
        for path in ROUTERS_DIR.glob("*.py")
        if _executor_imports(path)
    }

    unexpected = set(violations) - LEGACY_EXECUTOR_ROUTERS
    assert not unexpected, (
        "New router-to-executor dependency detected. Routers must call "
        f"ResourceService, WorkflowService, or TaskService instead: {sorted(unexpected)}"
    )


def test_legacy_executor_allowlist_stays_explicit() -> None:
    """The temporary allowlist must only contain real router files."""
    existing_router_files = {path.name for path in ROUTERS_DIR.glob("*.py")}
    missing = LEGACY_EXECUTOR_ROUTERS - existing_router_files
    assert not missing, f"Remove stale legacy allowlist entries: {sorted(missing)}"
