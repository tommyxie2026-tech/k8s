from __future__ import annotations

from threading import Lock

from app.schemas.common import TaskInfo, TaskStatus


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, TaskInfo] = {}

    def create(self, task: TaskInfo) -> TaskInfo:
        with self._lock:
            self._tasks[task.task_id] = task
        return task

    def update_status(
        self, task_id: str, status: TaskStatus, return_code: int | None = None
    ) -> None:
        with self._lock:
            task = self._tasks[task_id]
            self._tasks[task_id] = task.model_copy(
                update={"status": status, "return_code": return_code}
            )

    def get(self, task_id: str) -> TaskInfo | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list(self) -> list[TaskInfo]:
        with self._lock:
            return list(self._tasks.values())


task_store = InMemoryTaskStore()
