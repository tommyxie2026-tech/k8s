# Design-to-Code Gap Analysis v1.0

> Status: BASELINE
> Scope: CPP V2.0 current implementation versus frozen P0-01 through P8 specifications
> Purpose: Define implementation gaps, priorities, dependencies and acceptance conditions before modifying core code.

---

## 1. Executive Summary

The repository already contains strong automation assets, backup and governance playbooks, an initial FastAPI service, workflow prototypes and frozen product specifications.

The main gap is not feature absence. The main gap is architectural convergence.

Current implementation contains two execution models, two task/job concepts, file and in-memory persistence, mixed API boundaries, synchronous workflow execution and incomplete resource repositories.

The implementation programme must therefore prioritize convergence before adding new features.

---

## 2. Current Strengths

```text
1. Existing Ansible playbooks cover cluster, governance, storage, KubeVirt and backup operations.
2. Platform API already exposes health, job, cluster, node pool, storage pool, KubeVirt, backup, governance and observability routes.
3. Workflow templates already cover governance, VM backup, VM restore and observability preflight.
4. Destructive workflow confirmation exists for VM restore.
5. Workflow and audit file persistence prototypes exist.
6. P0-P8 frozen design baseline is complete.
```

---

## 3. Critical Architecture Gaps

### GAP-001: Duplicate Executor Implementations

Current code has:

```text
app.core.executor.PlaybookExecutor
app.services.executor.Executor
```

Differences:

```text
core.executor: asynchronous Popen, TaskInfo, task_store
services.executor: synchronous subprocess.run, JobRecord, in-memory _JOBS
```

Impact:

```text
Inconsistent execution semantics
Duplicate status models
Different API behaviour
No single Runtime Plane boundary
Difficult persistence migration
```

Required outcome:

```text
One Executor interface
One Task resource model
Executor registry for ansible/kubectl/virtctl/helm/terraform/shell
One persistent TaskRepository
```

Priority: P0 Blocker

---

### GAP-002: Duplicate Task and Job Models

Current implementation exposes both Task and Job concepts.

Impact:

```text
Conflicts with frozen P1 Task resource
Inconsistent identifiers and status fields
Workflow steps consume JobRecord while legacy APIs expose TaskInfo
```

Required outcome:

```text
Task becomes the single execution resource.
Job becomes a compatibility alias or is removed.
All direct and workflow executions produce Task resources.
```

Priority: P0 Blocker

---

### GAP-003: Persistence Does Not Match P2

Current persistence includes:

```text
In-memory job dictionary
File-based workflow JSON
JSONL audit log
Legacy task_store
```

Missing:

```text
Repository interfaces
SQLite database
Alembic migrations
metadata/spec/status storage model
UUIDv7-compatible identifiers
generation/resource_version
soft deletion
```

Required outcome:

```text
SQLAlchemy/SQLModel persistence layer
SQLite default database
Alembic migrations
Repositories for Resource, Workflow, Task, AuditEvent and ResourceEvent
PostgreSQL-compatible schema
```

Priority: P0 Blocker

---

### GAP-004: API Routers Bypass Workflow Boundary

Some routers directly submit playbooks or execute synchronous jobs.

Impact:

```text
Violates P0-02 and P3 boundary
API behaviour differs by route
Destructive safety cannot be applied consistently
Audit coverage is incomplete
```

Required outcome:

```text
Complex operations: API -> WorkflowService
Simple direct operations: API -> TaskService -> Runtime
No router imports executor directly
```

Priority: P0 Blocker

---

### GAP-005: Workflow Execution Is Synchronous

Current WorkflowEngine.create() immediately calls run(), and run() blocks while each playbook completes.

Missing:

```text
Queued execution
Worker ownership
Retry policy
Timeout policy
Cancellation
Resume
Compensation
Approval state
```

Required outcome:

```text
Workflow creation returns immediately.
Worker claims queued workflows/tasks.
Workflow state is persisted before execution.
Retry, timeout and cancellation fields follow P4.
```

Priority: P1

---

### GAP-006: Workflow API Shape Is Not Fully Aligned

Current API uses generic workflow submission by template name.

Potential conflict:

```text
Frozen API requires stable Resource and Workflow contracts.
Earlier design examples suggested dedicated action endpoints.
```

Required outcome:

```text
Keep canonical POST /api/v1/workflows.
Add resource action endpoints only as thin adapters that create workflows.
Return stable Workflow resource shape.
```

