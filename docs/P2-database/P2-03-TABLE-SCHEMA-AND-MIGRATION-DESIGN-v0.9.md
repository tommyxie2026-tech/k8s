# P2-03 Table Schema and Migration Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on:
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - P2-02-ER-MODEL-DESIGN-v0.9
> Scope: CPP physical schema strategy, baseline table design, indexes and migrations

---

## 1. Purpose

This document defines the CPP V2.0 physical persistence strategy.

It translates P2-01 and P2-02 into candidate tables, common columns, indexes and migration conventions.

This document is still Design Review and must be frozen before implementation.

---

## 2. Database Strategy

V2.0 starts with SQLite for development and single-node deployment.

V2.1 targets PostgreSQL for production HA.

The schema must be designed with PostgreSQL compatibility in mind from day one.

Rules:

```text
1. Do not depend on SQLite-only behavior.
2. Keep JSON fields compatible with PostgreSQL jsonb migration.
3. Use Repository Pattern for all persistence access.
4. Use Alembic for versioned migrations.
5. Do not change schema manually without migration files.
```

---

## 3. Common Columns

All resource tables must include:

```sql
id TEXT PRIMARY KEY,
kind TEXT NOT NULL,
name TEXT NOT NULL,
labels JSON NOT NULL DEFAULT '{}',
annotations JSON NOT NULL DEFAULT '{}',
spec JSON NOT NULL DEFAULT '{}',
status JSON NOT NULL DEFAULT '{}',
generation INTEGER NOT NULL DEFAULT 1,
resource_version TEXT NOT NULL,
created_at TEXT NOT NULL,
updated_at TEXT NOT NULL,
deleted_at TEXT NULL
```

Rules:

```text
id must be UUIDv7-compatible.
created_at/updated_at/deleted_at use UTC RFC3339 format.
labels, annotations, spec and status are JSON in SQLite and jsonb in PostgreSQL.
phase is stored inside status.phase, not as a top-level column unless denormalized later for performance.
```

---

## 4. Baseline Tables

