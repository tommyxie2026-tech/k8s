from __future__ import annotations

import pytest

from app.runtime.executor import (
    AnsibleExecutor,
    ExecutionRequest,
    UnsafeCommandRefError,
    UnsupportedExecutorError,
    default_executor_registry,
)


def test_default_executor_registry_exposes_frozen_executor_types() -> None:
    registry = default_executor_registry()

    assert registry.supported_types() == (
        "ansible",
        "helm",
        "kubectl",
        "shell",
        "terraform",
        "virtctl",
    )


def test_unknown_executor_type_is_rejected() -> None:
    registry = default_executor_registry()

    with pytest.raises(UnsupportedExecutorError):
        registry.get("unknown")


def test_ansible_executor_builds_safe_command() -> None:
    executor = AnsibleExecutor(project_root=".")
    request = ExecutionRequest(
        task_id="task-1",
        executor_type="ansible",
        command_ref="0092-velero-preflight.yml",
        extra_vars={"velero_enabled": True, "skip_none": None},
    )

    command = executor.build_command(request)

    assert command[:3] == ["ansible-playbook", "-i", "inventories/hosts-container.yml"]
    assert "0092-velero-preflight.yml" in command
    assert "velero_enabled=True" in command
    assert not any("skip_none" in item for item in command)


@pytest.mark.parametrize(
    "command_ref",
    ["", "/tmp/unsafe.yml", "../unsafe.yml", "not-a-playbook.txt"],
)
def test_ansible_executor_rejects_unsafe_playbook_refs(command_ref: str) -> None:
    executor = AnsibleExecutor(project_root=".")
    request = ExecutionRequest(task_id="task-1", executor_type="ansible", command_ref=command_ref)

    with pytest.raises(UnsafeCommandRefError):
        executor.build_command(request)