Priority: P1

---

### GAP-007: Resource Plane Is Mostly Router Facades

Current cluster, nodepool, storagepool and VM APIs mainly expose playbook actions or hard-coded summaries.

Missing:

```text
ResourceService
ResourceRepository
Persistent Cluster/Node/StoragePool/StorageClass/VM/Backup/Plugin/User resources
metadata/spec/status response shape
optimistic concurrency
```

Required outcome:

```text
Implement frozen P1 resource services and repositories.
Routers expose resources, not playbook implementation details.
```

Priority: P1

---

### GAP-008: Audit Model Is File-Based and Incomplete

Current audit service appends JSON lines.

Missing:

```text
AuditEvent repository
actor/target/workflow/task/request fields
append-only database controls
query API
retention policy
```

Required outcome:

```text
Persistent append-only AuditEvent table
AuditService interface
Request correlation ID
Audit query endpoint
```

Priority: P1

---

### GAP-009: Resource Events Are Missing

Frozen P2 requires ResourceEvent for lifecycle and state transitions.

Required outcome:

```text
ResourceEvent model and repository
Event emission from resource, workflow and task services
Outbox-compatible event transaction design
WebSocket/event projection adapter
```

Priority: P1

---

### GAP-010: Plugin SDK Is Not Implemented

Frozen P5 exists, but current code lacks:

```text
Plugin manifest
Capability registry
Plugin lifecycle service
Plugin API client boundary
Compatibility validation
Plugin security policy
```

Priority: P2

---

### GAP-011: Web Console Is Not Implemented

Frozen P6 defines resource-first UI, but no verified console implementation is present.

Required outcome:

```text
Resource navigation
Cluster/Node/Storage/VM/Backup views
Workflow and Task visibility
Destructive confirmation UX
Audit view
```

Priority: P2

---

### GAP-012: Authentication and Authorization Are Missing

Current Platform API has no complete frozen Identity/RBAC implementation.

Required outcome:

```text
Request identity context
Local development identity provider
RBAC policy interface
Resource/action authorization checks
Audit denied actions
OIDC/LDAP extension boundary
```

Priority: P1 for minimum RBAC, P3 for enterprise identity integrations

---

### GAP-013: CI and Validation Do Not Cover Product Layers

Existing syntax checks validate playbooks, but frozen P7/P8 require broader gates.

Missing:

```text
Python lint/type checks
Unit tests
Repository integration tests
API contract tests
Workflow state-machine tests
Migration tests on SQLite/PostgreSQL
Security and destructive-operation tests
Packaging tests
```

Priority: P0 foundation, expanded through all milestones

---

## 4. Gap Priority Summary

### P0 Blockers

```text
GAP-001 Executor convergence
GAP-002 Task/Job convergence
GAP-003 Persistence foundation
GAP-004 API boundary convergence
GAP-013 Minimum CI gates
```

### P1 Core Product

```text
GAP-005 Async Workflow Runtime
GAP-006 Workflow API alignment
GAP-007 Resource Plane implementation
GAP-008 Audit persistence
GAP-009 Resource Events
GAP-012 Minimum identity and RBAC
```

### P2 Extensibility and UX

```text
GAP-010 Plugin SDK
GAP-011 Web Console
```

---

## 5. Implementation Principles

```text
1. Do not add new direct router-to-executor paths.
2. Preserve existing playbooks as Ansible executor assets.
3. Introduce compatibility adapters before deleting legacy APIs.
4. Every migration must include tests and rollback guidance.
5. Each Epic must satisfy P8 acceptance gates before completion.
6. Frozen specs may not be changed silently to fit current code.
7. Implementation must converge toward one Resource, Workflow and Task model.
```

---

## 6. Exit Criteria For Gap Closure

The design-to-code gap is considered closed when:

```text
1. One executor abstraction exists.
2. Task is the only execution resource.
3. SQLite repositories and Alembic migrations are active.
4. All complex API actions create Workflows.
5. Workflow execution is asynchronous and persistent.
6. Core resources use metadata/spec/status.
7. AuditEvent and ResourceEvent are queryable and append-only.
8. Minimum RBAC protects resource actions.
9. Plugin SDK supports at least one external capability plugin.
10. Web Console exposes core resources and workflow visibility.
11. CI validates API, database, workflow, safety and packaging layers.
```
