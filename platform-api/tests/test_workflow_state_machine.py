from app.db.exceptions import ResourceVersionConflictError
from app.services.workflow_state_machine import WorkflowStateMachine, WorkflowStepStateMachine


def test_workflow_state_machine_accepts_valid_lifecycle() -> None:
    WorkflowStateMachine.ensure_transition("pending", "queued")
    WorkflowStateMachine.ensure_transition("queued", "running")
    WorkflowStateMachine.ensure_transition("running", "succeeded")


def test_workflow_state_machine_rejects_skipping_to_success() -> None:
    try:
        WorkflowStateMachine.ensure_transition("pending", "succeeded")
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")


def test_workflow_terminal_state_is_immutable() -> None:
    try:
        WorkflowStateMachine.ensure_transition("failed", "running")
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")


def test_step_state_machine_supports_skip_and_cancel() -> None:
    WorkflowStepStateMachine.ensure_transition("pending", "skipped")
    WorkflowStepStateMachine.ensure_transition("queued", "cancelled")


def test_step_state_machine_rejects_terminal_reentry() -> None:
    try:
        WorkflowStepStateMachine.ensure_transition("succeeded", "running")
    except ResourceVersionConflictError:
        pass
    else:
        raise AssertionError("expected ResourceVersionConflictError")
