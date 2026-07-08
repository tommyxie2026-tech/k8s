# P2-01 Data Architecture Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on: FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0, FROZEN-P1-01-DOMAIN-MODEL-v1.0
> Scope: CPP data architecture and persistence principles

---

## 1. Purpose

This document defines the data architecture for CPP V2.0.

It does not define final database tables. Table schema, indexes and constraints will be defined in P2-02 ER Model and P2-03 Persistence Strategy.

This document freezes the high-level rules for:

```text
Data classification
Resource storage model
Runtime data boundary
Audit data boundary
Migration strategy
Naming conventions
```

---

## 2. Design Principles

CPP data architecture follows the frozen P0/P1 principles:

```text
Everything Is A Resource
Resource Model Driven
API First
Workflow Native
Safe by Default
```

Database design must support these principles rather than merely persist implementation objects.

---

## 3. Data Classification

CPP data is divided into four categories.

| Category | Persisted | Examples | Owner |
|---|---|---|---|
| Resource Data | Yes | Cluster, Node, VM, StoragePool, Backup | Resource Plane |
| Workflow Data | Yes | Workflow, Task, Step result | Workflow / Runtime Plane |
| Runtime Data | No or Recoverable | Worker queue, process context, lock state | Runtime Plane |
| Audit Data | Yes | User action, workflow event, task event | Observability Plane |

---

## 4. Resource Data

Resource Data is the durable source of truth for CPP resources.

Frozen core resources inherited from P1:

```text
Cluster
Node
StoragePool
StorageClass
VM
Backup
Workflow
Task
Plugin
User
```

All resource data must use the metadata/spec/status pattern.

---

## 5. Metadata / Spec / Status Model

Every persisted resource must be stored in three logical sections.

```yaml
Resource:
  metadata:
    id: string
    kind: string
    name: string
    display_name: string
    description: string
    labels: map[string]string
    annotations: map[string]string
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime|null
  spec:
    desired_state: object
  status:
    observed_state: object
```

Rules:

```text
1. metadata identifies and describes the resource.
2. spec is desired state and may be changed by API or Workflow.
3. status is observed state and must be changed by controllers, workers, runtime or reconciliation logic.
4. API may read both spec and status.
5. API must not fake runtime status without an observation source.
```

---

## 6. Workflow Data

Workflow Data must be persisted.

Workflow persistence must include:

```text
workflow id
workflow name
target resource
destructive flag
current phase
step list
step phase
step input
step output reference
return code
created_at
started_at
finished_at
```

Workflow and Task data must survive API process restart.

---

## 7. Runtime Data

Runtime Data includes:

```text
in-memory queue
worker process state
executor context
temporary lock
subprocess pid
streaming log cursor
```

Runtime Data is not the source of truth.

Rules:

```text
1. Runtime Data may be lost during restart.
2. Runtime must be reconstructable from Workflow and Task persisted data.
3. Critical lifecycle transitions must be flushed before execution.
4. Long-running tasks must write observable progress to persistent Task or Audit data.
```

---

## 8. Audit Data

Audit Data is immutable append-only data.

Audit records must capture:

```text
timestamp
actor
action
resource kind
resource id
workflow id
task id
result
request id
source ip optional
```

Audit Data must not be physically updated except by retention and archival processes.

---

## 9. Storage Backend Strategy

V2.0 uses a staged storage backend strategy.

### V2.0

```text
SQLite for single-node and development deployment
File-based workflow/audit compatibility layer allowed during transition
```

### V2.1

```text
SQLite with Alembic migrations
Optional PostgreSQL backend
```

### V2.2+

```text
PostgreSQL recommended for production HA
External object storage for logs, backups and large artifacts
```

API and domain models must not depend on the concrete database backend.

---

## 10. Migration Strategy

Schema changes must be versioned.

Preferred tool:

```text
Alembic
```

Rules:

```text
1. Manual production schema modification is forbidden.
2. Every schema change must have a migration version.
3. Migrations must be reversible where practical.
4. Data migrations must be separated from code behavior changes when possible.
5. Database version must be visible via admin API or diagnostic command.
```

---

## 11. Naming Conventions

Table names must use snake_case plural form.

Examples:

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
audit_events
```

Common columns:

```text
id
kind
name
display_name
description
labels
annotations
spec
status
created_at
updated_at
deleted_at
```

Lifecycle field inside status should use:

```text
phase
```

Avoid mixing:

```text
state
status
running
condition
```

as primary lifecycle fields.

---

## 12. Indexing Principles

Indexes are not fully frozen here, but the following principles apply:

```text
1. id must be indexed and unique.
2. kind + name should be indexed where name lookup is common.
3. cluster_id should be indexed for cluster-scoped resources.
4. deleted_at should support soft-delete filtering.
5. labels may require JSON or auxiliary index strategy in later design.
```

Detailed indexes are deferred to P2-02.

---

## 13. Transaction Principles

Transactions must protect state transitions.

Examples:

```text
Workflow created + first Task created
Task running + audit event written
Task failed + Workflow failed
Resource spec update + audit event written
```

If audit and resource update cannot be atomically committed in V2.0, failure must be clearly logged and recoverable.

---

## 14. Data Ownership

Ownership is frozen as follows:

```text
Resource Plane owns Resource Data.
Workflow Plane owns Workflow Data.
Runtime Plane owns Runtime Data and Task execution updates.
Observability Plane owns Audit Data.
Plugin Plane does not own database tables directly in V2.0.
```

Plugins must use stable service APIs instead of direct table access.

---

## 15. Review Items

Before freezing P2-01, confirm:

1. Do we accept the four data categories: Resource, Workflow, Runtime, Audit?
2. Do we freeze metadata/spec/status as the universal persistence model?
3. Do we accept Runtime Data as recoverable but not authoritative?
4. Do we accept SQLite -> PostgreSQL staged evolution?
5. Do we accept Alembic-style versioned schema migration?
6. Do we accept snake_case plural table naming and `phase` as the lifecycle field?

---

## 16. Deferred To Later Specs

The following are intentionally deferred:

```text
ER diagram -> P2-02
Full table schema -> P2-02
Persistence lifecycle details -> P2-03
Migration implementation -> P2-04
Database coding convention -> P2-05
API response schema -> P3
Workflow retry and rollback details -> P4
```