CPP V2.0 baseline tables:

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
resource_events
schema_versions
```

---

## 5. Resource Tables

### 5.1 clusters

Logical columns:

```sql
clusters (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'Cluster',
  name TEXT NOT NULL,
  labels JSON NOT NULL DEFAULT '{}',
  annotations JSON NOT NULL DEFAULT '{}',
  spec JSON NOT NULL DEFAULT '{}',
  status JSON NOT NULL DEFAULT '{}',
  generation INTEGER NOT NULL DEFAULT 1,
  resource_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT NULL
)
```

Candidate indexes:

```text
idx_clusters_name_active unique(name) where deleted_at is null
idx_clusters_created_at
idx_clusters_deleted_at
```

---

### 5.2 nodes

Additional columns:

```sql
cluster_id TEXT NOT NULL
```

Candidate indexes:

```text
idx_nodes_cluster_id
idx_nodes_cluster_name_active unique(cluster_id, name) where deleted_at is null
idx_nodes_deleted_at
```

---

### 5.3 storage_pools

Additional columns:

```sql
cluster_id TEXT NOT NULL
```

Candidate indexes:

```text
idx_storage_pools_cluster_id
idx_storage_pools_cluster_name_active unique(cluster_id, name) where deleted_at is null
```

---

### 5.4 storage_classes

Additional columns:

```sql
cluster_id TEXT NOT NULL,
storage_pool_id TEXT NOT NULL
```

Candidate indexes:

```text
idx_storage_classes_cluster_id
idx_storage_classes_storage_pool_id
idx_storage_classes_cluster_name_active unique(cluster_id, name) where deleted_at is null
```

---

### 5.5 vms

Additional columns:

```sql
cluster_id TEXT NOT NULL,
namespace TEXT NOT NULL
```

Candidate indexes:

```text
idx_vms_cluster_id
idx_vms_namespace
idx_vms_cluster_namespace_name_active unique(cluster_id, namespace, name) where deleted_at is null
idx_vms_deleted_at
```

---

### 5.6 backups

Additional columns:

```sql
cluster_id TEXT NOT NULL,
target_kind TEXT NOT NULL,
target_id TEXT NULL,
workflow_id TEXT NULL
```

Candidate indexes:

```text
idx_backups_cluster_id
idx_backups_target
idx_backups_workflow_id
idx_backups_created_at
```

---

### 5.7 workflows

Additional columns:

```sql
cluster_id TEXT NULL,
target_kind TEXT NULL,
target_id TEXT NULL,
created_by TEXT NULL
```

Candidate indexes:

```text
idx_workflows_cluster_id
idx_workflows_target
idx_workflows_created_by
idx_workflows_created_at
idx_workflows_deleted_at
```

---

### 5.8 tasks

Additional columns:

```sql
workflow_id TEXT NULL,
executor_type TEXT NOT NULL,
command_ref TEXT NOT NULL
```

Candidate indexes:

```text
idx_tasks_workflow_id
idx_tasks_executor_type
idx_tasks_created_at
```

---

### 5.9 plugins

Additional columns:

```sql
category TEXT NOT NULL,
version TEXT NOT NULL,
provider TEXT NULL
```

Candidate indexes:

```text
idx_plugins_category
idx_plugins_name_version_active unique(name, version) where deleted_at is null
```

---

### 5.10 users

Additional columns:

```sql
source TEXT NOT NULL
```

Candidate indexes:

```text
idx_users_name_active unique(name) where deleted_at is null
idx_users_source
```

---

## 6. Event Tables

### 6.1 audit_events

Audit events are append-only.

```sql
audit_events (
  id TEXT PRIMARY KEY,
  actor_id TEXT NULL,
  actor_type TEXT NOT NULL,
  action TEXT NOT NULL,
  target_kind TEXT NULL,
  target_id TEXT NULL,
  workflow_id TEXT NULL,
  task_id TEXT NULL,
  result TEXT NOT NULL,
  reason TEXT NULL,
  metadata JSON NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
)
```

Indexes:

```text
idx_audit_events_actor
idx_audit_events_target
idx_audit_events_action
idx_audit_events_created_at
idx_audit_events_workflow_id
idx_audit_events_task_id
```

Rules:

```text
No updated_at.
No deleted_at.
No update-in-place.
Corrections must be represented by new events.
```

---

### 6.2 resource_events

Resource events record resource lifecycle and state changes.

```sql
resource_events (
  id TEXT PRIMARY KEY,
  resource_kind TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  reason TEXT NULL,
  message TEXT NULL,
  workflow_id TEXT NULL,
  task_id TEXT NULL,
  metadata JSON NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
)
```

Indexes:

```text
idx_resource_events_resource
idx_resource_events_event_type
idx_resource_events_created_at
idx_resource_events_workflow_id
idx_resource_events_task_id
```

---

## 7. Foreign Key Strategy

P2-03 recommends a pragmatic foreign key strategy.

Strict FK candidates:

```text
nodes.cluster_id -> clusters.id
storage_pools.cluster_id -> clusters.id
storage_classes.cluster_id -> clusters.id
storage_classes.storage_pool_id -> storage_pools.id
vms.cluster_id -> clusters.id
tasks.workflow_id -> workflows.id nullable
```

Polymorphic references are not strict FK candidates:

```text
workflow.target_kind + workflow.target_id
backup.target_kind + backup.target_id
audit_events.target_kind + audit_events.target_id
resource_events.resource_kind + resource_events.resource_id
```

Reason:

```text
Polymorphic targets must support all current and future resource kinds.
Strict foreign keys here would make schema evolution harder.
```

---

## 8. JSON Column Strategy

SQLite:

```text
JSON stored as TEXT with JSON validation where practical.
```

PostgreSQL:

```text
JSON migrated to jsonb.
GIN indexes may be added for selected labels/spec/status paths.
```

Rules:

```text
1. Do not query deeply nested JSON fields in critical paths unless indexed.
2. Keep frequently queried fields as dedicated columns only after proven need.
3. Do not prematurely denormalize status.phase in v0.9.
```

---

## 9. Migration Strategy

Use Alembic for schema migrations.

Recommended layout:

```text
platform-api/
  alembic.ini
  migrations/
    env.py
    versions/
      0001_initial_resource_tables.py
      0002_event_tables.py
      0003_indexes.py
```

Rules:

```text
1. Every schema change must have an Alembic migration.
2. Migrations must be forward-only by default.
3. Downgrade may be best-effort for development but not required for destructive production changes.
4. Migration files must be reviewed like application code.
5. CI must run migration upgrade on a clean SQLite database.
```

---

## 10. Repository Boundary

Each aggregate root should have a repository.

Candidate repositories:

```text
ClusterRepository
NodeRepository
StoragePoolRepository
StorageClassRepository
VMRepository
BackupRepository
WorkflowRepository
TaskRepository
PluginRepository
UserRepository
AuditEventRepository
ResourceEventRepository
```

Repository methods should use Resource semantics:

```text
create(resource)
get(id)
list(filters)
update_spec(id, spec, resource_version)
update_status(id, status)
soft_delete(id)
append_event(event)
```

Forbidden:

```text
Router writes SQL directly
Workflow writes SQL directly
Plugin writes SQL directly
Executor writes SQL directly
```

---

## 11. Concurrency Strategy

All resource updates must use optimistic concurrency.

Rules:

```text
1. update_spec requires expected resource_version.
2. update_status updates resource_version.
3. generation increments only on spec changes.
4. conflicting updates must return conflict errors at service/API layer.
```

---

## 12. Deletion and Retention

Resource tables:

```text
soft delete with deleted_at
```

Event tables:

```text
append-only, no soft delete by normal operation
```

Future retention design:

```text
audit_events retention policy
resource_events retention policy
workflow/task archival policy
backup expiry policy
```

---

## 13. Review Items

Before freezing P2-03, confirm:

1. Are JSON spec/status fields acceptable for V2.0?
2. Should status.phase remain inside JSON or be denormalized into a dedicated column from day one?
3. Is nullable tasks.workflow_id acceptable for legacy direct tasks?
4. Is the pragmatic FK strategy acceptable?
5. Is Alembic the mandatory migration mechanism?
6. Should event tables be append-only with no updated_at/deleted_at?
