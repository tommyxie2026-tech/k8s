# CPP Compatibility and Deprecation Map v1.0

> Status: ACTIVE
> Milestone: M0 Engineering Baseline
> Task: T0.10
> Purpose: Preserve compatibility while converging the prototype onto the frozen CPP architecture.

---

## 1. Compatibility Principles

```text
1. Public API compatibility is preserved before internal compatibility.
2. Internal duplicate abstractions may be replaced after adapters exist.
3. No destructive endpoint loses its confirmation requirement.
4. Existing playbooks remain valid execution assets.
5. Deprecated interfaces must have an explicit replacement and removal milestone.
6. New code must use only canonical interfaces.
```

---

## 2. Canonical Target Architecture

```text
Router
  -> ResourceService or WorkflowService or TaskService
    -> Repository / RuntimeService
      -> ExecutorRegistry
        -> AnsibleExecutor / future executors
```

Forbidden for new code:

```text
Router -> app.core.executor
Router -> app.services.executor
Workflow -> subprocess
Router -> subprocess
```

---

## 3. Executor Compatibility Map

### Existing: `app.core.executor.PlaybookExecutor`

Current consumers:

```text
legacy action routers
governance router
observability router
backup router
possibly kubevirt router
```

Current behaviour:

```text
Popen-based asynchronous launch
task_store status
no terminal completion update
```

Target replacement:

```text
TaskService -> RuntimeService -> ExecutorRegistry -> AnsibleExecutor
```

Compatibility status:

```text
DEPRECATED-INTERNAL
```

Migration rule:

```text
Keep importable during M0-M2.
Implement adapter delegating to TaskService once persistence exists.
No new imports allowed.
Remove after all routers migrate and compatibility tests pass.
```

Planned removal:

```text
End of M3
```

---

### Existing: `app.services.executor.Executor`

Current consumers:

```text
WorkflowEngine
jobs router
clusters router
nodepools router
storagepools router
```

Current behaviour:

```text
blocking subprocess.run
process-local _JOBS dictionary
JobRecord response
```

Target replacement:

```text
RuntimeService -> ExecutorRegistry -> AnsibleExecutor
TaskRepository as source of truth
```

Compatibility status:

```text
DEPRECATED-INTERNAL
```

Migration rule:

```text
Replace run_playbook() calls with TaskService.submit().
Workflow must create Task resources rather than JobRecord objects.
Keep get_job/list_jobs through compatibility adapter.
```

Planned removal:

```text
End of M3
```

---

## 4. Task and Job Compatibility Map

### Canonical target: `Task`

Task becomes the only execution resource.

Target identity:

```text
id: UUIDv7-compatible
kind: Task
metadata/spec/status structure
workflow_id optional
executor_type
command_ref
phase
return_code
log_path
```

---

### Existing: `TaskInfo`, `TaskStatus`, `TaskCreateResponse`

Compatibility status:

```text
TEMPORARY-COMPATIBILITY
```

Replacement:

```text
Task resource schema
TaskCreateCompatibilityResponse
```

Migration rule:

```text
Legacy endpoints may continue returning task_id/status/playbook.
Internally the response must be generated from canonical Task.
```

Planned removal:

```text
No earlier than API v2 or one full deprecation cycle after M4
```

---

### Existing: `JobRecord`, `JobStatus`

Compatibility status:

```text
DEPRECATED-PUBLIC-ALIAS
```

Replacement:

```text
Task resource
```

Migration rule:

```text
/api/v1/jobs remains temporarily available.
It reads canonical Task records and maps them to the legacy Job response.
New documentation uses /api/v1/tasks.
Responses include deprecation headers once M4 lands.
```

Planned removal:

```text
API v2, not during V2.0 v1 API lifetime
```

---

## 5. Workflow Compatibility Map

### Existing canonical route

```text
POST /api/v1/workflows
GET /api/v1/workflows
GET /api/v1/workflows/{workflow_id}
```

Compatibility status:

```text
SUPPORTED
```

Target behaviour change:

```text
POST returns queued Workflow immediately.
Execution happens asynchronously through RuntimeService.
Response changes only through additive fields within /api/v1.
```

---

### Existing `WorkflowStep` embedded output

Compatibility status:

```text
DEPRECATED-INTERNAL-SHAPE
```

Replacement:

```text
Workflow contains Task references.
Task contains execution status and log reference.
```

Migration rule:

```text
During M3, keep optional embedded step summaries.
Do not return unbounded stdout/stderr in workflow list responses.
Add /workflows/{id}/tasks and /tasks/{id}/logs.
```

---

### Existing hardcoded `WORKFLOW_TEMPLATES`

Compatibility status:

```text
SUPPORTED-PROTOTYPE
```

Replacement:

```text
Versioned WorkflowTemplate registry
```

Migration rule:

```text
Existing names remain stable:
governance.full_check
backup.vm
restore.vm
observability.preflight
```

---

## 6. Router Compatibility Map

### Health

```text
/health
```

Status: supported; no breaking change.

### Jobs

```text
/api/v1/jobs
```

Status: deprecated alias for Tasks after M2.

### Workflows

```text
/api/v1/workflows
```

Status: canonical and supported.

### Clusters, NodePools, StoragePools, KubeVirt, Backup, Governance, Observability

Current status:

```text
action-oriented prototype routes
```

Target:

```text
resource APIs plus workflow action adapters
```

Migration rule:

```text
Read endpoints migrate to ResourceService.
Mutation/action endpoints become thin adapters that create Workflows or Tasks.
Existing route paths remain during V2.0 where practical.
```

---

## 7. Persistence Compatibility Map

### Existing `_JOBS` memory dictionary

Status:

```text
REMOVE
```

Replacement:

```text
TaskRepository
```

Removal milestone:

```text
M2
```

### Existing JSON workflow files

Status:

```text
MIGRATE
```

Replacement:

```text
WorkflowRepository
```

Migration requirement:

```text
Provide one-time importer for existing workflow JSON records.
Keep read-only fallback for one compatibility release if needed.
```

Removal milestone:

```text
M3
```

### Existing audit JSONL

Status:

```text
EXPORT-SINK-ONLY
```

Replacement:

```text
AuditEventRepository
```

Migration rule:

```text
Database becomes source of truth.
JSONL may remain as optional export sink.
```

---

## 8. Playbook Compatibility

Existing playbook names and variables remain supported unless explicitly versioned.

Rules:

```text
1. Runtime calls existing playbooks through AnsibleExecutor.
2. Workflow templates preserve playbook mappings.
3. Variable renames require compatibility aliases.
4. Destructive flags and confirmation variables remain mandatory.
5. Playbook syntax checks remain release gates.
```

---

## 9. Deprecation Communication

When M4 API convergence lands, deprecated public routes must emit:

```text
Deprecation: true
Sunset: <future date when decided>
Link: <replacement endpoint>; rel="successor-version"
```

OpenAPI descriptions must mark deprecated operations.

No public endpoint is removed only because the internal implementation changed.

---

## 10. M0 Completion Criteria

T0.10 is complete when:

```text
1. Both executor implementations have a documented replacement.
2. Task and Job compatibility is defined.
3. Workflow compatibility is defined.
4. Router migration rules are defined.
5. Persistence migration rules are defined.
6. Public removal is separated from internal removal.
```

Status:

```text
COMPLETE
```

Next implementation tasks:

```text
T0.1 Add pytest baseline
T0.2 Add Ruff configuration
T0.3 Add type-check baseline
T0.4 Add CI workflow
T0.5 Add startup smoke test
T0.6 Add architecture dependency test
```
