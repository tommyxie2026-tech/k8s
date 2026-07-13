from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import AuditEventModel, ResourceEventModel  # noqa: F401
from app.repositories.audit_event import AuditEventRepository
from app.repositories.resource_event import ResourceEventRepository


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_audit_event_repository_is_append_only_and_queryable() -> None:
    with _session() as session:
        repository = AuditEventRepository(session)

        event = repository.append(
            actor_type="user",
            actor_user_id="user-1",
            action="workflow.create",
            target_kind="Workflow",
            target_id="workflow-1",
            workflow_id="workflow-1",
            request_id="request-1",
            details={"destructive": False},
        )

        stored = repository.get(event.id)
        assert stored is not None
        assert stored.action == "workflow.create"
        assert stored.details == {"destructive": False}
        assert repository.list(workflow_id="workflow-1") == [stored]

        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")
        assert not hasattr(repository, "soft_delete")


def test_resource_event_repository_is_append_only_and_filterable() -> None:
    with _session() as session:
        repository = ResourceEventRepository(session)

        event = repository.append(
            event_type="VMStarted",
            resource_kind="VM",
            resource_id="vm-1",
            workflow_id="workflow-1",
            task_id="task-1",
            generation=2,
            resource_version="version-2",
            payload={"phase": "running"},
        )

        stored = repository.get(event.id)
        assert stored is not None
        assert stored.event_type == "VMStarted"
        assert stored.payload == {"phase": "running"}
        assert repository.list(resource_kind="VM", resource_id="vm-1") == [stored]

        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")
        assert not hasattr(repository, "soft_delete")
