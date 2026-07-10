# I0-01 Design-to-Code Gap Analysis v1.0

> Status: APPROVED BASELINE
> Version: v1.0
> Scope: Gap analysis between the frozen CPP design baseline and the current repository implementation
> Depends on: FROZEN-P0-01 through FROZEN-P8

---

## 1. Purpose

This document converts the frozen design baseline into an implementation plan.

It identifies:

```text
Current implementation assets
Design mismatches
Technical debt
Priority
Dependencies
Acceptance criteria
Implementation sequence
```

The goal is not to rewrite the entire repository. The goal is to migrate incrementally from the current playbook/API prototype into the frozen CPP product architecture.

---

## 2. Current Implementation Summary

The repository already contains valuable implementation assets:

```text
Ansible playbooks for cluster, storage, KubeVirt, backup and governance
FastAPI-based platform-api
Task and workflow prototypes
File-based workflow and audit persistence
Backup and restore preflight workflows
KubeVirt VM backup and restore workflow definitions
Basic routers for clusters, node pools, storage pools, governance and observability
Syntax-check and playbook validation scripts
```

These assets should be preserved and moved behind the frozen API, Workflow, Runtime and Executor boundaries.

---

## 3. Executive Gap Summary

| Area | Current State | Frozen Target | Severity |
|---|---|---|---|
| Executor | Two incompatible executor implementations | One executor abstraction and registry | P0 |
| Task persistence | Memory/file-based and incomplete lifecycle | Repository-backed durable Task resource | P0 |
| Workflow persistence | JSON files under `/tmp` | Repository-backed Workflow and Task aggregates | P0 |
| API boundary | Several routers submit playbooks directly | API creates resources or workflows only | P0 |
| Resource model | Router-specific request/response objects | Unified metadata/spec/status resources | P0 |
| Database | No frozen repository-backed implementation | SQLite + Alembic + Repository Pattern | P0 |
| Event model | Direct audit file writes | ResourceEvent and AuditEvent append-only repositories | P1 |
| Authentication/RBAC | Not implemented as product boundary | Minimal identity and authorization baseline | P1 |
| Workflow semantics | Synchronous execution in one path, asynchronous in another | Durable queue, worker, task lifecycle | P0 |
| Plugin framework | Design only | Plugin registry and capability interface | P2 |
| Web Console | Not implemented | Resource-first console | P2 |
| CI/acceptance | Playbook syntax checks exist | Full API, workflow, persistence and safety gates | P1 |

---

## 4. P0 Gaps — Must Be Fixed Before Feature Expansion

### GAP-P0-01: Dual Executor Implementations

Current implementation contains two executor paths:

```text
app.core.executor
app.services.executor
```

Observed characteristics:

```text
app.core.executor:
  asynchronous Popen
  task_store integration
  used by older routers

app.services.executor:
  synchronous run_playbook
  in-memory job records
  used by newer workflow code and routers
```

Risk:

```text
Different task semantics
Different status models
Different log handling
Different failure behavior
Inconsistent API responses
No single Runtime boundary
```

Target:

```text
RuntimeService
  -> ExecutorRegistry
       -> AnsibleExecutor
       -> KubectlExecutor
       -> VirtctlExecutor
       -> HelmExecutor
       -> ShellExecutor
```

Implementation decision:

```text
1. Keep Ansible as the first production executor.
2. Introduce a common Executor protocol.
3. Remove direct router dependency on both legacy executors.
4. Preserve compatibility through an adapter during migration.
```

Acceptance criteria:

```text
Only one executor abstraction is imported by Runtime/Worker.
Routers do not import executor modules.
Every execution creates a durable Task record.
All executors return the same result object.
```

---

### GAP-P0-02: API Directly Submits Playbooks

Current routers may call executor submission methods directly.

This violates the frozen boundary:

```text
API -> Workflow Service
Workflow -> Runtime
Runtime -> Executor
```

Target:

```text
Simple read operation:
API -> ResourceService

Mutating or operational action:
API -> WorkflowService -> RuntimeService -> Executor
```

Migration:

```text
1. Mark direct playbook endpoints as legacy.
2. Add workflow-backed replacement endpoints.
3. Keep legacy endpoints temporarily as adapters.
4. Remove direct execution after compatibility period.
```

