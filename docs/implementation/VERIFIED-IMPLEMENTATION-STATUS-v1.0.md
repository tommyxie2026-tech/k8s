# CPP V2.0 Verified Implementation Status v1.0

> Status: ACTIVE BASELINE
> Purpose: Record implementation capabilities verified against repository code before continuing migration.

---

## 1. M0 Engineering Baseline

Verified complete:

```text
pytest configuration
application health/startup smoke test
architecture guard preventing new Router -> Executor imports
current API and executor inventory
compatibility and deprecation policy
```

Remaining M0 work:

```text
CI lint/type-check workflow verification
formal frozen-spec traceability test
```

---

## 2. M1 Persistence Foundation

Verified complete:

```text
SQLAlchemy 2.x dependency
Alembic dependency
SQLite engine and session lifecycle
common ResourceMixin
metadata/spec/status storage
UUIDv7-compatible IDs
resource_version and generation
soft deletion
optimistic concurrency exception
WorkflowRepository
TaskRepository
AuditEventRepository
ResourceEventRepository
WorkflowStepModel
```

TaskRepository additionally implements:

```text
queued task claim
worker ownership and heartbeat
terminal completion
failure persistence
orphaned running task recovery
```

Remaining M1 verification:

```text
initial Alembic migration execution in CI
PostgreSQL compatibility test
file-based workflow import utility
```

---

## 3. M2 Runtime Convergence

Verified complete:

```text
ExecutionRequest
ExecutionResult
Executor protocol
ExecutorRegistry
AnsibleExecutor
command_ref safety validation
kubectl/virtctl/helm/terraform/shell interface stubs
RuntimeService durable submit
RuntimeService execution boundary
LocalTaskWorker
persistent task logs
worker claim/heartbeat
orphan recovery
```

Remaining M2 convergence:

```text
migrate all legacy Router -> Executor calls
remove in-memory _JOBS implementation
convert legacy jobs API to Task compatibility view
remove old executors after compatibility window
running-process cancellation signalling
```

---

## 4. M3 Workflow Engine

Verified complete foundations:

```text
WorkflowModel
WorkflowStepModel
ordered workflow steps
step dependency field
retry attempt/max_attempts fields
step timeout field
workflow/step state transition helpers
WorkflowStepRepository
persisted retry plan
retry backoff timestamp
retry history
release of due retry
running-step timeout query
```

Critical remaining M3 work:

```text
1. Implement one asynchronous WorkflowOrchestrator service.
2. Persist Workflow and steps atomically from a versioned definition.
3. Queue only dependency-ready steps through RuntimeService.
4. Reconcile Task terminal state back into WorkflowStep state.
5. Queue downstream steps after dependency success.
6. Mark Workflow succeeded/failed/cancelled from durable step state.
7. Replace synchronous app.services.workflow.WorkflowEngine execution path.
8. Migrate /api/v1/workflows router to the asynchronous orchestrator.
9. Add workflow integration tests covering restart and failure recovery.
```

---

## 5. Current Highest-Priority Blocker

The current highest-priority blocker is no longer persistence or Executor abstraction.

It is:

```text
Legacy synchronous WorkflowEngine still bypasses the new durable Runtime Plane.
```

Target boundary:

```text
API
  -> WorkflowService
    -> WorkflowRepository / WorkflowStepRepository
      -> RuntimeService.submit
        -> LocalTaskWorker
          -> ExecutorRegistry
            -> AnsibleExecutor
```

---

## 6. Next Implementation Slice

The next slice is:

```text
M3 / Workflow Orchestration Convergence
```

Tasks:

```text
WF-001 Add versioned WorkflowDefinition schema
WF-002 Add built-in workflow definition catalog
WF-003 Add asynchronous WorkflowOrchestrator.create()
WF-004 Add queue_ready_steps()
WF-005 Add reconcile_task_result()
WF-006 Add workflow terminal-state calculation
WF-007 Add workflow API compatibility adapter
WF-008 Add integration tests
```

Exit criteria:

```text
POST /api/v1/workflows returns a pending/queued workflow without running playbooks.
Worker executes durable Tasks outside the request lifecycle.
Task completion advances WorkflowStep and Workflow state.
A failed step durably fails or retries according to policy.
Existing workflow names remain compatible.
```
