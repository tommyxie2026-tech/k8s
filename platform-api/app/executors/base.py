from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Executor-neutral description of one runtime task."""

    task_id: str
    action: str
    command_ref: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Normalized result returned by every executor implementation."""

    return_code: int
    stdout: str = ""
    stderr: str = ""
    command: Sequence[str] = field(default_factory=tuple)

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0


class Executor(Protocol):
    """Stable Runtime -> Executor boundary defined by FROZEN-P0-02/P4."""

    executor_type: str

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one task and return a normalized terminal result."""
        ...
