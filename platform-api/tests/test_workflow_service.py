from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.exceptions import ResourceVersionConflictError
from app.services.workflow_service import WorkflowService


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


def _steps() -> list[dict[str, object]]:
    return [
        {
            "name": "preflight",
            "action": "backup.preflight",
            "executor_type": "ansible",
            "command_ref": "0092-velero-preflight.yml",
        },
        {
            "name": "backup",
            "action": "backup.execute",
            "executor_type": "ansible",
            "command_ref": "0095-kubevirt-vm-backup.yml",
            "depends_on": ["preflight"],
        },
    ]


def test_create_persists_workflow_and_ordered_steps(session: Session) -> None:
    service = WorkflowService(session)

    workflow, steps = service.create(name="backup.vm", steps=_steps())

    assert workflow.phase == "pending"
    assert workflow.status["phase"] == "pending"
    assert [step.name for step in steps] == ["preflight", "backup"]
    assert [step.position for step in steps] == [0, 1]
    assert service.get(workflow.id) is not None
    assert [step.name for step in service.list_steps(workflow.id)] == ["preflight", "backup"]


def test_step_dependencies_must_reference_previous_steps(session: Session) -> None:
    service = WorkflowService(session)

    with pytest.raises(ValueError, match="unknown or forward dependencies"):
        service.create(
            name="invalid",
            steps=[
                {
                    "name": "backup",
                    "command_ref": "0095-kubevirt-vm-backup.yml",
                    "depends_on": ["preflight"],
                },
                {
                    "name": "preflight",
                    "command_ref": "0092-velero-preflight.yml",
                },
            ],
        )


def test_workflow_state_machine_and_dependency_enforcement(session: Session) -> None:
    service = WorkflowService(session)
    workflow, steps = service.create(name="backup.vm", steps=_steps())

    service.queue(workflow.id)
    service.start(workflow.id)

    with pytest.raises(ResourceVersionConflictError, match="unsatisfied dependencies"):
        service.mark_step_running(workflow.id, steps[1].id, "task-backup")

    service.mark_step_running(workflow.id, steps[0].id, "task-preflight")
    service.mark_step_succeeded(workflow.id, steps[0].id)
    service.mark_step_running(workflow.id, steps[1].id, "task-backup")
    service.mark_step_succeeded(workflow.id, steps[1].id)

    completed = service.get(workflow.id)
    assert completed is not None
    assert completed.phase == "succeeded"
    assert completed.status["completed_steps"] == 2


def test_step_failure_propagates_to_workflow(session: Session) -> None:
    service = WorkflowService(session)
    workflow, steps = service.create(name="backup.vm", steps=_steps())
    service.queue(workflow.id)
    service.start(workflow.id)
    service.mark_step_running(workflow.id, steps[0].id, "task-preflight")

    failed_step = service.mark_step_failed(
        workflow.id,
        steps[0].id,
        error="preflight failed",
    )

    failed_workflow = service.get(workflow.id)
    assert failed_step.phase == "failed"
    assert failed_workflow is not None
    assert failed_workflow.phase == "failed"
    assert failed_workflow.status["failed_step"] == "preflight"
    assert failed_workflow.status["error"] == "preflight failed"


def test_terminal_workflow_rejects_invalid_transition(session: Session) -> None:
    service = WorkflowService(session)
    workflow, steps = service.create(name="single", steps=[_steps()[0]])
    service.queue(workflow.id)
    service.start(workflow.id)
    service.mark_step_running(workflow.id, steps[0].id, "task-one")
    service.mark_step_succeeded(workflow.id, steps[0].id)

    with pytest.raises(ResourceVersionConflictError, match="invalid workflow transition"):
        service.transition(workflow.id, "running")
