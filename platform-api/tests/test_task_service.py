from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.runtime.executor import AnsibleExecutor, ExecutorRegistry, UnsupportedExecutorError
from app.services.task_service import TaskService


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def test_enqueue_creates_durable_queued_task_without_execution() -> None:
    session = make_session()
    registry = ExecutorRegistry([AnsibleExecutor(project_root=".")])
    service = TaskService(session, executor_registry=registry)

    task = service.enqueue(
        name="cluster-preflight",
        executor_type="ansible",
        command_ref="0000-preflight.yml",
        extra_vars={"check_mode": True},
        timeout_seconds=300,
    )

    loaded = service.require(task.id)
    assert loaded.phase == "queued"
    assert loaded.status == {"phase": "queued"}
    assert loaded.spec["extra_vars"] == {"check_mode": True}
    assert loaded.spec["timeout_seconds"] == 300
    assert loaded.return_code is None
    assert loaded.started_at is None


def test_enqueue_rejects_unknown_executor_before_persisting_task() -> None:
    session = make_session()
    service = TaskService(session, executor_registry=ExecutorRegistry())

    try:
        service.enqueue(
            name="invalid-task",
            executor_type="unknown",
            command_ref="noop",
        )
    except UnsupportedExecutorError:
        pass
    else:
        raise AssertionError("expected UnsupportedExecutorError")


def test_enqueue_rejects_invalid_timeout() -> None:
    session = make_session()
    registry = ExecutorRegistry([AnsibleExecutor(project_root=".")])
    service = TaskService(session, executor_registry=registry)

    try:
        service.enqueue(
            name="invalid-timeout",
            executor_type="ansible",
            command_ref="0000-preflight.yml",
            timeout_seconds=0,
        )
    except ValueError as exc:
        assert "timeout_seconds" in str(exc)
    else:
        raise AssertionError("expected ValueError")
