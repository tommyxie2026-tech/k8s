from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings
from app.core.task_store import task_store
from app.schemas.common import TaskCreateResponse, TaskInfo, TaskStatus


class PlaybookExecutor:
    def build_command(self, playbook: str, extra_vars: Dict[str, Any] | None = None) -> list[str]:
        cmd = [settings.ansible_playbook_bin, "-i", settings.inventory, playbook]
        for key, value in (extra_vars or {}).items():
            if value is None:
                continue
            cmd.extend(["-e", f"{key}={value}"])
        return cmd

    def submit(self, playbook: str, extra_vars: Dict[str, Any] | None = None) -> TaskCreateResponse:
        task_id = str(uuid.uuid4())
        command = self.build_command(playbook, extra_vars)
        task = TaskInfo(
            task_id=task_id,
            status=TaskStatus.pending,
            playbook=playbook,
            command=command,
            extra_vars=extra_vars or {},
        )
        task_store.create(task)
        self._spawn(task_id, command)
        return TaskCreateResponse(task_id=task_id, status=TaskStatus.pending, playbook=playbook)

    def _spawn(self, task_id: str, command: list[str]) -> None:
        Path(settings.task_log_dir).mkdir(parents=True, exist_ok=True)
        log_path = Path(settings.task_log_dir) / f"{task_id}.log"
        task_store.update_status(task_id, TaskStatus.running)
        with open(log_path, "ab") as log_file:
            process = subprocess.Popen(
                command,
                cwd=settings.project_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )
        # V1 intentionally does not block. A later worker will update final status.
        # The task status endpoint exposes the command and log path convention.


executor = PlaybookExecutor()
