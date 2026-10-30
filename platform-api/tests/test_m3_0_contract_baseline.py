"""M3-0 contract baseline: no live Ansible, Kubernetes or other external commands.

GREEN tests enforce existing safe behavior. Strict XFAIL tests describe CURRENT
gaps against FROZEN-P3/P4 or proposed M3-3 recovery safety. Do not remove xfail
markers until the corresponding implementation and full regression checks pass.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.db.base import Base
from app.db.repositories import TaskRepository
from app.runtime.executor import (
    ExecutionRequest,
    ExecutionResult,
    ExecutorRegistry,
    UnsupportedExecutorError,
)
from app.runtime.service import RuntimeService, TaskSubmission
from app.runtime.worker import LocalTaskWorker
from app.services.workflow_safety import WorkflowConfirmationError
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class RecordingExecutor:
    executor_type = "recording"

    def __init__(self) -> None:
        self.calls: list[ExecutionRequest] = []

    def build_command(self, request: ExecutionRequest) -> list[str]:
        return ["recording", request.command_ref]

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls.append(request)
        return ExecutionResult(
            task_id=request.task_id,
            executor_type=self.executor_type,
            command=self.build_command(request),
            return_code=0,
            stdout="simulated",
            stderr="",
        )


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine, expire_on_commit=False, future=True)
    finally:
        engine.dispose()


def _submission(
    *,
    command_ref: str = "0092-velero-preflight.yml",
    executor_type: str = "recording",
) -> TaskSubmission:
    return TaskSubmission(
        name="m3-contract-check",
        executor_type=executor_type,
        command_ref=command_ref,
        extra_vars={},
        timeout_seconds=30,
    )


def test_cancelled_queued_task_is_not_executed_by_worker(session_factory) -> None:
    """Cancelling a queued Task must block dispatch; no real Executor is used."""
    recorder = RecordingExecutor()
    registry = ExecutorRegistry([recorder])
    with session_factory() as session:
        runtime = RuntimeService(session, registry)
        task = runtime.submit(_submission())
        runtime.cancel(task.id)
        task_id = task.id

    worker = LocalTaskWorker(session_factory=session_factory, executor_registry=registry)
    assert worker.run_once() is None
    assert recorder.calls == []
    with session_factory() as session:
        assert TaskRepository(session).require(task_id).phase == "cancelled"


def test_second_worker_does_not_claim_completed_task(
    session_factory, tmp_path, monkeypatch
) -> None:
    """Sequential claim safety only: this is not a multi-worker race test."""
    from app.core.config import settings

    recorder = RecordingExecutor()
    registry = ExecutorRegistry([recorder])
    monkeypatch.setattr(settings, "task_log_dir", str(tmp_path))
    with session_factory() as session:
        task_id = RuntimeService(session, registry).submit(_submission()).id

    first = LocalTaskWorker(
        session_factory=session_factory,
        executor_registry=registry,
        worker_id="worker-first",
    )
    second = LocalTaskWorker(
        session_factory=session_factory,
        executor_registry=registry,
        worker_id="worker-second",
    )
    assert first.run_once() == task_id
    assert second.run_once() is None
    assert len(recorder.calls) == 1
    with session_factory() as session:
        assert TaskRepository(session).require(task_id).phase == "succeeded"


def test_destructive_workflow_missing_confirmation_rejects_before_dispatch(monkeypatch) -> None:
    """Existing legacy WorkflowSafetyPolicy stops an unconfirmed restore."""
    from app.schemas.workflows import WorkflowCreateRequest
    from app.services import workflow as legacy_workflow

    calls: list[str] = []

    def forbidden_run(*args, **kwargs) -> None:
        calls.append("executor")
        raise AssertionError("the legacy executor must never be called")

    monkeypatch.setattr(legacy_workflow.executor, "run_playbook", forbidden_run)
    monkeypatch.setattr(legacy_workflow, "audit", lambda *args, **kwargs: None)

    with pytest.raises(WorkflowConfirmationError):
        legacy_workflow.WorkflowEngine().create(
            WorkflowCreateRequest(name="restore.vm", confirm=False)
        )
    assert calls == []


@pytest.mark.xfail(
    strict=True,
    reason="M3-0 gap: RuntimeService.execute resolves registry.get outside its exception boundary",
)
def test_unknown_executor_does_not_leave_task_running(session_factory) -> None:
    """An unknown Executor must not leave an indefinitely 'running' Task."""
    registry = ExecutorRegistry([RecordingExecutor()])
    with session_factory() as session:
        runtime = RuntimeService(session, registry)
        task_id = runtime.submit(_submission(executor_type="unknown")).id
        try:
            runtime.execute(task_id)
        except UnsupportedExecutorError:
            pass
        session.expire_all()
        assert TaskRepository(session).require(task_id).phase != "running"


@pytest.mark.xfail(
    strict=True,
    reason="M3-3 candidate: orphaned destructive work must be reconciled before replay",
)
def test_stale_restore_task_is_not_blindly_requeued(session_factory) -> None:
    """A stale heartbeat alone does not establish that a VM restore never ran."""
    with session_factory() as session:
        tasks = TaskRepository(session)
        task = tasks.create(
            name="restore-vm",
            executor_type="recording",
            command_ref="0096-kubevirt-vm-restore.yml",
            spec={"extra_vars": {"vm_restore_apply_confirm": True}},
            phase="queued",
        )
        session.commit()
        tasks.claim_next_queued("disconnected-worker")
        stale_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat().replace(
            "+00:00", "Z"
        )
        task.status = {**task.status, "heartbeat_at": stale_at}
        session.commit()
        task_id = task.id

    worker = LocalTaskWorker(
        session_factory=session_factory,
        executor_registry=ExecutorRegistry([RecordingExecutor()]),
    )
    worker.recover_orphaned(stale_after_seconds=300)
    with session_factory() as session:
        assert TaskRepository(session).require(task_id).phase != "queued"


@pytest.mark.xfail(
    strict=True,
    reason="FROZEN-P3 gap: mounted KubeVirt restore Action API still calls legacy executor",
)
def test_unconfirmed_vm_restore_does_not_submit_legacy_executor(monkeypatch) -> None:
    """Use a spy: this test does not run or schedule a real restore Playbook."""
    from app.routers import kubevirt

    class SubmitSpy:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def submit(self, playbook: str, extra_vars=None):
            self.calls.append(playbook)
            return {"test": "intercepted"}

    spy = SubmitSpy()
    monkeypatch.setattr(kubevirt, "executor", spy)
    request = kubevirt.VMRestoreRequest(name="m3-test-only", confirm=False)
    try:
        kubevirt.restore_vm(request)
    except (HTTPException, PermissionError):
        pass

    assert spy.calls == [], "unconfirmed restore must be denied before any dispatch"


@pytest.mark.xfail(
    strict=True,
    reason="FROZEN-P3 gap: cancel/retry Workflow and read-only Task routes are not all mounted",
)
def test_frozen_workflow_lifecycle_and_task_query_routes_are_mounted() -> None:
    from app.main import app

    actual = {
        (route.path, method)
        for route in app.routes
        for method in (getattr(route, "methods", None) or ())
    }
    frozen = {
        ("/api/v1/workflows", "POST"),
        ("/api/v1/workflows", "GET"),
        ("/api/v1/workflows/{workflow_id}", "GET"),
        ("/api/v1/workflows/{workflow_id}/cancel", "POST"),
        ("/api/v1/workflows/{workflow_id}/retry", "POST"),
        ("/api/v1/tasks", "GET"),
        ("/api/v1/tasks/{task_id}", "GET"),
        ("/api/v1/tasks/{task_id}/logs", "GET"),
    }
    assert not (frozen - actual), f"frozen API routes missing: {sorted(frozen - actual)}"


@pytest.mark.xfail(
    strict=True,
    reason="FROZEN-P4 gap: legacy WorkflowEngine.create synchronously invokes run()",
)
def test_legacy_workflow_creation_does_not_execute_in_request(monkeypatch) -> None:
    """Intercept run() and JSON storage; never execute infrastructure commands."""
    from app.schemas.workflows import WorkflowCreateRequest
    from app.services import workflow as legacy_workflow

    class MemoryWorkflowStore:
        def __init__(self) -> None:
            self.records: dict[str, object] = {}

        def save(self, record):
            self.records[record.workflow_id] = record
            return record

        def get(self, workflow_id: str):
            return self.records.get(workflow_id)

    executed: list[str] = []
    monkeypatch.setattr(legacy_workflow, "workflow_store", MemoryWorkflowStore())
    monkeypatch.setattr(legacy_workflow, "audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        legacy_workflow.WorkflowEngine,
        "run",
        lambda self, workflow_id: executed.append(workflow_id),
    )
    legacy_workflow.WorkflowEngine().create(
        WorkflowCreateRequest(name="observability.preflight")
    )
    assert executed == [], "API submission must only persist and queue a Workflow"
