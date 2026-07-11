from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Canonical request passed from Runtime to an Executor implementation."""

    task_id: str
    executor_type: str
    command_ref: str
    extra_vars: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Canonical result returned by Executor implementations."""

    task_id: str
    executor_type: str
    command: list[str]
    return_code: int
    stdout: str
    stderr: str


class Executor(Protocol):
    """Runtime executor boundary frozen by P4.

    Implementations may call Ansible, kubectl, virtctl, helm, terraform or shell,
    but callers must depend on this protocol instead of direct subprocess usage.
    """

    executor_type: str

    def build_command(self, request: ExecutionRequest) -> list[str]: ...

    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...


class UnsupportedExecutorError(ValueError):
    """Raised when the Runtime asks for an unknown executor type."""


class UnsafeCommandRefError(ValueError):
    """Raised when command_ref violates executor safety policy."""


class AnsibleExecutor:
    executor_type = "ansible"

    def __init__(self, project_root: str | None = None) -> None:
        self.project_root = Path(project_root or settings.project_root).resolve()

    @staticmethod
    def _validate_playbook_ref(playbook: str) -> None:
        if not playbook:
            raise UnsafeCommandRefError("playbook reference must not be empty")
        path = Path(playbook)
        if path.is_absolute():
            raise UnsafeCommandRefError("playbook reference must be relative")
        if ".." in path.parts:
            raise UnsafeCommandRefError("playbook reference must not traverse parent directories")
        if not playbook.endswith((".yml", ".yaml")):
            raise UnsafeCommandRefError("playbook reference must be a YAML file")

    def build_command(self, request: ExecutionRequest) -> list[str]:
        self._validate_playbook_ref(request.command_ref)
        cmd = [settings.ansible_playbook_bin, "-i", settings.inventory, request.command_ref]
        for key, value in request.extra_vars.items():
            if value is None:
                continue
            cmd.extend(["-e", f"{key}={value}"])
        return cmd

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        command = self.build_command(request)
        proc = subprocess.run(
            command,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=request.timeout_seconds,
            check=False,
        )
        return ExecutionResult(
            task_id=request.task_id,
            executor_type=self.executor_type,
            command=command,
            return_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )


class NotImplementedExecutor:
    def __init__(self, executor_type: str) -> None:
        self.executor_type = executor_type

    def build_command(self, request: ExecutionRequest) -> list[str]:
        raise UnsupportedExecutorError(f"executor {request.executor_type} is not implemented yet")

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        raise UnsupportedExecutorError(f"executor {request.executor_type} is not implemented yet")


class ExecutorRegistry:
    def __init__(self, executors: list[Executor] | None = None) -> None:
        self._executors: dict[str, Executor] = {}
        for executor in executors or []:
            self.register(executor)

    def register(self, executor: Executor) -> None:
        self._executors[executor.executor_type] = executor

    def get(self, executor_type: str) -> Executor:
        executor = self._executors.get(executor_type)
        if executor is None:
            raise UnsupportedExecutorError(f"unknown executor type: {executor_type}")
        return executor

    def supported_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))


def default_executor_registry() -> ExecutorRegistry:
    registry = ExecutorRegistry([AnsibleExecutor()])
    # Interface stubs required by M2; they are intentionally not executable yet.
    for executor_type in ("kubectl", "virtctl", "helm", "terraform", "shell"):
        registry.register(NotImplementedExecutor(executor_type))
    return registry
