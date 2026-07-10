from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from app.core.config import settings
from app.executors.base import ExecutionRequest, ExecutionResult


class AnsibleExecutor:
    executor_type = "ansible"

    def __init__(self) -> None:
        self.project_root = Path(settings.project_root).resolve()

    def build_command(self, request: ExecutionRequest) -> list[str]:
        command = [
            settings.ansible_playbook_bin,
            "-i",
            settings.inventory,
            request.command_ref,
        ]
        if request.parameters:
            command.extend(["--extra-vars", json.dumps(dict(request.parameters))])
        return command

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        command = self.build_command(request)
        completed = subprocess.run(
            command,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
        return ExecutionResult(
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            command=tuple(command),
        )
