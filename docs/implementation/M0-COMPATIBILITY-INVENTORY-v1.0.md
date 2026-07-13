# M0 Compatibility Inventory v1.0

> Status: COMPLETE
> Milestone: M0 Engineering Baseline
> Tasks: T0.7, T0.8, T0.9, T0.10
> Purpose: Inventory current API, executor, Task/Job compatibility paths before M1/M2 refactoring.

---

## 1. Current API Router Inventory

The FastAPI application currently exposes the following router groups:

```text
health
jobs
workflows
clusters
nodepools
storagepools
kubevirt
backups
governance
observability
```

Current architectural classification:

| Router group | Current role | Target boundary |
|---|---|---|
| health | Read-only application status | API -> HealthService |
| jobs | In-memory JobRecord query | Compatibility API -> TaskService |
| workflows | Workflow creation/query | API -> WorkflowService |
| clusters | Cluster operations and playbook execution | API -> ResourceService / WorkflowService |
| nodepools | NodePool checks and operations | API -> ResourceService / WorkflowService |
| storagepools | Storage checks and operations | API -> ResourceService / WorkflowService |
| kubevirt | VM/KubeVirt operations | API -> ResourceService / WorkflowService |
| backups | Backup and restore operations | API -> WorkflowService |
| governance | Governance playbooks | API -> WorkflowService |
| observability | Observability preflight | API -> WorkflowService |

Rules for migration:

```text
1. Read endpoints move to Resource/Query Services.
2. Complex or multi-step operations move to WorkflowService.
3. Approved simple direct actions move to TaskService.
4. No router may call Executor after M2 completion.
```

---

## 2. Current Executor Inventory

### 2.1 Legacy asynchronous executor

```text
platform-api/app/core/executor.py
class: PlaybookExecutor
public method: submit(playbook, extra_vars)
process model: subprocess.Popen
state model: TaskInfo + task_store
```

Characteristics:

```text
Creates UUIDv4 task_id
Writes process output to task log file
Transitions pending -> running
Does not wait for completion
Does not persist final succeeded/failed state
```

### 2.2 Legacy synchronous executor

```text
platform-api/app/services/executor.py
class: Executor
public method: run_playbook(action, playbook, extra_vars)
process model: subprocess.run
state model: JobRecord + process-local _JOBS dictionary
```

Characteristics:

```text
Creates timestamp-based job_id
Blocks caller until command completes
Captures stdout and stderr in memory
Stores result only in process memory
Loses JobRecord data on restart
```

### 2.3 Target executor model

```text
WorkflowService / TaskService
        -> RuntimeService
          -> ExecutorRegistry
            -> AnsibleExecutor
            -> kubectl Executor
            -> virtctl Executor
            -> future executors
```

There must be one canonical execution request, result and Task resource.

---

## 3. Current Router-to-Executor Call Sites

The architecture dependency test identifies the following transitional router files as existing direct Executor consumers:

```text
backup.py
clusters.py
governance.py
kubevirt.py
nodepools.py
observability.py
storagepools.py
```

These files form the temporary allowlist in `tests/test_architecture.py`.

Migration order:

```text
1. observability.py -> preflight Workflow
2. governance.py -> governance Workflow definitions
3. backup.py -> backup/restore Workflow definitions
4. nodepools.py -> Resource read + maintenance Workflow
5. storagepools.py -> Resource read + storage Workflow
6. kubevirt.py -> VM Resource service + lifecycle Workflows
7. clusters.py -> Cluster Resource service + lifecycle Workflows
```

The order starts with lower-risk, already-workflow-shaped endpoints and leaves Cluster migration until resource persistence is stable.

---

## 4. Current Task and Job Models

### 4.1 TaskInfo path

Used by:

```text
app.core.executor.PlaybookExecutor
app.core.task_store
legacy Task status API paths
```

Known semantics:

```text
task_id
status
playbook
command
extra_vars
log path convention
```

