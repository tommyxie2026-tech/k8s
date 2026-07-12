import pytest

from app.services.workflow_state import (
    InvalidWorkflowDefinition,
    InvalidWorkflowTransition,
    StepState,
    WorkflowPhase,
    WorkflowStepPhase,
    ready_steps,
    transition_step,
    transition_workflow,
    validate_step_dependencies,
    workflow_phase_from_steps,
)


def test_workflow_state_machine_accepts_valid_transition() -> None:
    assert transition_workflow("pending", "queued") is WorkflowPhase.queued
    assert transition_workflow("queued", "running") is WorkflowPhase.running
    assert transition_workflow("running", "succeeded") is WorkflowPhase.succeeded


def test_workflow_state_machine_rejects_terminal_transition() -> None:
    with pytest.raises(InvalidWorkflowTransition):
        transition_workflow("succeeded", "running")


def test_step_state_machine_requires_queue_before_running() -> None:
    with pytest.raises(InvalidWorkflowTransition):
        transition_step("pending", "running")

    assert transition_step("pending", "queued") is WorkflowStepPhase.queued
    assert transition_step("queued", "running") is WorkflowStepPhase.running


def test_dependency_validation_rejects_unknown_and_cycles() -> None:
    with pytest.raises(InvalidWorkflowDefinition):
        validate_step_dependencies(
            [StepState("restore", WorkflowStepPhase.pending, ("missing",))]
        )

    with pytest.raises(InvalidWorkflowDefinition):
        validate_step_dependencies(
            [
                StepState("a", WorkflowStepPhase.pending, ("b",)),
                StepState("b", WorkflowStepPhase.pending, ("a",)),
            ]
        )


def test_ready_steps_only_returns_satisfied_dependencies() -> None:
    steps = [
        StepState("preflight", WorkflowStepPhase.succeeded),
        StepState("restore", WorkflowStepPhase.pending, ("preflight",)),
        StepState("verify", WorkflowStepPhase.pending, ("restore",)),
    ]

    assert ready_steps(steps) == ["restore"]


def test_failed_step_propagates_failed_workflow_phase() -> None:
    steps = [
        StepState("preflight", WorkflowStepPhase.succeeded),
        StepState("restore", WorkflowStepPhase.failed, ("preflight",)),
        StepState("verify", WorkflowStepPhase.pending, ("restore",)),
    ]

    assert workflow_phase_from_steps(steps) is WorkflowPhase.failed
