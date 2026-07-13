from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable


class CompensationPolicy(StrEnum):
    """Defines whether and how a workflow step participates in compensation."""

    none = "none"
    on_failure = "on_failure"
    always = "always"


class CompensationPhase(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class InvalidCompensationDefinition(ValueError):
    pass


@dataclass(frozen=True)
class CompensationAction:
    """Executor-neutral description of one compensating operation."""

    action: str
    executor_type: str
    command_ref: str
    input: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise InvalidCompensationDefinition("compensation action must not be empty")
        if not self.executor_type.strip():
            raise InvalidCompensationDefinition("compensation executor_type must not be empty")
        if not self.command_ref.strip():
            raise InvalidCompensationDefinition("compensation command_ref must not be empty")


@dataclass(frozen=True)
class CompensatableStep:
    """Minimal workflow-step projection used to build a Saga compensation plan."""

    name: str
    position: int
    phase: str
    policy: CompensationPolicy = CompensationPolicy.none
    compensation: CompensationAction | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidCompensationDefinition("workflow step name must not be empty")
        if self.position < 0:
            raise InvalidCompensationDefinition("workflow step position must be non-negative")
        if self.policy is not CompensationPolicy.none and self.compensation is None:
            raise InvalidCompensationDefinition(
                f"step {self.name} enables compensation but has no compensation action"
            )
        if self.policy is CompensationPolicy.none and self.compensation is not None:
            raise InvalidCompensationDefinition(
                f"step {self.name} defines compensation but policy is none"
            )


@dataclass(frozen=True)
class PlannedCompensation:
    step_name: str
    original_position: int
    action: CompensationAction
    phase: CompensationPhase = CompensationPhase.pending


def build_compensation_plan(
    steps: Iterable[CompensatableStep],
    *,
    workflow_failed: bool,
) -> list[PlannedCompensation]:
    """Build a reverse-order Saga compensation plan.

    Only steps that reached ``succeeded`` are eligible. ``on_failure`` actions are
    included only when the workflow failed, while ``always`` actions are included
    whenever compensation planning is requested.
    """

    step_list = list(steps)
    names = [step.name for step in step_list]
    if len(names) != len(set(names)):
        raise InvalidCompensationDefinition("workflow step names must be unique")

    positions = [step.position for step in step_list]
    if len(positions) != len(set(positions)):
        raise InvalidCompensationDefinition("workflow step positions must be unique")

    eligible: list[CompensatableStep] = []
    for step in step_list:
        if step.phase != "succeeded" or step.compensation is None:
            continue
        if step.policy is CompensationPolicy.always:
            eligible.append(step)
        elif step.policy is CompensationPolicy.on_failure and workflow_failed:
            eligible.append(step)

    eligible.sort(key=lambda step: step.position, reverse=True)
    return [
        PlannedCompensation(
            step_name=step.name,
            original_position=step.position,
            action=step.compensation,
        )
        for step in eligible
    ]
