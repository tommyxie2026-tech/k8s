import pytest

from app.services.workflow_compensation import (
    CompensationAction,
    CompensationPolicy,
    CompensatableStep,
    InvalidCompensationDefinition,
    build_compensation_plan,
)


def _action(name: str) -> CompensationAction:
    return CompensationAction(
        action=name,
        executor_type="ansible",
        command_ref=f"playbooks/{name}.yml",
        input={"confirm": True},
    )


def test_compensation_plan_runs_successful_steps_in_reverse_order() -> None:
    steps = [
        CompensatableStep(
            name="create-volume",
            position=0,
            phase="succeeded",
            policy=CompensationPolicy.on_failure,
            compensation=_action("delete-volume"),
        ),
        CompensatableStep(
            name="create-vm",
            position=1,
            phase="succeeded",
            policy=CompensationPolicy.on_failure,
            compensation=_action("delete-vm"),
        ),
    ]

    plan = build_compensation_plan(steps, workflow_failed=True)

    assert [item.step_name for item in plan] == ["create-vm", "create-volume"]
    assert [item.action.action for item in plan] == ["delete-vm", "delete-volume"]


def test_compensation_plan_excludes_failed_and_pending_steps() -> None:
    steps = [
        CompensatableStep(
            name="completed",
            position=0,
            phase="succeeded",
            policy=CompensationPolicy.on_failure,
            compensation=_action("undo-completed"),
        ),
        CompensatableStep(
            name="failed",
            position=1,
            phase="failed",
            policy=CompensationPolicy.on_failure,
            compensation=_action("undo-failed"),
        ),
        CompensatableStep(name="pending", position=2, phase="pending"),
    ]

    plan = build_compensation_plan(steps, workflow_failed=True)

    assert [item.step_name for item in plan] == ["completed"]


def test_on_failure_policy_is_not_planned_for_successful_workflow() -> None:
    step = CompensatableStep(
        name="create-resource",
        position=0,
        phase="succeeded",
        policy=CompensationPolicy.on_failure,
        compensation=_action("delete-resource"),
    )

    assert build_compensation_plan([step], workflow_failed=False) == []


def test_always_policy_is_planned_even_without_workflow_failure() -> None:
    step = CompensatableStep(
        name="temporary-lock",
        position=0,
        phase="succeeded",
        policy=CompensationPolicy.always,
        compensation=_action("release-lock"),
    )

    plan = build_compensation_plan([step], workflow_failed=False)

    assert [item.action.action for item in plan] == ["release-lock"]


def test_compensation_requires_action_when_policy_is_enabled() -> None:
    with pytest.raises(InvalidCompensationDefinition, match="has no compensation action"):
        CompensatableStep(
            name="create-resource",
            position=0,
            phase="succeeded",
            policy=CompensationPolicy.on_failure,
        )


def test_duplicate_step_positions_are_rejected() -> None:
    steps = [
        CompensatableStep(name="first", position=0, phase="succeeded"),
        CompensatableStep(name="second", position=0, phase="succeeded"),
    ]

    with pytest.raises(InvalidCompensationDefinition, match="positions must be unique"):
        build_compensation_plan(steps, workflow_failed=True)
