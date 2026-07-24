import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import AuditEventModel, ResourceEventModel
from app.db.repositories import WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository
from app.services.workflow_resume import WorkflowResumeService


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    return factory()


def create_failed_workflow(session):
    workflow = WorkflowRepository(session).create(name="restore.vm", phase="failed")
    steps = WorkflowStepRepository(session)

    preflight = steps.create(
        workflow_id=workflow.id,
        name="preflight",
        position=0,
        action="restore.vm.preflight",
        command_ref="0092-velero-preflight.yml",
    )
    steps.set_phase(preflight.id, "queued")
    steps.set_phase(preflight.id, "running", task_id="task-preflight")
    steps.set_phase(preflight.id, "succeeded")

    restore = steps.create(
        workflow_id=workflow.id,
        name="restore",
        position=1,
        action="restore.vm.restore",
        command_ref="0096-kubevirt-vm-restore.yml",
    )
    steps.set_phase(restore.id, "queued")
    steps.set_phase(restore.id, "running", task_id="task-restore")
    steps.set_phase(restore.id, "failed", error="restore failed")

    verify = steps.create(
        workflow_id=workflow.id,
        name="verify",
        position=2,
        action="restore.vm.verify",
        command_ref="0092-velero-preflight.yml",
        depends_on=["restore"],
    )
    session.commit()
    return workflow, preflight, restore, verify


def test_resume_preserves_successful_steps_and_resets_failed_path() -> None:
    session = make_session()
    workflow, preflight, restore, verify = create_failed_workflow(session)
    previous_started_at = restore.started_at
    previous_finished_at = restore.finished_at

    result = WorkflowResumeService(session).resume_from_step(workflow.id, restore.id)

    steps = WorkflowStepRepository(session)
    refreshed_workflow = WorkflowRepository(session).require(workflow.id)
    refreshed_preflight = steps.require(preflight.id)
    refreshed_restore = steps.require(restore.id)
    refreshed_verify = steps.require(verify.id)

    assert refreshed_workflow.phase == "queued"
    assert refreshed_workflow.finished_at is None
    assert refreshed_workflow.status["resume_pending"] is True
    assert refreshed_workflow.status["resume_step_id"] == restore.id
    assert refreshed_workflow.status["resume_count"] == 1

    assert refreshed_preflight.phase == "succeeded"
    assert refreshed_preflight.task_id == "task-preflight"

    assert refreshed_restore.phase == "pending"
    assert refreshed_restore.task_id is None
    assert refreshed_restore.error is None
    assert refreshed_restore.started_at is None
    assert refreshed_restore.finished_at is None
    assert refreshed_restore.input["_resume"]["history"] == [
        {
            "phase": "failed",
            "attempt": 1,
            "task_id": "task-restore",
            "error": "restore failed",
            "started_at": previous_started_at,
            "finished_at": previous_finished_at,
            "resumed_at": refreshed_workflow.status["resumed_at"],
        }
    ]

    assert refreshed_verify.phase == "pending"
    assert refreshed_verify.task_id is None
    assert refreshed_verify.input["_resume"]["history"][0]["phase"] == "pending"

    assert result.reset_step_ids == (restore.id, verify.id)
    assert result.preserved_step_ids == (preflight.id,)


def test_resume_persists_audit_and_resource_events() -> None:
    session = make_session()
    workflow, _, restore, _ = create_failed_workflow(session)

    WorkflowResumeService(session).resume_from_step(
        workflow.id,
        restore.id,
        actor_user_id="user-1",
    )

    audit_events = list(session.scalars(select(AuditEventModel)))
    resource_events = list(session.scalars(select(ResourceEventModel)))

    assert [event.action for event in audit_events] == ["workflow.resumed"]
    assert audit_events[0].actor_user_id == "user-1"
    assert audit_events[0].details["resume_step_id"] == restore.id
    assert audit_events[0].details["resume_count"] == 1
    assert [event.event_type for event in resource_events] == ["WorkflowResumed"]
    assert resource_events[0].payload["resume_count"] == 1


def test_resume_requires_failed_workflow() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm", phase="running")
    step = WorkflowStepRepository(session).create(
        workflow_id=workflow.id,
        name="backup",
        position=0,
        action="backup.vm",
        command_ref="0095-kubevirt-vm-backup.yml",
    )
    session.commit()

    with pytest.raises(ValueError, match="requires failed phase"):
        WorkflowResumeService(session).resume_from_step(workflow.id, step.id)


def test_resume_requires_failed_step() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm", phase="failed")
    step = WorkflowStepRepository(session).create(
        workflow_id=workflow.id,
        name="backup",
        position=0,
        action="backup.vm",
        command_ref="0095-kubevirt-vm-backup.yml",
    )
    session.commit()

    with pytest.raises(ValueError, match="step must be failed"):
        WorkflowResumeService(session).resume_from_step(workflow.id, step.id)


def test_resume_rejects_pending_retry() -> None:
    session = make_session()
    workflow, _, restore, _ = create_failed_workflow(session)
    workflow.status = {**workflow.status, "retry_pending": True}
    session.commit()

    with pytest.raises(ValueError, match="retry is pending"):
        WorkflowResumeService(session).resume_from_step(workflow.id, restore.id)


def test_resume_rejects_active_compensation() -> None:
    session = make_session()
    workflow, _, restore, _ = create_failed_workflow(session)
    workflow.status = {**workflow.status, "compensation_phase": "running"}
    session.commit()

    with pytest.raises(ValueError, match="compensation is active"):
        WorkflowResumeService(session).resume_from_step(workflow.id, restore.id)
