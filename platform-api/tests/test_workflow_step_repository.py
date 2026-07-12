from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.exceptions import ResourceVersionConflictError
from app.db.models import WorkflowStepModel, WorkflowStepPhase
from app.db.repositories import WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository


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


def test_workflow_steps_are_persisted_and_ordered() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    steps = WorkflowStepRepository(session)

    workflow = workflows.create(name="backup.vm")
    second = steps.create(
        workflow_id=workflow.id,
        name="snapshot-check",
        position=1,
        action="backup.vm.snapshot-check",
        command_ref="0094-volume-snapshot-check.yml",
        depends_on=["velero-preflight"],
    )
    first = steps.create(
        workflow_id=workflow.id,
        name="velero-preflight",
        position=0,
        action="backup.vm.velero-preflight",
        command_ref="0092-velero-preflight.yml",
    )
    session.commit()

    loaded = steps.list_for_workflow(workflow.id)

    assert [step.id for step in loaded] == [first.id, second.id]
    assert all(isinstance(step, WorkflowStepModel) for step in loaded)
    assert loaded[1].depends_on == ["velero-preflight"]
    assert loaded[0].phase == WorkflowStepPhase.pending.value


def test_workflow_step_tracks_attempt_and_task() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    steps = WorkflowStepRepository(session)

    workflow = workflows.create(name="restore.vm", destructive=True)
    step = steps.create(
        workflow_id=workflow.id,
        name="vm-restore",
        position=0,
        action="restore.vm.vm-restore",
        command_ref="0096-kubevirt-vm-restore.yml",
        max_attempts=2,
        timeout_seconds=600,
    )

    steps.set_phase(step.id, WorkflowStepPhase.running, task_id="task-1")
    steps.set_phase(step.id, WorkflowStepPhase.succeeded)

    loaded = steps.require(step.id)
    assert loaded.phase == WorkflowStepPhase.succeeded.value
    assert loaded.task_id == "task-1"
    assert loaded.attempt == 1
    assert loaded.started_at is not None
    assert loaded.finished_at is not None


def test_terminal_workflow_step_cannot_return_to_running() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    steps = WorkflowStepRepository(session)

    workflow = workflows.create(name="governance.full_check")
    step = steps.create(
        workflow_id=workflow.id,
        name="capacity",
        position=0,
        action="governance.full_check.capacity",
        command_ref="0077-capacity-planning.yml",
    )

    steps.set_phase(step.id, WorkflowStepPhase.failed, error="capacity check failed")

    try:
        steps.set_phase(step.id, WorkflowStepPhase.running)
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")
