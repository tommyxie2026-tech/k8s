from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.repositories import TaskRepository
from app.runtime.executor import ExecutionRequest, ExecutionResult, ExecutorRegistry
from app.runtime.worker import LocalTaskWorker
from app.services.task_service import TaskService


class StubExecutor:
    executor_type = "stub"

    def __init__(self, *, return_code: int = 0) -> None:
        self.return_code = return_code
        self.requests: list[ExecutionRequest] = []

    def build_command(self, request: ExecutionRequest) -> list[str]:
        return ["stub", request.command_ref]

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return ExecutionResult(
            task_id=request.task_id,
            executor_type=self.executor_type,
            command=self.build_command(request),
            return_code=self.return_code,
            stdout="worker stdout",
            stderr="" if self.return_code == 0 else "worker stderr",
        )


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_worker_claims_executes_and_persists_success(tmp_path, monkeypatch) -> None:
    session_factory = make_session_factory()
    executor = StubExecutor()
    registry = ExecutorRegistry([executor])
    monkeypatch.setattr(settings, "task_log_dir", str(tmp_path))

    with session_factory() as session:
        task = TaskService(session, executor_registry=registry).enqueue(
            name="runtime-success",
            executor_type="stub",
            command_ref="example-command",
            extra_vars={"check": True},
            timeout_seconds=30,
        )
        task_id = task.id

    worker = LocalTaskWorker(
        session_factory=session_factory,
        executor_registry=registry,
        worker_id="worker-test",
    )

    assert worker.run_once() == task_id
    assert len(executor.requests) == 1
    assert executor.requests[0].extra_vars == {"check": True}

    with session_factory() as session:
        loaded = TaskRepository(session).require(task_id)
        assert loaded.phase == "succeeded"
        assert loaded.return_code == 0
        assert loaded.stdout == "worker stdout"
        assert loaded.started_at is not None
        assert loaded.finished_at is not None
        assert loaded.status["worker_id"] == "worker-test"
        assert loaded.log_path is not None

    assert (tmp_path / f"{task_id}.log").read_text(encoding="utf-8") == "worker stdout"


def test_worker_persists_executor_failure(tmp_path, monkeypatch) -> None:
    session_factory = make_session_factory()
    executor = StubExecutor(return_code=2)
    registry = ExecutorRegistry([executor])
    monkeypatch.setattr(settings, "task_log_dir", str(tmp_path))

    with session_factory() as session:
        task_id = TaskService(session, executor_registry=registry).enqueue(
            name="runtime-failure",
            executor_type="stub",
            command_ref="failing-command",
        ).id

    worker = LocalTaskWorker(session_factory=session_factory, executor_registry=registry)
    assert worker.run_once() == task_id

    with session_factory() as session:
        loaded = TaskRepository(session).require(task_id)
        assert loaded.phase == "failed"
        assert loaded.return_code == 2
        assert loaded.stderr == "worker stderr"


def test_worker_recovers_stale_running_task() -> None:
    session_factory = make_session_factory()
    executor = StubExecutor()
    registry = ExecutorRegistry([executor])

    with session_factory() as session:
        task = TaskService(session, executor_registry=registry).enqueue(
            name="orphaned-task",
            executor_type="stub",
            command_ref="example-command",
        )
        repository = TaskRepository(session)
        repository.claim_next_queued("dead-worker")
        stale = (datetime.now(UTC) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        task.status = {**task.status, "heartbeat_at": stale}
        session.commit()
        task_id = task.id

    worker = LocalTaskWorker(
        session_factory=session_factory,
        executor_registry=registry,
        worker_id="replacement-worker",
    )
    assert worker.recover_orphaned(stale_after_seconds=300) == 1

    with session_factory() as session:
        loaded = TaskRepository(session).require(task_id)
        assert loaded.phase == "queued"
        assert loaded.status["recovered_from_worker"] == "dead-worker"
        assert loaded.status["worker_id"] is None
