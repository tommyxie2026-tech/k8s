# P2-03 Table Schema and Index Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on:
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - P2-02-ER-MODEL-DESIGN-v0.9
> Scope: CPP physical table candidates, common columns, indexes and constraints

---

## 1. Purpose

This document defines the candidate physical table schema for CPP V2.0.

It remains database-agnostic where possible and must support SQLite first, PostgreSQL later.

---

## 2. Table Naming

Tables use plural snake_case:

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

---

## 3. Common Resource Columns

All core resource tables should include:

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

Notes:

```text
1. SQLite may store JSON as TEXT with JSON validation in app/repository layer.
2. PostgreSQL target should use JSONB.
3. Timestamps use UTC RFC3339-compatible strings.
4. id must be UUIDv7-compatible.
```

---

## 4. clusters

Additional indexed fields:

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

## 5. nodes

Additional fields:

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

## 6. storage_pools

Additional fields:

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

## 7. storage_classes

Additional fields:

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

## 8. vms

Additional fields:

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

## 9. backups

Additional fields:

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

## 10. workflows

Additional fields:

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

## 11. tasks

Additional fields:

```sql
workflow_id TEXT,
executor_type TEXT NOT NULL,
command_ref TEXT,
phase TEXT,
return_code INTEGER,
log_path TEXT,
started_at TEXT,
finished_at TEXT
```

Indexes:

```text
idx_tasks_workflow(workflow_id)
idx_tasks_phase(phase)
idx_tasks_executor_type(executor_type)
idx_tasks_started_at(started_at)
```

---

## 12. plugins

Additional fields:

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

## 13. users

Additional fields:

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

## 14. audit_events

Audit events are append-only.

Candidate columns:

```sql
id TEXT PRIMARY KEY,
actor_user_id TEXT,
action TEXT NOT NULL,
target_kind TEXT,
target_id TEXT,
workflow_id TEXT,
task_id TEXT,
result TEXT,
message TEXT,
metadata JSON NOT NULL DEFAULT '{}',
created_at TEXT NOT NULL
```

Indexes:

```text
idx_audit_events_actor(actor_user_id)
idx_audit_events_target(target_kind, target_id)
idx_audit_events_action(action)
idx_audit_events_created_at(created_at)
```

No updated_at or deleted_at for normal audit rows.

---

## 15. resource_events

Resource events support UI, WebSocket and lifecycle visibility.

Candidate columns:

```sql
id TEXT PRIMARY KEY,
resource_kind TEXT NOT NULL,
resource_id TEXT NOT NULL,
event_type TEXT NOT NULL,
actor_user_id TEXT,
workflow_id TEXT,
task_id TEXT,
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

---

## 16. JSON Field Strategy

SQLite V2.0:

```text
JSON stored as TEXT.
Validation performed in repository/service layer.
Indexes are only created on extracted shadow columns where needed.
```

PostgreSQL target:

```text
JSONB for labels, annotations, spec, status, metadata and payload.
GIN indexes may be added for labels/selectors in later versions.
```

---

## 17. Soft Delete Index Strategy

SQLite has limited partial index portability with future PostgreSQL migration.

V2.0 default:

```text
Use deleted_at in uniqueness checks at repository/service layer.
Add composite indexes including deleted_at for lookup performance.
```

PostgreSQL later:

```text
Use partial unique indexes WHERE deleted_at IS NULL.
```

---

## 18. Review Items

Before freezing P2-03, confirm:

```text
1. All core resources use common metadata/spec/status columns.
2. phase is duplicated as an indexed shadow column from status.phase.
3. SQLite stores JSON as TEXT in V2.0.
4. AuditEvent is append-only and does not use deleted_at.
5. ResourceEvent is separate from AuditEvent.
6. Soft-delete uniqueness is enforced by repository in V2.0 and DB partial indexes in PostgreSQL later.
```
