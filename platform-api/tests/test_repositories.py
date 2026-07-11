from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.exceptions import ResourceVersionConflictError
from app.db.models import AuditEventModel, ResourceEventModel, TaskModel, WorkflowModel
from app.db.repositories import AuditEventRepository, ResourceEventRepository, TaskRepository, WorkflowRepository


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


def test_workflow_repository_persists_metadata_spec_status() -> None:
    session = make_session()
    repo = WorkflowRepository(session)

    workflow = repo.create(name="backup.vm", spec={"target": "vm-1"})
    session.commit()

    loaded = repo.require(workflow.id)
    assert isinstance(loaded, WorkflowModel)
    assert loaded.kind == "Workflow"
    assert loaded.spec == {"target": "vm-1"}
    assert loaded.status["phase"] == "pending"
    assert loaded.generation == 1
    assert loaded.deleted_at is None


def test_update_spec_increments_generation_and_resource_version() -> None:
    session = make_session()
    repo = WorkflowRepository(session)
    workflow = repo.create(name="restore.vm", spec={"confirm": False})
    original_version = workflow.resource_version

    updated = repo.update_spec(workflow.id, {"confirm": True}, expected_resource_version=original_version)

    assert updated.generation == 2
    assert updated.resource_version != original_version
    assert updated.spec == {"confirm": True}


def test_optimistic_concurrency_rejects_stale_resource_version() -> None:
    session = make_session()
    repo = WorkflowRepository(session)
    workflow = repo.create(name="governance.full_check")

    try:
        repo.update_status(workflow.id, {"phase": "running"}, expected_resource_version="stale")
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")


def test_soft_delete_hides_resource_by_default() -> None:
    session = make_session()
    repo = WorkflowRepository(session)
    workflow = repo.create(name="observability.preflight")

    repo.soft_delete(workflow.id)

    assert repo.get(workflow.id) is None
    assert repo.get(workflow.id, include_deleted=True) is not None


def test_task_repository_terminal_state_is_immutable() -> None:
    session = make_session()
    repo = TaskRepository(session)
    task = repo.create(name="preflight", executor_type="ansible", command_ref="0000-preflight.yml")

    repo.set_phase(task.id, "succeeded", return_code=0)

    try:
        repo.set_phase(task.id, "running")
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")

    loaded = repo.require(task.id)
    assert isinstance(loaded, TaskModel)
    assert loaded.phase == "succeeded"
    assert loaded.return_code == 0


def test_audit_and_resource_events_are_append_only_records() -> None:
    session = make_session()
    audit = AuditEventRepository(session)
    events = ResourceEventRepository(session)

    audit_event = audit.append(action="workflow.created", target_kind="Workflow", result="success")
    resource_event = events.append(
        event_type="WorkflowCreated",
        resource_kind="Workflow",
        resource_id="wf-1",
        payload={"name": "backup.vm"},
    )
    session.commit()

    assert isinstance(audit_event, AuditEventModel)
    assert audit_event.action == "workflow.created"
    assert isinstance(resource_event, ResourceEventModel)
    assert resource_event.payload == {"name": "backup.vm"}
