from __future__ import annotations

from app.executors.ansible import AnsibleExecutor
from app.executors.base import Executor


class ExecutorRegistry:
    """Registry for runtime executor implementations."""

    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}

    def register(self, executor: Executor) -> None:
        executor_type = executor.executor_type.strip().lower()
        if not executor_type:
            raise ValueError("executor_type must not be empty")
        self._executors[executor_type] = executor

    def get(self, executor_type: str) -> Executor:
        key = executor_type.strip().lower()
        try:
            return self._executors[key]
        except KeyError as exc:
            available = ", ".join(sorted(self._executors)) or "none"
            raise ValueError(
                f"unknown executor_type={executor_type!r}; available={available}"
            ) from exc

    def list_types(self) -> list[str]:
        return sorted(self._executors)


executor_registry = ExecutorRegistry()
executor_registry.register(AnsibleExecutor())
