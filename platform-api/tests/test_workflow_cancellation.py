from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import AuditEventModel, ResourceEventModel, TaskModel, WorkflowStepModel
from app.db.repositories import TaskRepository, WorkflowRepository
from app.services.workflow_cancellation import WorkflowCancellationService


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


def test_cancel_pending_workflow_cancels_pending_and_queued_work() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    tasks = TaskRepository(session)
    workflow = workflows.create(name="backup.vm", phase="queued")
    pending_task = tasks.create(
        name="preflight",
        workflow_id=workflow.id,
        executor_type="ansible",
        command_ref="0092-velero-preflight.yml",
        phase="pending",
    )
    queued_task = tasks.create(
        name="snapshot",
        workflow_id=workflow.id,
        executor_type="ansible",
        command_ref="0094-volume-snapshot-check.yml",
        phase="queued",
    )
    session.add_all(
        [
            WorkflowStepModel(
                workflow_id=workflow.id,
                name="preflight",
                position=0,
                action="backup.vm.preflight",
                command_ref="0092-velero-preflight.yml",
                phase="pending",
            ),
            WorkflowStepModel(
                workflow_id=workflow.id,
                name="snapshot",
                position=1,
                action="backup.vm.snapshot",
                command_ref="0094-volume-snapshot-check.yml",
                phase="queued",
            ),
        ]
    )
    session.commit()

    result = WorkflowCancellationService(session).request_cancel(
        workflow.id,
        reason="operator requested",
        request_id="req-1",
    )

    assert result.workflow_phase == "cancelled"
    assert set(result.cancelled_task_ids) == {pending_task.id, queued_task.id}
    assert not result.cancellation_requested_task_ids
    assert workflows.require(workflow.id).phase == "cancelled"
    assert tasks.require(pending_task.id).phase == "cancelled"
    assert tasks.require(queued_task.id).phase == "cancelled"
    assert session.scalars(select(AuditEventModel)).all()
    assert session.scalars(select(ResourceEventModel)).all()


def test_cancel_running_workflow_requests_runtime_stop_before_terminal_state() -> None:
    session = make_session()
    workflows = WorkflowRepository(session)
    tasks = TaskRepository(session)
    workflow = workflows.create(name="restore.vm", phase="running")
    running_task = tasks.create(
        name="restore",
        workflow_id=workflow.id,
        executor_type="ansible",
        command_ref="0096-kubevirt-vm-restore.yml",
        phase="running",
    )
    step = WorkflowStepModel(
        workflow_id=workflow.id,
        name="restore",
        position=0,
        action="restore.vm.restore",
        command_ref="0096-kubevirt-vm-restore.yml",
        phase="running",
        task_id=running_task.id,
    )
    session.add(step)
    session.commit()

    service = WorkflowCancellationService(session)
    result = service.request_cancel(workflow.id, reason="stop restore")

    assert result.workflow_phase == "running"
    assert result.cancellation_requested_task_ids == (running_task.id,)
    assert workflows.require(workflow.id).status["cancellation_pending"] is True
    assert tasks.require(running_task.id).status["cancellation_requested"] is True

    tasks.set_phase(running_task.id, "cancelled")
    step.phase = "cancelled"
    session.commit()
    service.finalize_cancel(workflow.id)

    assert workflows.require(workflow.id).phase == "cancelled"
    assert workflows.require(workflow.id).status["cancellation_pending"] is False
