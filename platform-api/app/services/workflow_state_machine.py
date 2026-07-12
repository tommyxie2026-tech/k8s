from __future__ import annotations

from dataclasses import dataclass

from app.db.exceptions import ResourceVersionConflictError


WORKFLOW_TERMINAL_PHASES = {"succeeded", "failed", "cancelled"}
STEP_TERMINAL_PHASES = {"succeeded", "failed", "skipped", "cancelled"}

WORKFLOW_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"queued", "cancelled"},
    "queued": {"running", "cancelled", "failed"},
    "running": {"succeeded", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}

STEP_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"queued", "skipped", "cancelled"},
    "queued": {"running", "skipped", "cancelled", "failed"},
    "running": {"succeeded", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "skipped": set(),
    "cancelled": set(),
}


@dataclass(frozen=True)
class TransitionDecision:
    current: str
    requested: str
    allowed: bool


class WorkflowStateMachine:
    @staticmethod
    def can_transition(current: str, requested: str) -> bool:
        return requested in WORKFLOW_TRANSITIONS.get(current, set())

    @classmethod
    def ensure_transition(cls, current: str, requested: str) -> None:
        if current == requested:
            return
        if not cls.can_transition(current, requested):
            raise ResourceVersionConflictError(
                f"invalid workflow transition: {current} -> {requested}"
            )


class WorkflowStepStateMachine:
    @staticmethod
    def can_transition(current: str, requested: str) -> bool:
        return requested in STEP_TRANSITIONS.get(current, set())

    @classmethod
    def ensure_transition(cls, current: str, requested: str) -> None:
        if current == requested:
            return
        if not cls.can_transition(current, requested):
            raise ResourceVersionConflictError(
                f"invalid workflow step transition: {current} -> {requested}"
            )
