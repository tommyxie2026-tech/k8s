# CPP Compatibility Inventory v1.0

> Status: BASELINE
> Scope: Current API routes, executor call sites, TaskInfo/JobRecord consumers, deprecation and compatibility map
> Related tasks: T0.7, T0.8, T0.9, T0.10

---

## 1. Current API Router Inventory

The current FastAPI application registers:

```text
health
jobs
workflows
clusters
nodepools
storagepools
kubevirt
backup
governance
observability
```

Base path:

```text
/api/v1
```

except the health router.

Migration rule:

```text
No existing route is removed during M0-M3.
New implementations must preserve route compatibility or provide an explicit deprecation response.
```

---

## 2. Executor Call-Site Inventory

Two executor implementations currently exist.

### 2.1 Legacy Core Executor

```text
app.core.executor.PlaybookExecutor
```

Characteristics:

```text
subprocess.Popen
asynchronous process launch
TaskInfo model
core.task_store
pending/running status only
no terminal state collector in current implementation
```

Known router consumers:

```text
backup.py
governance.py
kubevirt.py
observability.py
```

These paths must migrate to:

```text
Router -> WorkflowService
```

or, for explicitly approved simple operations:

```text
Router -> TaskService -> RuntimeService
```

### 2.2 Services Executor

```text
app.services.executor.Executor
```

Characteristics:

```text
subprocess.run
synchronous/blocking execution
JobRecord model
in-memory _JOBS dictionary
captures stdout/stderr directly
```

Known consumers:

```text
clusters.py
nodepools.py
storagepools.py
jobs.py
app.services.workflow.WorkflowEngine
```

These paths must migrate to the canonical Task resource and unified Runtime Plane.

---

## 3. Current Task and Job Model Inventory

### 3.1 Legacy TaskInfo

```text
Identifier: task_id
Statuses:
  pending
  running
  success
  failed
  cancelled
Payload:
  playbook
  command
  return_code
  extra_vars
```

Compatibility risks:

```text
Uses success rather than succeeded
No queued status
No stdout/stderr fields
No workflow_id
No metadata/spec/status contract
```

### 3.2 JobRecord

```text
Identifier: job_id
Statuses:
  queued
  running
  succeeded
  failed
Payload:
  action
  command
  return_code
  stdout
  stderr
```

Compatibility risks:

```text
No cancelled status
No playbook or extra_vars compatibility fields
No workflow_id
No metadata/spec/status contract
In-memory only
```

### 3.3 Canonical Target Task

The canonical Task resource will use:

```text
metadata.id
metadata.kind = Task
metadata.name
metadata.generation
metadata.resource_version
spec.workflow_id
spec.executor_type
spec.command_ref
spec.parameters
status.phase
status.return_code
status.log_path
status.started_at
status.finished_at
```

Canonical terminal phases:

```text
succeeded
failed
cancelled
```

---

## 4. Compatibility Mapping

### 4.1 Identifier Mapping

```text
TaskInfo.task_id -> Task.metadata.id
JobRecord.job_id -> Task.metadata.id
```

Legacy responses keep the old field names during the deprecation window.

### 4.2 Status Mapping

```text
TaskStatus.pending   -> Task.status.phase = pending
TaskStatus.running   -> Task.status.phase = running
TaskStatus.success   -> Task.status.phase = succeeded
TaskStatus.failed    -> Task.status.phase = failed
TaskStatus.cancelled -> Task.status.phase = cancelled

JobStatus.queued     -> Task.status.phase = queued
JobStatus.running    -> Task.status.phase = running
JobStatus.succeeded  -> Task.status.phase = succeeded
JobStatus.failed     -> Task.status.phase = failed
```

### 4.3 Payload Mapping

```text
TaskInfo.playbook       -> Task.spec.command_ref
TaskInfo.extra_vars     -> Task.spec.parameters
TaskInfo.command        -> compatibility-only response field
JobRecord.action        -> Task.metadata.name or Task.spec.action
JobRecord.command       -> compatibility-only response field
JobRecord.stdout/stderr -> referenced by Task.status.log_path or compatibility response
```

---

## 5. Deprecation Policy

### Phase A: Introduce Canonical Task

```text
Add Task resource schema and repository.
Keep existing /jobs and legacy task routes operational.
Adapters translate canonical Task into legacy response shapes.
```

### Phase B: Migrate Internal Consumers

```text
WorkflowEngine uses TaskService.
Routers no longer import either executor implementation.
_JOBS and core.task_store stop being sources of truth.
```

### Phase C: Deprecate Legacy Responses

```text
Mark JobRecord and TaskInfo schemas deprecated in OpenAPI/docs.
Return deprecation headers where practical.
Document canonical /tasks API replacement.
```

### Phase D: Remove Legacy Internals

Removal is allowed only after:

```text
No internal consumer imports legacy schemas.
Compatibility API tests pass.
Upgrade notes are published.
One full release deprecation window has elapsed.
```

---

## 6. Compatibility Constraints

During M0-M3:

```text
1. Existing API routes must remain callable.
2. Existing playbook execution capability must not be removed.
3. New code must not add Router -> Executor imports.
4. Legacy task/job records may be adapted but not silently reinterpreted.
5. Status value changes must be explicit and tested.
6. Workflow persistence migration must include an import path for existing JSON records.
```

---

## 7. Exit Criteria

T0.7-T0.10 are complete when:

```text
API route inventory exists.
Executor call-site inventory exists.
TaskInfo/JobRecord compatibility mapping exists.
Deprecation phases are documented.
Architecture guard prevents new direct executor imports.
```
