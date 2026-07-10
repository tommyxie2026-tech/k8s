# P2-03 Table Schema and Index Design v0.9

> Status: Design Review
> Depends on FROZEN-P2-01 and FROZEN-P2-02

## 1. Scope

Defines physical tables, common columns, indexes, constraints, SQLite/PostgreSQL compatibility and migration rules.

## 2. Common Resource Columns

All resource tables use:

```text
id TEXT/UUID PRIMARY KEY
kind VARCHAR(64) NOT NULL
name VARCHAR(255) NOT NULL
display_name VARCHAR(255)
description TEXT
labels JSON NOT NULL DEFAULT {}
annotations JSON NOT NULL DEFAULT {}
spec JSON NOT NULL DEFAULT {}
status JSON NOT NULL DEFAULT {}
generation BIGINT NOT NULL DEFAULT 1
resource_version VARCHAR(64) NOT NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
updated_at TIMESTAMP WITH TIME ZONE NOT NULL
deleted_at TIMESTAMP WITH TIME ZONE NULL
```

SQLite stores UUID/timestamps as text and JSON as JSON-compatible text. PostgreSQL uses UUID, TIMESTAMPTZ and JSONB.

## 3. Core Tables

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
node_storage_pools
vm_storage_classes
audit_events
resource_events
schema_migrations
```

## 4. Foreign Keys

```text
nodes.cluster_id -> clusters.id
storage_pools.cluster_id -> clusters.id
storage_pools.plugin_id -> plugins.id optional
storage_classes.cluster_id -> clusters.id
storage_classes.storage_pool_id -> storage_pools.id
vms.cluster_id -> clusters.id
backups.cluster_id -> clusters.id
backups.vm_id -> vms.id optional
backups.created_by_workflow_id -> workflows.id optional
workflows.cluster_id -> clusters.id optional
workflows.created_by -> users.id
tasks.workflow_id -> workflows.id optional
```

All foreign keys use RESTRICT or SET NULL. CASCADE delete is forbidden for durable domain resources.

## 5. Unique Constraints

Partial uniqueness applies only to non-deleted rows:

```text
clusters(name)
nodes(cluster_id, hostname)
storage_pools(cluster_id, name)
storage_classes(cluster_id, name)
vms(cluster_id, namespace, name)
plugins(name, version)
users(username)
```

SQLite compatibility may use composite unique constraints including `deleted_at` plus repository checks where partial indexes are unavailable.

## 6. Required Indexes

```text
idx_resource_kind_created(kind, created_at)
idx_resource_name_deleted(name, deleted_at)
idx_nodes_cluster(cluster_id, deleted_at)
idx_storage_pools_cluster(cluster_id, deleted_at)
idx_storage_classes_pool(storage_pool_id, deleted_at)
idx_vms_cluster_namespace(cluster_id, namespace, deleted_at)
idx_backups_target(target_kind, target_id, created_at)
idx_workflows_phase_created(phase, created_at)
idx_tasks_workflow_phase(workflow_id, phase)
idx_audit_actor_created(actor_id, created_at)
idx_audit_target_created(target_kind, target_id, created_at)
idx_events_resource_created(resource_kind, resource_id, created_at)
```

## 7. Status Projection Columns

Frequently queried lifecycle values may be projected from JSON into dedicated columns:

```text
phase
cluster_id
namespace
executor_type
return_code
```

JSON remains authoritative for full status, while projected columns are query accelerators and must be updated in the same local transaction.

## 8. Audit and Event Tables

`audit_events` and `resource_events` are append-only. UPDATE and DELETE are forbidden through repositories. Purge requires an explicit administrative retention workflow.

## 9. Optimistic Concurrency

Updates must include:

```sql
WHERE id = :id AND resource_version = :expected_version
```

A successful update generates a new `resource_version`; spec changes also increment `generation`.

## 10. Migration Rules

Alembic is mandatory. Each migration must be forward-only in production, idempotent where practical, and validated on both SQLite and PostgreSQL. Destructive migrations require backup, explicit approval and rollback documentation.

## 11. Review Items

1. Accept JSON/JSONB for spec/status with projected query columns.
2. Accept no cascade delete for core resources.
3. Accept append-only event/audit tables.
4. Accept SQLite V2.0 and PostgreSQL-compatible schema from day one.
5. Accept Alembic as the only schema migration mechanism.
