# FROZEN-P4 Workflow Engine Specification v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P3-API-SPECIFICATION-v1.0
> Scope: CPP V2.0 workflow model, task model, lifecycle, safety, retry, rollback and executor boundary
> Rule: Any incompatible change to workflow lifecycle, task semantics, destructive confirmation or executor boundary must create a new design version and pass review again.

---

## 1. Purpose

This specification freezes the CPP V2.0 Workflow Engine design.

Workflow is the only supported abstraction for complex infrastructure operations.

Examples:

```text
Cluster preflight
Cluster upgrade
Node maintenance
VM backup
VM restore
Storage governance
KubeVirt validation
Velero preflight
```

---

## 2. Core Principle

CPP freezes the following principle:

```text
API creates Workflow.
Workflow creates Tasks.
Runtime executes Tasks.
Executor performs concrete commands.
```

Forbidden:

```text
API -> Executor
Workflow -> kubectl directly
Workflow -> ansible-playbook directly
Plugin -> Executor directly
```

Allowed:

```text
API -> Workflow Service
Workflow Engine -> Runtime Plane
Runtime Plane -> Executor
Executor -> Kubernetes ecosystem
```

---

## 3. Workflow Resource

Workflow is a Resource.

```yaml
Workflow:
  metadata:
    id: string
    kind: Workflow
    name: string
    labels: map[string]string
    annotations: map[string]string
    generation: integer
    resource_version: string
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime|null
  spec:
    cluster_id: string|null
    target_kind: string|null
    target_id: string|null
    workflow_type: string
    destructive: boolean
    confirm_required: boolean
    confirm_phrase: string|null
    params: object
  status:
    phase: pending | queued | running | succeeded | failed | cancelled
    current_task_id: string|null
    started_at: datetime|null
    finished_at: datetime|null
    reason: string|null
```

---

## 4. Task Resource

Task is a Resource and may exist independently for legacy single-action operations.

```yaml
Task:
  metadata:
    id: string
    kind: Task
    name: string
    created_at: datetime
    updated_at: datetime
  spec:
    workflow_id: string|null
    executor_type: ansible | kubectl | virtctl | helm | terraform | shell
    command_ref: string
    args: object
    timeout_seconds: integer|null
  status:
    phase: pending | queued | running | succeeded | failed | cancelled
    return_code: integer|null
    log_path: string|null
    started_at: datetime|null
    finished_at: datetime|null
    reason: string|null
```

---

## 5. Lifecycle

Workflow lifecycle:

```text
pending -> queued -> running -> succeeded
pending -> queued -> running -> failed
pending -> queued -> cancelled
running -> cancelled
```

Task lifecycle:

```text
pending -> queued -> running -> succeeded
pending -> queued -> running -> failed
pending -> queued -> cancelled
running -> cancelled
```

Rules:

```text
1. A Workflow may only succeed when all required Tasks succeed.
2. A Task failure fails the Workflow unless retry or compensation policy applies.
3. Cancellation must be best-effort and auditable.
4. Every lifecycle transition must emit a ResourceEvent.
```

---

## 6. Workflow Template

Workflow templates define ordered task plans.

```yaml
WorkflowTemplate:
  name: string
  workflow_type: string
  destructive: boolean
  confirm_required: boolean
  confirm_phrase: string|null
  params_schema: object
  tasks:
    - name: string
      executor_type: string
      command_ref: string
      args_template: object
```

V2.0 templates must be stored as code or static configuration. Dynamic user-authored workflows are deferred.

---

## 7. Destructive Operation Safety

Destructive operations must be Workflow-based.

Examples:

```text
VM restore
Cluster upgrade
Node drain
Storage class deletion
Backup deletion
```

Rules:

```text
1. destructive=true requires explicit confirmation.
2. A destructive Workflow may require confirm_phrase.
3. Confirmation must be audited.
4. API must not bypass Workflow for destructive operations.
```

---

## 8. Retry Policy

V2.0 supports simple retry policy.

```yaml
retry_policy:
  max_attempts: integer
  backoff_seconds: integer
```

Rules:

```text
1. Retry applies to Task execution, not arbitrary resource mutation.
2. Retried Tasks must preserve previous attempt logs.
3. Retry must emit events.
```

Advanced conditional retry is deferred.

---

## 9. Rollback and Compensation

CPP uses Saga-style compensation.

Rollback is not SQL rollback.

Rules:

```text
1. Compensation must be modeled as explicit Tasks.
2. Compensation failure must be visible.
3. Compensation must not erase original failure history.
4. Rollback plans must be part of Workflow template design.
```

V2.0 may implement rollback for selected workflows only.

---

## 10. Executor Boundary

Executor is an abstraction.

Supported executor types:

```text
ansible
kubectl
virtctl
helm
terraform
shell
```

Ansible is one executor, not the platform core.

Executor responsibilities:

```text
Run concrete command
Capture stdout/stderr
Return return_code
Write logs
Report Task status
```

Executor must not own Workflow status, Resource status or Audit policy.

---

## 11. Events and Audit

Workflow and Task transitions must emit events.

Examples:

```text
WorkflowCreated
WorkflowQueued
WorkflowStarted
WorkflowSucceeded
WorkflowFailed
TaskQueued
TaskStarted
TaskSucceeded
TaskFailed
DestructiveWorkflowConfirmed
```

Audit must record:

```text
actor
action
target
workflow_id
task_id when applicable
result
timestamp
```

---

## 12. Persistence Rules

Workflow and Task are durable resources.

Required persistence:

```text
Workflow metadata/spec/status
Task metadata/spec/status
Task attempts
Log references
Events
Audit records
```

Runtime queues may be transient, but durable Workflow and Task state must survive process restart.

---

## 13. V2.0 Workflow Set

Minimum V2.0 workflows:

```text
cluster.preflight
storage.governance
backup.etcd
backup.vm
restore.vm
velero.preflight
volume.snapshot.check
observability.preflight
```

---

## 14. Deferred

The following are deferred:

```text
User-authored dynamic workflows
Graph/DAG workflows
Distributed queue HA
Advanced approval policy
Long-running human approval steps
Workflow visual designer
```

---

## 15. Frozen Decisions

```text
1. Workflow is a Resource.
2. Task is a Resource and may exist independently.
3. API must create Workflow for complex/destructive operations.
4. Workflow must not directly execute infrastructure commands.
5. Runtime invokes Executor.
6. Executor is abstract; Ansible is only one executor.
7. Saga compensation is the rollback model.
8. Workflow and Task lifecycle transitions must emit events and audit records.
```
