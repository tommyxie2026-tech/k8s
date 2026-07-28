import pytest

from app.services.workflow_safety import (
    WorkflowConfirmationError,
    WorkflowSafetyPolicy,
)


def test_non_destructive_workflow_needs_no_confirmation() -> None:
    policy = WorkflowSafetyPolicy()

    decision = policy.require_confirmation(
        {"destructive": False},
        confirm=False,
        confirm_phrase="",
        workflow_name="backup.vm",
    )

    assert decision.destructive is False
    assert decision.required_phrase is None


def test_destructive_workflow_requires_exact_confirmation_phrase() -> None:
    policy = WorkflowSafetyPolicy()

    with pytest.raises(WorkflowConfirmationError, match="confirm=true"):
        policy.require_confirmation(
            {"destructive": True, "confirm_phrase": "RESTORE_VM"},
            confirm=False,
            confirm_phrase="",
            workflow_name="restore.vm",
        )

    with pytest.raises(WorkflowConfirmationError, match="confirm_phrase=RESTORE_VM"):
        policy.require_confirmation(
            {"destructive": True, "confirm_phrase": "RESTORE_VM"},
            confirm=True,
            confirm_phrase="WRONG",
            workflow_name="restore.vm",
        )


def test_destructive_workflow_accepts_valid_confirmation() -> None:
    policy = WorkflowSafetyPolicy()

    decision = policy.require_confirmation(
        {"destructive": True, "confirm_phrase": "RESTORE_VM"},
        confirm=True,
        confirm_phrase="RESTORE_VM",
        workflow_name="restore.vm",
    )

    assert decision.destructive is True
    assert decision.required_phrase == "RESTORE_VM"


def test_destructive_definition_uses_default_confirmation_phrase() -> None:
    policy = WorkflowSafetyPolicy()

    decision = policy.require_confirmation(
        {"destructive": True},
        confirm=True,
        confirm_phrase="CONFIRM",
        workflow_name="dangerous.operation",
    )

    assert decision.required_phrase == "CONFIRM"


def test_destructive_definition_rejects_empty_confirmation_phrase() -> None:
    policy = WorkflowSafetyPolicy()

    with pytest.raises(ValueError, match="non-empty confirm_phrase"):
        policy.evaluate_definition({"destructive": True, "confirm_phrase": "   "})
