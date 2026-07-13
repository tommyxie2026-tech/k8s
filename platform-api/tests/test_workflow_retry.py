from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import AuditEventModel, ResourceEventModel
from app.db.repositories import WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository
from app.services.workflow_retry import WorkflowRetryService


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    return session_factory()


def create_failed_step(session, *, max_attempts: int = 3):
    workflow = WorkflowRepository(session).create(name="backup.vm", phase="failed")
    steps = WorkflowStepRepository(session)
    step = steps.create(
        workflow_id=workflow.id,
        name="snapshot",
        position=0,
        action="backup.vm.snapshot",
        command_ref="0094-volume-snapshot-check.yml",
        max_attempts=max_attempts,
    )
    steps.set_phase(step.id, "queued")
    steps.set_phase(step.id, "running", task_id="task-attempt-1")
    steps.set_phase(step.id, "failed", error="temporary storage error")
    session.commit()
    return workflow, step


def test_plan_retry_persists_backoff_and_failure_history() -> None:
    session = make_session()
    workflow, step = create_failed_step(session)
    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)

    result = WorkflowRetryService(session).plan_retry(
        step.id,
        backoff_seconds=30,
        now=now,
    )

    refreshed = WorkflowStepRepository(session).require(step.id)
    retry_state = refreshed.input["_retry"]
    assert result.workflow_id == workflow.id
    assert result.attempt == 1
    assert result.max_attempts == 3
    assert result.backoff_seconds == 30
    assert result.retry_not_before.endswith("Z")
    assert refreshed.phase == "failed"
    assert retry_state["backoff_seconds"] == 30
    assert retry_state["history"] == [
        {
            "attempt": 1,
            "task_id": "task-attempt-1",
            "error": "temporary storage error",
            "failed_at": refreshed.finished_at,
        }
    ]
    assert WorkflowRepository(session).require(workflow.id).status["retry_pending"] is True
    assert [event.action for event in session.scalars(select(AuditEventModel))] == [
        "workflow.step.retry_planned"
    ]
    assert [event.event_type for event in session.scalars(select(ResourceEventModel))] == [
        "WorkflowStepRetryPlanned"
    ]


def test_release_due_retry_resets_step_for_new_task_attempt() -> None:
    session = make_session()
    workflow, step = create_failed_step(session)
    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    service = WorkflowRetryService(session)
    service.plan_retry(step.id, backoff_seconds=10, now=now)

    assert service.release_due_retries(now=now + timedelta(seconds=9)) == []
    released = service.release_due_retries(now=now + timedelta(seconds=10))

    assert len(released) == 1
    refreshed = WorkflowStepRepository(session).require(step.id)
    refreshed_workflow = WorkflowRepository(session).require(workflow.id)
    assert refreshed.phase == "pending"
    assert refreshed.task_id is None
    assert refreshed.error is None
    assert refreshed.started_at is None
    assert refreshed.finished_at is None
    assert refreshed.attempt == 1
    assert refreshed.input["_retry"]["retry_not_before"] is None
    assert refreshed_workflow.phase == "queued"
    assert refreshed_workflow.status["retry_pending"] is False


def test_retry_is_bounded_by_max_attempts() -> None:
    session = make_session()
    _, step = create_failed_step(session, max_attempts=1)

    with pytest.raises(ValueError, match="retry exhausted"):
        WorkflowRetryService(session).plan_retry(step.id, backoff_seconds=5)


def test_retry_rejects_negative_backoff() -> None:
    session = make_session()
    _, step = create_failed_step(session)

    with pytest.raises(ValueError, match="backoff_seconds must be non-negative"):
        WorkflowRetryService(session).plan_retry(step.id, backoff_seconds=-1)
