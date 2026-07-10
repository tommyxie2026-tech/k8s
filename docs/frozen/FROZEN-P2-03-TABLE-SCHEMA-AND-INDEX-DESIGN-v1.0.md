# FROZEN-P2-03 Table Schema and Index Design v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P2-02-ER-MODEL-v1.0
> Scope: CPP physical table candidates, common columns, indexes and constraints
> Rule: Any incompatible change to common columns, table naming, indexed shadow fields, append-only event tables, or soft-delete uniqueness strategy must create a new design version and pass review again.

---

## 1. Purpose

This document freezes the CPP V2.0 physical table and index baseline.

The design is database-agnostic where practical and must support:

```text
SQLite in V2.0
PostgreSQL in later versions
```

---

## 2. Frozen Table Set

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
```

All table names use plural snake_case.

---

## 3. Common Resource Columns

All mutable resource tables must include:

```sql
id TEXT PRIMARY KEY,
kind TEXT NOT NULL,
name TEXT NOT NULL,
display_name TEXT,
description TEXT,
labels JSON NOT NULL DEFAULT '{}',
annotations JSON NOT NULL DEFAULT '{}',
spec JSON NOT NULL DEFAULT '{}',
status JSON NOT NULL DEFAULT '{}',
generation INTEGER NOT NULL DEFAULT 1,
resource_version TEXT NOT NULL,
created_at TEXT NOT NULL,
updated_at TEXT NOT NULL,
deleted_at TEXT
```

Rules:

```text
1. SQLite stores JSON as TEXT and validates it in repository/service layers.
2. PostgreSQL uses JSONB.
3. All timestamps are UTC and RFC3339-compatible.
4. id is UUIDv7-compatible.
5. generation increments only when spec changes.
6. resource_version changes on any persisted change.
```

---

## 4. Indexed Shadow Columns

Frequently queried fields may be duplicated from spec/status into typed shadow columns.

The canonical resource payload remains metadata/spec/status. Shadow columns exist only for filtering, sorting and indexing.

Frozen lifecycle shadow column:

```text
phase
```

Rules:

```text
1. phase mirrors status.phase.
2. Repository writes must update status and phase atomically.
3. Shadow columns must never become an alternative source of truth.
```

---

## 5. clusters

Additional columns:

```sql
provider TEXT,
mode TEXT,
api_endpoint TEXT,
phase TEXT
```

Indexes:

```text
idx_clusters_name_active(name, deleted_at)
idx_clusters_phase(phase)
idx_clusters_mode(mode)
```

---

## 6. nodes

Additional columns:

```sql
cluster_id TEXT NOT NULL,
hostname TEXT NOT NULL,
management_ip TEXT,
phase TEXT
```

Indexes:

```text
idx_nodes_cluster(cluster_id)
idx_nodes_cluster_hostname(cluster_id, hostname, deleted_at)
idx_nodes_phase(phase)
```

Foreign key candidate:

```text
nodes.cluster_id -> clusters.id
```

---

## 7. storage_pools

Additional columns:

```sql
cluster_id TEXT NOT NULL,
type TEXT NOT NULL,
plugin TEXT,
phase TEXT
```

Indexes:

```text
idx_storage_pools_cluster(cluster_id)
idx_storage_pools_cluster_name(cluster_id, name, deleted_at)
idx_storage_pools_type(type)
idx_storage_pools_phase(phase)
```

---

## 8. storage_classes

Additional columns:

```sql
cluster_id TEXT NOT NULL,
storage_pool_id TEXT,
provisioner TEXT,
reclaim_policy TEXT,
volume_binding_mode TEXT,
phase TEXT
```

Indexes:

```text
idx_storage_classes_cluster(cluster_id)
idx_storage_classes_pool(storage_pool_id)
idx_storage_classes_cluster_name(cluster_id, name, deleted_at)
idx_storage_classes_phase(phase)
```

Foreign key candidates:

```text
storage_classes.cluster_id -> clusters.id
storage_classes.storage_pool_id -> storage_pools.id
```

---

## 9. vms

Additional columns:

```sql
cluster_id TEXT NOT NULL,
namespace TEXT NOT NULL,
phase TEXT,
node_name TEXT
```

Indexes:

```text
idx_vms_cluster(cluster_id)
idx_vms_cluster_namespace_name(cluster_id, namespace, name, deleted_at)
idx_vms_phase(phase)
idx_vms_node(node_name)
```

---

## 10. backups

Additional columns:

```sql
cluster_id TEXT NOT NULL,
scope TEXT NOT NULL,
target_kind TEXT,
target_id TEXT,
backend TEXT,
location TEXT,
phase TEXT,
created_by_workflow_id TEXT,
expires_at TEXT
```

Indexes:

```text
idx_backups_cluster(cluster_id)
idx_backups_target(target_kind, target_id)
idx_backups_phase(phase)
idx_backups_expires_at(expires_at)
```

---

## 11. workflows

Additional columns:

```sql
cluster_id TEXT,
target_kind TEXT,
target_id TEXT,
destructive INTEGER NOT NULL DEFAULT 0,
created_by TEXT,
phase TEXT,
started_at TEXT,
finished_at TEXT
```

Indexes:

```text
idx_workflows_phase(phase)
idx_workflows_cluster(cluster_id)
idx_workflows_target(target_kind, target_id)
idx_workflows_created_by(created_by)
idx_workflows_created_at(created_at)
```

---

## 12. tasks

Additional columns:

```sql
workflow_id TEXT,
executor_type TEXT NOT NULL,
command_ref TEXT,
sequence_number INTEGER,
phase TEXT,
return_code INTEGER,
log_path TEXT,
started_at TEXT,
finished_at TEXT
```

Indexes:

```text
idx_tasks_workflow(workflow_id)
idx_tasks_workflow_sequence(workflow_id, sequence_number)
idx_tasks_phase(phase)
idx_tasks_executor_type(executor_type)
idx_tasks_started_at(started_at)
```

---

## 13. plugins

Additional columns:

```sql
category TEXT NOT NULL,
version TEXT NOT NULL,
provider TEXT,
phase TEXT
```

Indexes:

```text
idx_plugins_name_version(name, version, deleted_at)
idx_plugins_category(category)
idx_plugins_phase(phase)
```

---

## 14. users

Additional columns:

```sql
username TEXT NOT NULL,
email TEXT,
source TEXT NOT NULL,
phase TEXT
```

Indexes:

```text
idx_users_username_source(username, source, deleted_at)
idx_users_email(email)
idx_users_phase(phase)
```

---

## 15. audit_events

Audit events are append-only.

```sql
id TEXT PRIMARY KEY,
actor_user_id TEXT,
actor_name TEXT,
action TEXT NOT NULL,
target_kind TEXT,
target_id TEXT,
workflow_id TEXT,
task_id TEXT,
result TEXT,
request_id TEXT,
message TEXT,
metadata JSON NOT NULL DEFAULT '{}',
created_at TEXT NOT NULL
```

Indexes:

```text
idx_audit_events_actor(actor_user_id)
idx_audit_events_target(target_kind, target_id)
idx_audit_events_action(action)
idx_audit_events_workflow(workflow_id)
idx_audit_events_created_at(created_at)
```

Rules:

```text
1. No updated_at.
2. No deleted_at.
3. Existing rows must not be updated in place.
```

---

## 16. resource_events

Resource events are append-only and support UI, WebSocket and lifecycle history.

```sql
id TEXT PRIMARY KEY,
resource_kind TEXT NOT NULL,
resource_id TEXT NOT NULL,
event_type TEXT NOT NULL,
source TEXT,
reason TEXT,
message TEXT,
actor_user_id TEXT,
workflow_id TEXT,
task_id TEXT,
generation INTEGER,
resource_version TEXT,
payload JSON NOT NULL DEFAULT '{}',
created_at TEXT NOT NULL
```

Indexes:

```text
idx_resource_events_resource(resource_kind, resource_id)
idx_resource_events_event_type(event_type)
idx_resource_events_created_at(created_at)
idx_resource_events_workflow(workflow_id)
```

Rules:

```text
1. No updated_at.
2. No deleted_at.
3. High-volume metric samples must not be stored here.
```

---

## 17. JSON Strategy

SQLite V2.0:

```text
JSON stored as TEXT.
Validation occurs in repository/service layers.
Indexes use extracted typed shadow columns where needed.
```

PostgreSQL target:

```text
Use JSONB for labels, annotations, spec, status, metadata and payload.
GIN indexes may be added later for labels and selectors.
```

---

## 18. Soft-Delete Uniqueness

SQLite V2.0:

```text
Repository/service layer enforces uniqueness among records where deleted_at is null.
Composite indexes including deleted_at support lookup performance.
```

PostgreSQL target:

```text
Use partial unique indexes WHERE deleted_at IS NULL.
```

No automatic destructive cascade is allowed across aggregate roots.

---

## 19. Frozen Review Decisions

```text
1. All core resources use common metadata/spec/status columns.
2. phase is an indexed shadow column mirroring status.phase.
3. SQLite stores JSON as TEXT in V2.0.
4. PostgreSQL target uses JSONB.
5. AuditEvent is append-only and has no deleted_at.
6. ResourceEvent is separate from AuditEvent.
7. Soft-delete uniqueness is enforced by repository in SQLite and partial unique indexes in PostgreSQL.
8. Table names use plural snake_case.
9. sequence_number is required for ordered Workflow Tasks.
```

---

## 20. Deferred

```text
Concrete Alembic revisions
Migration rollback procedures
Repository interfaces and ORM mappings
Retention jobs
Partitioning strategy
PostgreSQL-specific GIN indexes
```

Next document:

```text
P2-04 Migration Design
```
