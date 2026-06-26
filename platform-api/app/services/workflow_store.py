import json
from pathlib import Path

from app.core.config import settings
from app.schemas.workflows import WorkflowRecord


def _workflow_dir() -> Path:
    base = Path(getattr(settings, "task_log_dir", "/tmp/k8s-platform-api/tasks"))
    path = base / "workflows"
    path.mkdir(parents=True, exist_ok=True)
    return path


class WorkflowStore:
    def save(self, record: WorkflowRecord) -> WorkflowRecord:
        path = _workflow_dir() / f"{record.workflow_id}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        path = _workflow_dir() / f"{workflow_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkflowRecord(**data)

    def list(self) -> list[WorkflowRecord]:
        records: list[WorkflowRecord] = []
        for path in sorted(_workflow_dir().glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(WorkflowRecord(**data))
        return records


workflow_store = WorkflowStore()
