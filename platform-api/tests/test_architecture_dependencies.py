from __future__ import annotations

import ast
from pathlib import Path


ROUTERS_DIR = Path(__file__).resolve().parents[1] / "app" / "routers"
FORBIDDEN_IMPORTS = {
    "app.core.executor",
    "app.services.executor",
}

# Existing transitional violations are documented here so the test prevents
# regressions without blocking Sprint 1 baseline setup. Each path must be
# removed from this list as routers migrate to WorkflowService/TaskService.
ALLOWED_EXISTING_VIOLATIONS = {
    "backup.py",
    "clusters.py",
    "governance.py",
    "kubevirt.py",
    "nodepools.py",
    "observability.py",
    "storagepools.py",
}


def _direct_forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_IMPORTS:
            violations.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_IMPORTS:
                    violations.append(alias.name)

    return violations


def test_no_new_router_to_executor_dependencies() -> None:
    unexpected: dict[str, list[str]] = {}

    for router_file in sorted(ROUTERS_DIR.glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        violations = _direct_forbidden_imports(router_file)
        if violations and router_file.name not in ALLOWED_EXISTING_VIOLATIONS:
            unexpected[router_file.name] = violations

    assert unexpected == {}, (
        "Routers must not import executor modules directly. "
        "Use WorkflowService or TaskService instead. Unexpected violations: "
        f"{unexpected}"
    )
