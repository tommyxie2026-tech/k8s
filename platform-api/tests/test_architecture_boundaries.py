from pathlib import Path


ROUTERS_DIR = Path(__file__).resolve().parents[1] / "app" / "routers"
FORBIDDEN_IMPORTS = ("app.core.executor", "app.services.executor")

# Existing technical debt recorded by DESIGN-TO-CODE-GAP-ANALYSIS-v1.0.
# Remove entries as routers are migrated to WorkflowService or TaskService.
LEGACY_EXECUTOR_IMPORT_ALLOWLIST = {
    "backup.py",
    "clusters.py",
    "governance.py",
    "nodepools.py",
    "observability.py",
    "storagepools.py",
}


def test_no_new_router_executor_dependencies() -> None:
    violations: list[str] = []

    for path in sorted(ROUTERS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        imports_executor = any(name in source for name in FORBIDDEN_IMPORTS)
        if imports_executor and path.name not in LEGACY_EXECUTOR_IMPORT_ALLOWLIST:
            violations.append(path.name)

    assert not violations, (
        "Routers must call WorkflowService or TaskService, not executors directly. "
        f"New violations: {violations}"
    )