Limitations:

```text
Not the frozen metadata/spec/status Resource model
No durable database repository
No reliable terminal state update
Uses UUIDv4 rather than UUIDv7-compatible public IDs
```

### 4.2 JobRecord path

Used by:

```text
app.services.executor.Executor
app.routers.jobs
app.services.workflow.WorkflowEngine step execution
newer service-oriented routers
```

Known semantics:

```text
job_id
action
status
command
return_code
stdout
stderr
```

Limitations:

```text
Process-local only
Timestamp ID may collide under concurrency
Synchronous execution blocks caller
Duplicates frozen Task resource
```

### 4.3 Canonical target Task

The canonical Task resource will contain:

```yaml
metadata:
  id: UUIDv7-compatible
  kind: Task
  name: string
  generation: integer
  resource_version: string
  created_at: UTC datetime
  updated_at: UTC datetime
  deleted_at: null
spec:
  workflow_id: string|null
  executor_type: string
  action: string
  command_ref: string
  parameters: object
status:
  phase: pending|queued|running|succeeded|failed|cancelled
  return_code: integer|null
  log_path: string|null
  started_at: UTC datetime|null
  finished_at: UTC datetime|null
```

---

## 5. Compatibility and Deprecation Map

| Current component | Transitional treatment | Target removal point |
|---|---|---|
| `app.core.executor.PlaybookExecutor` | Wrap through legacy adapter backed by TaskService | End of M2 |
| `app.services.executor.Executor` | Replace calls with RuntimeService; keep temporary adapter | End of M2 |
| `TaskInfo` | Map to canonical Task compatibility response | Deprecated in M2; removal after one compatibility release |
| `JobRecord` | Map to canonical Task compatibility response | Deprecated in M2; removal after one compatibility release |
| `_JOBS` dictionary | Read-only migration bridge, then remove | M2 |
| file WorkflowStore | Import existing JSON records into WorkflowRepository | M1/M3 |
| JSONL audit log | Retain as optional export sink | M5 |
| direct router executor imports | Temporary explicit allowlist | Remove progressively through M2–M4 |

---

## 6. Compatibility API Rules

During migration:

```text
1. Existing endpoint paths should remain available unless explicitly versioned.
2. Existing Task/Job identifiers remain readable through adapters.
3. New executions create canonical Task resources only.
4. Compatibility responses may project canonical Task into old response shapes.
5. Old in-memory/file records are read-only after migration cutover.
6. Destructive operation semantics must become stricter, never weaker.
```

---

## 7. Deprecation Phases

### Phase A — Introduce

```text
Add database repositories
Add canonical Task
Add RuntimeService and Executor interface
Keep old APIs operational
```

### Phase B — Redirect

```text
Legacy executor methods delegate to TaskService/RuntimeService
Job API reads canonical Task data
Workflow engine creates canonical Tasks
```

### Phase C — Warn

```text
Mark JobRecord and TaskInfo compatibility schemas deprecated
Document replacement Task API
Emit internal deprecation warnings
```

### Phase D — Remove

```text
Delete dual executors
Delete _JOBS
Delete legacy task_store after data/import verification
Remove router allowlist entries
```

Removal requires:

```text
Passing compatibility tests
Upgrade guidance
No active internal consumers
At least one compatibility release unless explicitly approved otherwise
```

---

## 8. M0 Exit Assessment

Completed M0 engineering baseline items:

```text
T0.1 pytest baseline and tests directory
T0.2 Ruff configuration
T0.3 Mypy configuration
T0.4 GitHub Actions CI
T0.5 Health/startup smoke test
T0.6 Router -> Executor architecture dependency guard
T0.7 API route inventory
T0.8 Executor call-site inventory
T0.9 TaskInfo and JobRecord consumer inventory
T0.10 Compatibility and deprecation map
```

M0 can be considered complete once CI confirms the current baseline is green.

Next milestone:

```text
M1 Persistence Foundation
```