Acceptance criteria:

```text
No router invokes ansible-playbook, Popen or run_playbook directly.
All destructive actions return workflow_id.
All operational actions are auditable.
```

---

### GAP-P0-03: Missing Durable Persistence Layer

Current state uses:

```text
In-memory dictionaries
JSON workflow files
JSONL audit logs
/tmp task logs
```

Target:

```text
SQLite default
SQLAlchemy data layer
Alembic migrations
Repository interfaces
PostgreSQL-compatible schema
```

Required first repositories:

```text
WorkflowRepository
TaskRepository
AuditEventRepository
ResourceEventRepository
ClusterRepository
```

Acceptance criteria:

```text
Process restart does not lose Workflow or Task state.
Alembic creates the schema from an empty database.
Repositories are the only persistence access path.
SQLite integration tests pass.
No router, workflow or plugin contains SQL.
```

---

### GAP-P0-04: Resource Contract Not Implemented

Current API models are router-specific and do not consistently expose:

```text
metadata
spec
status
```

Target resource shape:

```yaml
metadata:
  id: UUIDv7
  kind: string
  name: string
  labels: {}
  annotations: {}
  generation: integer
  resource_version: string
  created_at: datetime
  updated_at: datetime
  deleted_at: datetime|null
spec: {}
status: {}
```

Implementation order:

```text
Workflow
Task
Cluster
Backup
VM
StoragePool
StorageClass
Node
Plugin
User
```

Acceptance criteria:

```text
Workflow and Task APIs use the common resource contract first.
All new resource APIs use metadata/spec/status.
Spec changes increment generation.
All persisted updates change resource_version.
```

---

### GAP-P0-05: Workflow Engine Is Not Durable or Asynchronous

Current workflow execution is synchronous in the service path and persists between steps using files.

Target:

```text
Workflow submitted
  -> persisted as pending
  -> tasks persisted
  -> queued
  -> worker claims task
  -> executor runs
  -> task status persisted
  -> event emitted
  -> next task scheduled
```

V2.0 implementation choice:

```text
Database-backed queue first
Single worker process supported
Multiple workers later with lease/claim semantics
Redis not required for first implementation
```

Acceptance criteria:

```text
POST workflow returns before full execution completes.
Worker restart can resume pending/running reconciliation.
Terminal Task states are immutable.
Workflow failure stops downstream tasks unless policy says otherwise.
```

---

## 5. P1 Gaps — Required For A Reliable Product Baseline

### GAP-P1-01: Event and Audit Model

Current audit writes JSONL directly.

Target:

```text
AuditEventRepository: append-only security and operation audit
ResourceEventRepository: append-only resource lifecycle events
```

Required event fields:

```text
id
actor
actor_type
action/event_type
target_kind/resource_kind
target_id
workflow_id
task_id
result
request_id
payload/details
created_at
```

Acceptance criteria:

```text
Workflow creation, task start, task finish and destructive rejection emit events.
Audit records cannot be updated through normal repositories.
Audit remains readable after target soft deletion.
```

---

### GAP-P1-02: API Contract Consistency

Current routes use mixed patterns and mixed response types.

Target conventions:

```text
/api/v1/resources...
/api/v1/workflows
/api/v1/tasks
Consistent error envelope
Consistent pagination
Consistent request_id
Optimistic concurrency via resource_version
```

Acceptance criteria:

```text
OpenAPI documents one common error model.
List endpoints use one pagination model.
Mutating endpoints reject stale resource_version.
Legacy endpoints are tagged deprecated.
```

---

### GAP-P1-03: Minimal Authentication and Authorization

Current platform API does not yet implement the frozen enterprise boundary.

V2.0 minimum:

```text
Local development identity
Request actor propagation
Role checks for read/write/destructive actions
Service identity for worker and plugin calls
```

Deferred enterprise features:

```text
OIDC
LDAP
Multi-tenancy
Approval chains
```

Acceptance criteria:

```text
Every mutating request has an actor.
Destructive operations require authorization and explicit confirmation.
Audit records include actor and result.
```

---

