from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import AuditEventModel, ResourceEventModel
from app.db.repositories import TaskRepository, WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository
from app.services.workflow_timeout import WorkflowTimeoutService


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


def _rfc3339(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def test_expire_overdue_step_fails_step_task_and_workflow() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    tasks = TaskRepository(session)
    steps = WorkflowStepRepository(session)

    workflow = workflows.create(name="backup.vm", phase="running")
    task = tasks.create(
        name="snapshot",
        workflow_id=workflow.id,
        executor_type="ansible",
        command_ref="0094-volume-snapshot-check.yml",
        phase="running",
    )
    step = steps.create(
        workflow_id=workflow.id,
        name="snapshot",
        position=0,
        action="backup.vm.snapshot",
        command_ref="0094-volume-snapshot-check.yml",
        timeout_seconds=30,
    )
    steps.set_phase(step.id, "queued")
    steps.set_phase(step.id, "running", task_id=task.id)

    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    step.started_at = _rfc3339(now - timedelta(seconds=31))
    session.commit()

    results = WorkflowTimeoutService(session).expire_overdue(now=now)

    assert len(results) == 1
    assert results[0].workflow_id == workflow.id
    assert results[0].step_id == step.id
    assert results[0].task_id == task.id
    assert steps.require(step.id).phase == "failed"
    assert "timed out after 30 seconds" in (steps.require(step.id).error or "")
    assert tasks.require(task.id).phase == "failed"
    assert tasks.require(task.id).return_code == 124
    assert workflows.require(workflow.id).phase == "failed"

    audit = session.scalars(select(AuditEventModel)).all()
    events = session.scalars(select(ResourceEventModel)).all()
    assert [item.action for item in audit] == ["workflow.step.timed_out"]
    assert [item.event_type for item in events] == ["WorkflowStepTimedOut"]


def test_non_overdue_running_step_is_unchanged() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    tasks = TaskRepository(session)
    steps = WorkflowStepRepository(session)

    workflow = workflows.create(name="backup.vm", phase="running")
    task = tasks.create(
        name="snapshot",
        workflow_id=workflow.id,
        executor_type="ansible",
        command_ref="0094-volume-snapshot-check.yml",
        phase="running",
    )
    step = steps.create(
        workflow_id=workflow.id,
        name="snapshot",
        position=0,
        action="backup.vm.snapshot",
        command_ref="0094-volume-snapshot-check.yml",
        timeout_seconds=30,
    )
    steps.set_phase(step.id, "queued")
    steps.set_phase(step.id, "running", task_id=task.id)

    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    step.started_at = _rfc3339(now - timedelta(seconds=29))
    session.commit()

    results = WorkflowTimeoutService(session).expire_overdue(now=now)

    assert results == []
    assert steps.require(step.id).phase == "running"
    assert tasks.require(task.id).phase == "running"
    assert workflows.require(workflow.id).phase == "running"
    assert not session.scalars(select(AuditEventModel)).all()
    assert not session.scalars(select(ResourceEventModel)).all()


def test_step_timeout_must_be_positive() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm", phase="pending")

    try:
        WorkflowStepRepository(session).create(
            workflow_id=workflow.id,
            name="invalid",
            position=0,
            action="backup.vm.invalid",
            command_ref="noop.yml",
            timeout_seconds=0,
        )
    except ValueError as exc:
        assert str(exc) == "workflow step timeout_seconds must be greater than zero"
    else:
        raise AssertionError("expected timeout validation to reject zero")
