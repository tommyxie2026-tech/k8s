from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class WorkflowPhase(StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class WorkflowStepPhase(StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"


class InvalidWorkflowTransition(ValueError):
    pass


class InvalidWorkflowDefinition(ValueError):
    pass


WORKFLOW_TRANSITIONS: dict[WorkflowPhase, set[WorkflowPhase]] = {
    WorkflowPhase.pending: {WorkflowPhase.queued, WorkflowPhase.cancelled},
    WorkflowPhase.queued: {WorkflowPhase.running, WorkflowPhase.cancelled},
    WorkflowPhase.running: {
        WorkflowPhase.succeeded,
        WorkflowPhase.failed,
        WorkflowPhase.cancelled,
    },
    WorkflowPhase.succeeded: set(),
    WorkflowPhase.failed: set(),
    WorkflowPhase.cancelled: set(),
}

STEP_TRANSITIONS: dict[WorkflowStepPhase, set[WorkflowStepPhase]] = {
    WorkflowStepPhase.pending: {
        WorkflowStepPhase.queued,
        WorkflowStepPhase.skipped,
        WorkflowStepPhase.cancelled,
    },
    WorkflowStepPhase.queued: {
        WorkflowStepPhase.running,
        WorkflowStepPhase.cancelled,
    },
    WorkflowStepPhase.running: {
        WorkflowStepPhase.succeeded,
        WorkflowStepPhase.failed,
        WorkflowStepPhase.cancelled,
    },
    WorkflowStepPhase.succeeded: set(),
    WorkflowStepPhase.failed: set(),
    WorkflowStepPhase.skipped: set(),
    WorkflowStepPhase.cancelled: set(),
}


@dataclass(frozen=True)
class StepState:
    name: str
    phase: WorkflowStepPhase
    depends_on: tuple[str, ...] = ()


def transition_workflow(current: str, target: str) -> WorkflowPhase:
    current_phase = WorkflowPhase(current)
    target_phase = WorkflowPhase(target)
    if target_phase not in WORKFLOW_TRANSITIONS[current_phase]:
        raise InvalidWorkflowTransition(
            f"workflow cannot transition from {current_phase.value} to {target_phase.value}"
        )
    return target_phase


def transition_step(current: str, target: str) -> WorkflowStepPhase:
    current_phase = WorkflowStepPhase(current)
    target_phase = WorkflowStepPhase(target)
    if target_phase not in STEP_TRANSITIONS[current_phase]:
        raise InvalidWorkflowTransition(
            f"workflow step cannot transition from {current_phase.value} to {target_phase.value}"
        )
    return target_phase


def validate_step_dependencies(steps: Iterable[StepState]) -> None:
    step_list = list(steps)
    names = [step.name for step in step_list]
    if len(names) != len(set(names)):
        raise InvalidWorkflowDefinition("workflow step names must be unique")

    known = set(names)
    graph = {step.name: set(step.depends_on) for step in step_list}
    for name, dependencies in graph.items():
        unknown = dependencies - known
        if unknown:
            raise InvalidWorkflowDefinition(
                f"step {name} depends on unknown steps: {sorted(unknown)}"
            )
        if name in dependencies:
            raise InvalidWorkflowDefinition(f"step {name} cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise InvalidWorkflowDefinition("workflow dependency graph contains a cycle")
        if name in visited:
            return
        visiting.add(name)
        for dependency in graph[name]:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    for name in names:
        visit(name)


def ready_steps(steps: Iterable[StepState]) -> list[str]:
    step_list = list(steps)
    validate_step_dependencies(step_list)
    by_name = {step.name: step for step in step_list}
    ready: list[str] = []
    for step in step_list:
        if step.phase is not WorkflowStepPhase.pending:
            continue
        if all(
            by_name[dependency].phase is WorkflowStepPhase.succeeded
            for dependency in step.depends_on
        ):
            ready.append(step.name)
    return ready


def workflow_phase_from_steps(steps: Iterable[StepState]) -> WorkflowPhase:
    phases = [step.phase for step in steps]
    if not phases:
        return WorkflowPhase.succeeded
    if any(phase is WorkflowStepPhase.failed for phase in phases):
        return WorkflowPhase.failed
    if all(phase is WorkflowStepPhase.succeeded for phase in phases):
        return WorkflowPhase.succeeded
    if all(
        phase in {
            WorkflowStepPhase.succeeded,
            WorkflowStepPhase.skipped,
            WorkflowStepPhase.cancelled,
        }
        for phase in phases
    ) and any(phase is WorkflowStepPhase.cancelled for phase in phases):
        return WorkflowPhase.cancelled
    if any(phase is WorkflowStepPhase.running for phase in phases):
        return WorkflowPhase.running
    return WorkflowPhase.queued