### GAP-P1-04: Testing and Release Gates

Existing syntax checks are useful but insufficient.

Required test layers:

```text
Unit tests for repositories and services
SQLite migration tests
API contract tests
Workflow lifecycle tests
Executor adapter tests
Safety confirmation tests
Playbook syntax checks
End-to-end smoke tests
```

Acceptance criteria:

```text
CI blocks merge on unit, migration, API and safety failures.
A clean database can migrate to head.
A sample workflow completes through API -> Worker -> Executor.
```

---

## 6. P2 Gaps — Product Expansion After Core Stabilization

### GAP-P2-01: Plugin Runtime

Design exists, implementation does not.

First implementation:

```text
Plugin manifest
Plugin registry
Capability declaration
Enable/disable lifecycle
Public API client boundary
No direct database access
```

First three plugin targets:

```text
NFS storage
LVM/local storage
Ceph RBD storage
```

---

### GAP-P2-02: Web Console

Implement only after stable resource and workflow APIs.

First screens:

```text
Dashboard
Clusters
Nodes
StoragePools
StorageClasses
VMs
Backups
Workflows
Tasks
Audit
Plugins
```

The first UI milestone must prioritize workflow visibility and safety, not visual complexity.

---

### GAP-P2-03: Multi-Cluster and Edge

These remain future evolution areas.

V2.0 only needs:

```text
Cluster-scoped resource identity
Cluster-aware repositories
Cluster-aware workflow targeting
No global federation implementation yet
```

---

## 7. Compatibility Strategy

Existing playbooks and endpoints must not be removed abruptly.

Migration pattern:

```text
Legacy Router
  -> Compatibility Adapter
     -> WorkflowService
        -> RuntimeService
           -> AnsibleExecutor
```

Compatibility rules:

```text
1. Preserve existing playbook names and inventory variables.
2. Add deprecation headers to old direct-execution endpoints.
3. Keep response translation adapters during one transition release.
4. Do not change destructive confirmation defaults.
5. Do not automate destructive restore beyond frozen safety rules without separate review.
```

---

## 8. Implementation Epics

### EPIC-I1: Persistence Foundation

Tasks:

```text
I1-01 Add SQLAlchemy and Alembic
I1-02 Add database configuration
I1-03 Create common resource model
I1-04 Implement WorkflowRepository
I1-05 Implement TaskRepository
I1-06 Implement AuditEventRepository
I1-07 Implement ResourceEventRepository
I1-08 Add initial migration
I1-09 Add migration and repository tests
```

Exit criteria:

```text
Durable Workflow, Task, AuditEvent and ResourceEvent storage works on SQLite.
```

---

### EPIC-I2: Runtime and Executor Unification

Tasks:

```text
I2-01 Define Executor protocol
I2-02 Define ExecutionRequest and ExecutionResult
I2-03 Implement AnsibleExecutor adapter
I2-04 Add ExecutorRegistry
I2-05 Add RuntimeService
I2-06 Add Task claim/lease logic
I2-07 Add Worker loop
I2-08 Deprecate duplicate executor paths
I2-09 Add executor/runtime tests
```

Exit criteria:

```text
One durable Task can be queued, claimed, executed and completed through AnsibleExecutor.
```

---

### EPIC-I3: Workflow Engine Refactor

Tasks:

```text
I3-01 Persist Workflow before execution
I3-02 Persist Task plan
I3-03 Replace synchronous workflow execution
I3-04 Add retry policy baseline
I3-05 Add failure propagation
I3-06 Add cancellation baseline
I3-07 Add event emission
I3-08 Add restart reconciliation
I3-09 Add workflow lifecycle tests
```

Exit criteria:

```text
Workflow execution survives API process restart and exposes durable status.
```

---

### EPIC-I4: API Resource Alignment

Tasks:

```text
I4-01 Add common resource schemas
I4-02 Add common error envelope
I4-03 Add pagination model
I4-04 Refactor Workflow API
I4-05 Refactor Task API
I4-06 Add Cluster resource API
I4-07 Add optimistic concurrency
I4-08 Add request_id propagation
I4-09 Mark direct playbook endpoints deprecated
```

Exit criteria:

