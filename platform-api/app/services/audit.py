import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def audit(event: str, **fields) -> None:
    base = Path(getattr(settings, "task_log_dir", "/tmp/k8s-platform-api/tasks"))
    base.mkdir(parents=True, exist_ok=True)
    path = base / "audit.log"
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
