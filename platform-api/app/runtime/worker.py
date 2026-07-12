from __future__ import annotations

import socket
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories import TaskRepository
from app.db.session import SessionLocal
from app.runtime.executor import ExecutionRequest, ExecutorRegistry, default_executor_registry


class LocalTaskWorker:
    """Single-process durable worker for the V2.0 runtime baseline.

    The worker claims queued tasks from the repository, executes them through the
    registered Executor boundary, persists logs, and records terminal state.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
        executor_registry: ExecutorRegistry | None = None,
        worker_id: str | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.executor_registry = executor_registry or default_executor_registry()
        self.worker_id = worker_id or f"{socket.gethostname()}-{id(self):x}"

    def recover_orphaned(self, *, stale_after_seconds: int = 300) -> int:
        if stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be greater than zero")
        stale_before = (
            datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        ).isoformat().replace("+00:00", "Z")
        with self.session_factory() as session:
            recovered = TaskRepository(session).recover_orphaned(stale_before)
            session.commit()
            return recovered

    def run_once(self) -> str | None:
        task_snapshot = self._claim_next()
        if task_snapshot is None:
            return None

        task_id, executor_type, command_ref, spec = task_snapshot
        request = ExecutionRequest(
            task_id=task_id,
            executor_type=executor_type,
            command_ref=command_ref,
            extra_vars=dict(spec.get("extra_vars") or {}),
            timeout_seconds=spec.get("timeout_seconds"),
        )
        log_path = self._log_path(task_id)

        try:
            executor = self.executor_registry.get(executor_type)
            result = executor.execute(request)
            self._write_log(log_path, result.stdout, result.stderr)
            with self.session_factory() as session:
                tasks = TaskRepository(session)
                tasks.complete(
                    task_id,
                    return_code=result.return_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    log_path=str(log_path),
                )
                session.commit()
        except subprocess.TimeoutExpired as exc:
            message = f"task timed out after {exc.timeout} seconds"
            self._write_log(log_path, "", message)
            self._mark_failed(task_id, message, log_path)
        except Exception as exc:  # noqa: BLE001 - worker must persist all execution failures
            message = f"{type(exc).__name__}: {exc}"
            self._write_log(log_path, "", message)
            self._mark_failed(task_id, message, log_path)

        return task_id

    def heartbeat(self, task_id: str) -> None:
        with self.session_factory() as session:
            TaskRepository(session).heartbeat(task_id, self.worker_id)
            session.commit()

    def _claim_next(self) -> tuple[str, str, str, dict] | None:
        with self.session_factory() as session:
            task = TaskRepository(session).claim_next_queued(self.worker_id)
            if task is None:
                session.rollback()
                return None
            snapshot = (task.id, task.executor_type, task.command_ref, dict(task.spec))
            session.commit()
            return snapshot

    def _mark_failed(self, task_id: str, message: str, log_path: Path) -> None:
        with self.session_factory() as session:
            TaskRepository(session).fail(
                task_id,
                error=message,
                return_code=1,
                log_path=str(log_path),
            )
            session.commit()

    @staticmethod
    def _log_path(task_id: str) -> Path:
        directory = Path(settings.task_log_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{task_id}.log"

    @staticmethod
    def _write_log(path: Path, stdout: str, stderr: str) -> None:
        content = stdout
        if stderr:
            if content and not content.endswith("\n"):
                content += "\n"
            content += stderr
        path.write_text(content, encoding="utf-8")