```text
New API paths comply with FROZEN-P3 and no new router directly executes commands.
```

---

### EPIC-I5: Security and Audit Baseline

Tasks:

```text
I5-01 Add ActorContext
I5-02 Add local development authentication
I5-03 Add action-level authorization
I5-04 Enforce destructive confirmation
I5-05 Persist audit events
I5-06 Add denied-operation audit
I5-07 Add security tests
```

Exit criteria:

```text
All mutating operations are authenticated, authorized and audited.
```

---

### EPIC-I6: Resource Migration

Migration order:

```text
Workflow
Task
Cluster
Backup
VM
StoragePool
StorageClass
Node
Plugin
User
```

Each resource migration includes:

```text
Schema
Repository
Service
Router
Events
Tests
Compatibility adapter
```

---

### EPIC-I7: Plugin Foundation

Tasks:

```text
Plugin manifest schema
Plugin registry
Capability query API
Enable/disable workflow
Storage plugin interface
NFS/LVM/Ceph reference plugins
Plugin safety tests
```

---

### EPIC-I8: Web Console

Tasks:

```text
Application shell
Authentication flow
Resource list/detail components
Workflow timeline
Task log viewer
Destructive confirmation UI
Audit view
Plugin view
```

---

## 9. Recommended Milestones

### Milestone M1 — Durable Control Core

Includes:

```text
EPIC-I1
EPIC-I2
Workflow/Task portion of EPIC-I3 and I4
```

Deliverable:

```text
API submits a Workflow.
Worker executes an Ansible Task.
State persists in SQLite.
Logs and events remain after restart.
```

### Milestone M2 — Safe Resource API

Includes:

```text
Complete EPIC-I3
EPIC-I4
EPIC-I5
Cluster and Backup from EPIC-I6
```

Deliverable:

```text
Stable resource API, safety model, audit trail and backup workflows.
```

### Milestone M3 — Infrastructure Resource Coverage

Includes:

```text
VM
StoragePool
StorageClass
Node
Plugin foundation
```

Deliverable:

```text
Core infrastructure resources use common repositories and APIs.
```

### Milestone M4 — Product Experience

Includes:

```text
Plugin reference implementations
Web Console
Full validation gates
Release packaging
```

---

## 10. First Implementation Sprint

The first sprint must not start with Web Console or new infrastructure features.

Sprint goal:

```text
Build the durable Workflow/Task execution spine.
```

Sprint tasks:

```text
1. Add SQLAlchemy/Alembic dependencies.
2. Add database settings and session management.
3. Implement Workflow and Task database models.
4. Implement repositories.
5. Create the initial Alembic migration.
6. Define Executor protocol and AnsibleExecutor adapter.
7. Implement a database-backed worker loop.
8. Refactor one workflow end-to-end as reference.
9. Add integration tests for restart-safe execution.
```

Reference workflow:

```text
governance.full_check
```

Reason:

```text
Non-destructive
Multiple sequential steps
Uses existing playbooks
Good test of workflow, task and executor boundaries
```

---

## 11. Non-Goals For The First Sprint

Do not implement yet:

```text
PostgreSQL HA
Redis queue
OIDC/LDAP
Multi-tenancy
Full plugin isolation
Web Console
Multi-cluster federation
Edge management
Destructive etcd restore automation
```

---

## 12. Definition Of Done For The Gap-Closure Phase

The frozen design-to-code gap is considered closed when:

```text
1. Only one Runtime/Executor path exists.
2. Workflow and Task are durable resources.
3. API does not directly execute infrastructure commands.
4. SQLite schema is managed by Alembic.
5. Repository Pattern is enforced.
6. metadata/spec/status is used by all migrated resources.
7. ResourceEvent and AuditEvent are append-only.
8. Mutating and destructive operations are authorized and audited.
9. Core workflows pass restart and failure tests.
10. CI enforces the P8 validation gates.
```

---

## 13. Immediate Next Task

Start with:

```text
I1-01 Persistence Foundation
```

The first concrete code change should create:

```text
platform-api/app/db/
platform-api/app/models/
platform-api/app/repositories/
platform-api/alembic/
```

and add the minimum dependencies required for SQLAlchemy and Alembic.
