from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import TaskPhase
from app.db.session import create_database_engine
from app.runtime.executor import ExecutionRequest, ExecutionResult, ExecutorRegistry
from app.runtime.service import (
    RuntimeService,
    TaskNotExecutableError,
    TaskSubmission,
)


@dataclass
class FakeExecutor:
    executor_type: str = "fake"
    return_code: int = 0
    raise_error: bool = False

    def build_command(self, request: ExecutionRequest) -> list[str]:
        return ["fake", request.command_ref]

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if self.raise_error:
            raise RuntimeError("simulated executor failure")
        return ExecutionResult(
            task_id=request.task_id,
            executor_type=self.executor_type,
            command=self.build_command(request),
            return_code=self.return_code,
            stdout="ok" if self.return_code == 0 else "",
            stderr="" if self.return_code == 0 else "failed",
        )


@pytest.fixture()
def session() -> Session:
    engine = create_database_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    Base.metadata.drop_all(engine)
    engine.dispose()


def _submission() -> TaskSubmission:
    return TaskSubmission(
        name="test-task",
        executor_type="fake",
        command_ref="0092-velero-preflight.yml",
        extra_vars={"check": True},
        timeout_seconds=30,
    )


def test_submit_creates_durable_queued_task(session: Session) -> None:
    service = RuntimeService(session, ExecutorRegistry([FakeExecutor()]))

    task = service.submit(_submission())

    assert task.phase == TaskPhase.queued.value
    assert task.status["phase"] == TaskPhase.queued.value
    assert task.executor_type == "fake"
    assert task.spec["extra_vars"] == {"check": True}
    assert service.tasks.get(task.id) is not None


def test_execute_persists_successful_terminal_state(session: Session) -> None:
    service = RuntimeService(session, ExecutorRegistry([FakeExecutor(return_code=0)]))
    queued = service.submit(_submission())

    completed = service.execute(queued.id)

    assert completed.phase == TaskPhase.succeeded.value
    assert completed.return_code == 0
    assert completed.stdout == "ok"
    assert completed.started_at is not None
    assert completed.finished_at is not None


def test_execute_persists_failed_return_code(session: Session) -> None:
    service = RuntimeService(session, ExecutorRegistry([FakeExecutor(return_code=2)]))
    queued = service.submit(_submission())

    completed = service.execute(queued.id)

    assert completed.phase == TaskPhase.failed.value
    assert completed.return_code == 2
    assert completed.stderr == "failed"


def test_executor_exception_is_contained_and_persisted(session: Session) -> None:
    service = RuntimeService(session, ExecutorRegistry([FakeExecutor(raise_error=True)]))
    queued = service.submit(_submission())

    completed = service.execute(queued.id)

    assert completed.phase == TaskPhase.failed.value
    assert completed.return_code == 1
    assert completed.stderr == "simulated executor failure"


def test_terminal_task_cannot_be_cancelled(session: Session) -> None:
    service = RuntimeService(session, ExecutorRegistry([FakeExecutor()]))
    queued = service.submit(_submission())
    completed = service.execute(queued.id)

    with pytest.raises(TaskNotExecutableError):
        service.cancel(completed.id)
