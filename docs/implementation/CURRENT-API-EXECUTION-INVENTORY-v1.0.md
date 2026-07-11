# Current API and Execution Inventory v1.0

> Status: BASELINE
> Scope: Sprint 1 / T0.7-T0.10
> Purpose: Inventory current API routes, executor call sites, TaskInfo/JobRecord consumers, and compatibility/deprecation mapping before runtime convergence.

---

## 1. API Router Inventory

Current `platform-api/app/main.py` registers the following routers under `/api/v1` except health:

```text
/health
/api/v1/jobs
/api/v1/workflows
/api/v1/clusters
/api/v1/nodepools
/api/v1/storagepools
/api/v1/kubevirt
/api/v1/backups
/api/v1/governance
/api/v1/observability
```

Router files:

```text
app/routers/health.py
app/routers/jobs.py
app/routers/workflows.py
app/routers/clusters.py
app/routers/nodepools.py
app/routers/storagepools.py
app/routers/kubevirt.py
app/routers/backup.py
app/routers/governance.py
app/routers/observability.py
```

---

## 2. Executor Implementations

Current executor implementations:

```text
app.core.executor.PlaybookExecutor
app.services.executor.Executor
```

### 2.1 app.core.executor.PlaybookExecutor

Current behavior:

```text
Generates uuid4 task_id
Builds ansible-playbook command
Persists TaskInfo in app.core.task_store
Starts subprocess.Popen asynchronously
Sets task status to running
Does not update final terminal status
```

Primary risk:

```text
Task may remain running forever after process exits.
```

### 2.2 app.services.executor.Executor

Current behavior:

```text
Generates job-<timestamp> job_id
Stores JobRecord in in-memory _JOBS
Runs ansible-playbook through subprocess.run synchronously
Stores stdout/stderr/return_code in memory
Sets status succeeded or failed
```

Primary risks:

```text
API or workflow request blocks during playbook execution.
Job records are lost on process restart.
```

---

## 3. Executor Call Site Inventory

### 3.1 Legacy direct Task call path

```text
Router -> app.core.executor.executor.submit()
```

Known routers:

```text
backup.py
clusters.py
governance.py
nodepools.py
observability.py
storagepools.py
```

Expected migration:

```text
Router -> WorkflowService
or
Router -> TaskService -> RuntimeService
```

### 3.2 Synchronous Job call path

```text
Router or WorkflowEngine -> app.services.executor.executor.run_playbook()
```

Known consumers:

```text
app.services.workflow.WorkflowEngine
app.routers.jobs
some newer resource routers where run_playbook is used
```

Expected migration:

```text
WorkflowEngine -> WorkflowRepository + TaskRepository
RuntimeService -> ExecutorRegistry -> AnsibleExecutor
```

---

## 4. TaskInfo and JobRecord Consumer Inventory

### 4.1 TaskInfo

Current role:

```text
Legacy task status model for app.core.executor and app.core.task_store.
```

Expected migration:

```text
TaskInfo becomes a compatibility response mapped from canonical Task resource.
```

### 4.2 JobRecord

Current role:

```text
Synchronous in-memory job model for app.services.executor and jobs router.
```

Expected migration:

```text
JobRecord becomes deprecated.
Jobs API becomes compatibility wrapper over TaskRepository.
```

---

## 5. Compatibility and Deprecation Map

| Current concept | Target concept | Migration action |
|---|---|---|
| TaskInfo | Task resource | Compatibility response only |
| task_store | TaskRepository | Replace after M1/M2 |
| JobRecord | Task resource | Compatibility alias |
| _JOBS dict | TaskRepository | Remove after M2 |
| PlaybookExecutor.submit | TaskService.submit | Replace through adapter |
| Executor.run_playbook | RuntimeService.run_task | Replace through executor registry |
| Workflow JSON files | WorkflowRepository | Import then deprecate |
| audit.log JSONL only | AuditEventRepository + optional JSONL sink | Replace after M5 |

---

## 6. Temporary Allowlist

Architecture test currently allows legacy Router -> Executor imports only for known pre-existing routers.

The allowlist must shrink during M2/M3 and eventually become empty.

---

## 7. Migration Order

```text
1. Add repository persistence foundation.
2. Introduce canonical Task resource.
3. Add RuntimeService and Executor protocol.
4. Make legacy TaskInfo and JobRecord read from TaskRepository.
5. Migrate WorkflowEngine to create durable Task records.
6. Remove in-memory _JOBS.
7. Remove direct router executor imports.
8. Remove allowlist from architecture boundary test.
```

---

## 8. Acceptance For T0.7-T0.10

```text
API route inventory documented.
Executor call sites documented.
TaskInfo and JobRecord consumers documented.
Compatibility and deprecation map documented.
Migration order documented.
```
