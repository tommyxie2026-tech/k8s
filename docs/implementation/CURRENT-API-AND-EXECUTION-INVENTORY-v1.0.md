# Current API and Execution Inventory v1.0

> Status: BASELINE
> Scope: Sprint 1 / M0 compatibility inventory
> Related tasks: T0.7, T0.8, T0.9

---

## 1. Purpose

This document inventories the current Platform API routes and execution paths before the M1/M2 refactor.

It is intentionally descriptive, not prescriptive. The target architecture is defined by the frozen P0-P8 specifications and the implementation plan.

---

## 2. API Router Inventory

| Router | Prefix | Current role | Execution boundary |
|---|---|---|---|
| health.py | /health | health probe | no execution |
| jobs.py | /api/v1/jobs | legacy task listing and lookup | uses `app.core.task_store` |
| workflows.py | /api/v1/workflows | workflow create/list/get | uses `app.services.workflow.workflow_engine` |
| clusters.py | /api/v1/clusters | current cluster, preflight, syntax-check | imports `app.core.executor` |
| nodepools.py | /api/v1/nodepools | node-pool operations | imports legacy executor |
| storagepools.py | /api/v1/storagepools | storage governance and snapshot checks | imports legacy executor |
| kubevirt.py | /api/v1/kubevirt | KubeVirt operations | to be migrated/validated |
| backup.py | /api/v1/backups | backup/restore/preflight operations | imports `app.core.executor` |
| governance.py | /api/v1/governance | governance playbook endpoints | imports `app.core.executor` |
| observability.py | /api/v1/observability | observability preflight/install operations | imports legacy executor |

---

## 3. Execution Model Inventory

### 3.1 Legacy asynchronous playbook executor

```text
app.core.executor.PlaybookExecutor
```

Observed behavior:

```text
1. Builds ansible-playbook command.
2. Creates TaskInfo in app.core.task_store.
3. Starts subprocess.Popen.
4. Updates task status to running.
5. Does not wait for completion.
6. Does not persist terminal return code.
```

Current consumers:

```text
backup.py
clusters.py
governance.py
nodepools.py
observability.py
storagepools.py
```

Target migration:

```text
Router -> WorkflowService or TaskService -> RuntimeService -> ExecutorRegistry -> AnsibleExecutor
```

---

### 3.2 Legacy synchronous job executor

```text
app.services.executor.Executor
```

Observed behavior:

```text
1. Builds ansible-playbook command.
2. Creates JobRecord in in-memory _JOBS.
3. Executes subprocess.run synchronously.
4. Captures stdout/stderr.
5. Stores final status in memory.
```

Current consumers:

```text
app.services.workflow.WorkflowEngine
legacy/new service-level callers
```

Target migration:

```text
WorkflowEngine -> RuntimeService -> TaskRepository -> ExecutorRegistry
```

---

### 3.3 File-based workflow persistence

```text
app.services.workflow_store.WorkflowStore
```

Observed behavior:

```text
1. Stores workflow JSON files under task_log_dir/workflows.
2. Loads all workflow files by scanning the directory.
3. Has no database transaction boundary.
4. Has no generation/resource_version.
5. Is not HA-safe.
```

Target migration:

```text
WorkflowRepository backed by SQLite through SQLAlchemy/Alembic
```

---

### 3.4 Legacy task store

```text
app.core.task_store
```

Observed behavior:

```text
1. Stores TaskInfo records for legacy direct playbook submissions.
2. Feeds /api/v1/jobs endpoints.
3. Does not represent frozen P1 Task resource.
```

Target migration:

```text
TaskRepository as the single durable Task resource store
Job endpoints become compatibility views over TaskService
```

---

## 4. P0 Blocker Mapping

| Gap | Current evidence | Required outcome |
|---|---|---|
| Duplicate executors | `app.core.executor` and `app.services.executor` | one Executor protocol and registry |
| Duplicate task/job models | `TaskInfo` and `JobRecord` | one durable Task resource |
| File/in-memory persistence | workflow JSON, `_JOBS`, task_store | SQLite repositories via Alembic |
| Router direct execution | routers importing executors | routers call services only |
| Synchronous Workflow | `WorkflowEngine.create()` immediately runs workflow | queued Workflow + Runtime worker |

---

## 5. Compatibility Policy

During migration, current operational endpoints must remain available unless explicitly deprecated.

Compatibility rules:

```text
1. Keep existing route paths during M0-M3.
2. Add compatibility adapters rather than deleting legacy behaviours immediately.
3. New code must use frozen Resource/Workflow/Task semantics.
4. Direct Router -> Executor imports are technical debt and must not expand.
5. Delete legacy executors only after TaskService and RuntimeService are complete.
```

---

## 6. Immediate Migration Order

```text
1. Add persistence baseline.
2. Introduce canonical TaskRepository.
3. Build RuntimeService and ExecutorRegistry.
4. Migrate workflow execution to RuntimeService.
5. Replace router direct executor calls with WorkflowService/TaskService.
6. Remove legacy executor adapters.
```
