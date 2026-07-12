from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.exceptions import ResourceVersionConflictError
from app.db.models import WorkflowStepPhase
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


def test_workflow_steps_are_persisted_in_position_order() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm")
    steps = WorkflowStepRepository(session)

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
    assert loaded[1].depends_on == ["velero-preflight"]


def test_running_step_binds_task_and_increments_attempt() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm")
    steps = WorkflowStepRepository(session)
    step = steps.create(
        workflow_id=workflow.id,
        name="vm-backup",
        position=0,
        action="backup.vm.vm-backup",
        command_ref="0095-kubevirt-vm-backup.yml",
        max_attempts=2,
        timeout_seconds=300,
    )

    updated = steps.set_phase(
        step.id,
        WorkflowStepPhase.running,
        task_id="task-1",
    )
    session.commit()

    assert updated.phase == "running"
    assert updated.task_id == "task-1"
    assert updated.attempt == 1
    assert updated.started_at is not None


def test_terminal_step_cannot_transition_back_to_running() -> None:
    session = make_session()
    workflow = WorkflowRepository(session).create(name="backup.vm")
    steps = WorkflowStepRepository(session)
    step = steps.create(
        workflow_id=workflow.id,
        name="vm-backup",
        position=0,
        action="backup.vm.vm-backup",
        command_ref="0095-kubevirt-vm-backup.yml",
    )

    steps.set_phase(step.id, WorkflowStepPhase.succeeded)

    try:
        steps.set_phase(step.id, WorkflowStepPhase.running)
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")
