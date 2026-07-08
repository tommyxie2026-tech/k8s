# FROZEN-P2-01 Data Architecture v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> Scope: CPP data architecture and persistence principles
> Rule: Any incompatible change to data categories, resource shape, persistence boundary, transaction model or baseline conventions must create a new design version and pass review again.

---

## 1. Purpose

This frozen specification defines the CPP V2.0 data architecture.

It is the source of truth for later:

```text
P2-02 ER Model
P2-03 Table Schema and Index Design
P2-04 Migration Design
P3 API Specification
P4 Workflow Specification
P8 Test and Validation Specification
```

This document does not define final SQL tables or indexes.

---

## 2. Frozen Data Philosophy

CPP freezes the following principle:

> Data is a product, not a side effect of code.

The authoritative model is the Resource Model from P1. The database is only a persistence backend for resources.

Consequences:

```text
1. API, Workflow, Worker, Plugin and Web UI must use the Resource Model.
2. No module may define private persistent data models that bypass Resource semantics.
3. Storage backend may evolve from SQLite to PostgreSQL or other backends without changing upper-layer architecture.
```

---

## 3. Frozen Data Categories

CPP V2.0 freezes five data categories.

```text
Configuration
Spec
Status
Workflow
Audit
```

### 3.1 Configuration Data

Long-lived platform configuration.

Examples:

```text
Cluster
Node
StoragePool
StorageClass
Plugin
```

### 3.2 Spec Data

Desired state submitted by users, APIs, workflows or plugins through public APIs.

Examples:

```text
VM desired CPU/memory/disks
StorageClass reclaim policy
Backup target and retention
```

### 3.3 Status Data

Observed state reported by runtime, workers, executors, controllers or sync loops.

Examples:

```text
VM running node
Workflow phase
Task return code
StoragePool capacity usage
```

### 3.4 Workflow Data

Durable orchestration state.

Examples:

```text
Workflow
Task
Step output
Approval
Retry
Rollback
```

### 3.5 Audit Data

Append-only operational history.

Examples:

```text
User action
Workflow event
Task event
Security event
Resource change event
```

Audit data must not be modified after creation.

---

## 4. Frozen Resource Shape

All persistent resources must follow the following shape:

```yaml
Resource:
  metadata:
    id: string
    kind: string
    name: string
    labels: map[string]string
    annotations: map[string]string
    generation: integer
    resource_version: string
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime|null
  spec: object
  status: object
```

Rules:

```text
1. metadata is owned by the platform.
2. spec is desired state.
3. status is observed state.
4. spec changes must increment generation.
5. any persisted representation change must update resource_version.
6. deleted_at is used for soft deletion where auditability matters.
```

---

## 5. Frozen Spec / Status Separation

Spec and Status must be separated in model, database and API behavior.

Spec may be changed by:

```text
User
API
Workflow
Plugin through public API
```

Status may be changed by:

```text
Runtime
Worker
Executor
Controller / Sync loop
```

Forbidden:

```text
User directly updates status
Plugin directly updates status without status API
API hides spec and status in one opaque blob
```

---

## 6. Frozen Logical Stores

CPP defines four logical stores:

```text
Resource Store
Workflow Store
Runtime Store
Audit Store
```

### 6.1 Resource Store

Persists resource metadata, spec and status.

### 6.2 Workflow Store

Persists Workflow and Task state.

### 6.3 Runtime Store

Stores ephemeral queue and worker runtime state. It may be in-memory in V2.0 if recovery is possible.

### 6.4 Audit Store

Persists append-only events and audit records.

---

## 7. Frozen Repository Pattern

All database access must follow:

```text
Service -> Repository -> Database
```

Forbidden:

```text
Router -> SQL
Workflow -> SQL
Plugin -> SQL
Executor -> SQL
Worker -> SQL without repository
```

Repository Pattern is required to support SQLite to PostgreSQL migration.

---

## 8. Frozen Transaction Model

CPP uses Saga-style transaction semantics for cross-resource operations.

Infrastructure workflows cannot rely on cross-resource database rollback as the primary recovery mechanism.

Example VM Restore:

```text
Create Workflow
Validate Snapshot
Restore PVC
Restore VM
Verify VM
Mark result
```

Failures must be represented by:

```text
Workflow failure state
Retry
Rollback step
Manual intervention
Resume
```

---

## 9. Frozen Event Model

All important state changes must emit events.

Examples:

```text
ResourceCreated
ResourceUpdated
WorkflowCreated
WorkflowStarted
TaskStarted
TaskSucceeded
TaskFailed
VMBackupStarted
VMBackupFinished
```

Events are consumed by:

```text
Audit
WebSocket
Observability
Notification
Future automation
```

Audit must be event-backed where possible.

---

## 10. Frozen Versioning And Concurrency

All resources must support optimistic concurrency.

Required metadata:

```text
generation
resource_version
```

Rules:

```text
1. generation changes when spec changes.
2. resource_version changes when any persisted representation changes.
3. updates should use resource_version for conflict detection.
4. lost updates must be rejected with conflict semantics.
```

---

## 11. Frozen ID Strategy

CPP should use UUIDv7 for resource IDs.

Reason:

```text
Time sortable
Index friendly
Globally unique
Good for audit and pagination
```

Temporary UUIDv4 usage is allowed only behind a stable ID generation interface.

---

## 12. Frozen Time Strategy

All stored timestamps must use:

```text
UTC
RFC3339 at API boundary
Database timezone-normalized timestamp internally
```

Local timezone conversion belongs to clients and Web Console.

---

## 13. Frozen Deletion Strategy

CPP uses soft deletion where auditability matters.

Required field:

```text
deleted_at
```

Hard deletion is allowed only for ephemeral runtime data and must not violate audit requirements.

---

## 14. Frozen Naming Conventions

Recommended table names:

```text
clusters
nodes
storage_pools
storage_classes
vms
backups
workflows
tasks
plugins
users
events
audit_logs
```

Common fields:

```text
id
created_at
updated_at
deleted_at
generation
resource_version
```

Lifecycle state field:

```text
phase
```

Avoid mixing phase with inconsistent fields such as:

```text
status
state
running
```

---

## 15. Frozen Migration Strategy

All schema changes must be versioned.

Implementation path:

```text
V2.0: SQLite + Alembic
V2.1: PostgreSQL support
V2.2: PostgreSQL HA deployment mode
```

Manual production schema modification is forbidden.

---

## 16. Frozen ADRs

This specification creates the following architecture decisions:

```text
ADR-0005: metadata/spec/status resource shape
ADR-0006: Repository Pattern as mandatory data access model
ADR-0007: Saga as cross-resource transaction model
ADR-0008: Event-driven audit and state propagation
ADR-0009: UUIDv7, UTC/RFC3339, soft deletion and resource versioning
```

---

## 17. Frozen Review Decisions

The following review decisions are frozen:

```text
1. Five data categories are accepted: Configuration, Spec, Status, Workflow, Audit.
2. metadata/spec/status is accepted as the universal persisted resource shape.
3. Repository Pattern is mandatory for all database access.
4. Saga is accepted as the cross-resource transaction model.
5. Event, UUIDv7, UTC/RFC3339, soft deletion, generation and resource_version are accepted as baseline data conventions.
```

---

## 18. Deferred To Later Specs

The following are intentionally deferred:

```text
P2-02 ER Model
P2-03 Table Schema and Index Design
P2-04 Migration Design
P3 API request/response schema
P4 Workflow retry/rollback design
P8 Test and Validation Design
```
