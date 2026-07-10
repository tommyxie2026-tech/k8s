# FROZEN-P2-03 Table Schema and Migration Design v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P2-02-ER-MODEL-v1.0
> Scope: CPP physical table conventions, indexes, migration rules and SQLite/PostgreSQL compatibility
> Rule: Any incompatible change to table naming, common fields, migration strategy or persistence compatibility must create a new design version and pass review again.

---

## 1. Purpose

This frozen specification defines the CPP V2.0 physical schema rules.

It does not require all tables to be implemented immediately, but all future implementation must follow this baseline.

---

## 2. Database Strategy

V2.0 uses SQLite as the default embedded database.

V2.1+ targets PostgreSQL without changing service, API or workflow logic.

All persistence access must go through repositories.

```text
Service -> Repository -> Database
```

Forbidden:

```text
Router -> SQL
Workflow -> SQL
Plugin -> SQL
Executor -> SQL
```

---

## 3. Migration Strategy

CPP uses Alembic-style versioned migrations.

Rules:

```text
1. Manual schema modification in production is forbidden.
2. Every schema change must have a migration revision.
3. Migrations must be forward deterministic.
4. Destructive migrations must require explicit release notes and backup guidance.
5. SQLite and PostgreSQL compatibility must be considered before merging migrations.
```

---

## 4. Common Table Fields

Every resource table must contain:

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
generation
resource_version
created_at
updated_at
deleted_at
```

Recommended types:

```text
id: text, UUIDv7-compatible
kind: text
name: text
labels: json/text
annotations: json/text
spec: json/text
status: json/text
generation: integer
resource_version: text
created_at: text RFC3339 UTC
updated_at: text RFC3339 UTC
deleted_at: text RFC3339 UTC nullable
```

SQLite stores JSON as text. PostgreSQL may use jsonb.

---

## 5. Core Resource Tables

Frozen resource tables:

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
```

Frozen event/audit tables:

```text
resource_events
audit_events
```

---

## 6. clusters

Purpose: stores Cluster resources.

Required indexes:

```text
idx_clusters_name
idx_clusters_deleted_at
idx_clusters_phase
```

Uniqueness:

```text
unique(name) where deleted_at is null
```

---

## 7. nodes

Purpose: stores Node resources.

Important fields:

```text
cluster_id
hostname
management_ip
```

Required indexes:

```text
idx_nodes_cluster_id
idx_nodes_hostname
idx_nodes_phase
idx_nodes_deleted_at
```

Relationship:

```text
nodes.cluster_id -> clusters.id
```

---

## 8. storage_pools

Purpose: stores StoragePool resources.

Important fields:

```text
cluster_id
type
plugin
```

Required indexes:

```text
idx_storage_pools_cluster_id
idx_storage_pools_type
idx_storage_pools_phase
```

---

## 9. storage_classes

Purpose: stores StorageClass resources.

Important fields:

```text
cluster_id
storage_pool_id
provisioner
is_default
```

Required indexes:

```text
idx_storage_classes_cluster_id
idx_storage_classes_storage_pool_id
idx_storage_classes_is_default
```

Relationship:

```text
storage_classes.storage_pool_id -> storage_pools.id
```

---

## 10. vms

Purpose: stores VM resources.

Important fields:

```text
cluster_id
namespace
node_name
backup_policy_id
```

Required indexes:

```text
idx_vms_cluster_id
idx_vms_namespace_name
idx_vms_phase
idx_vms_node_name
```

Uniqueness:

```text
unique(cluster_id, namespace, name) where deleted_at is null
```

---

## 11. backups

Purpose: stores Backup resources.

Important fields:

```text
cluster_id
scope
target_ref
backend
location
created_by_workflow_id
expires_at
```

Required indexes:

```text
idx_backups_cluster_id
idx_backups_scope_target
idx_backups_phase
idx_backups_expires_at
```

---

## 12. workflows

Purpose: stores Workflow resources.

Important fields:

```text
cluster_id
target_kind
target_id
destructive
created_by
started_at
finished_at
```

Required indexes:

```text
idx_workflows_cluster_id
idx_workflows_target
idx_workflows_phase
idx_workflows_created_at
```

---

## 13. tasks

Purpose: stores Task resources.

Important fields:

```text
workflow_id
executor_type
command_ref
return_code
log_path
started_at
finished_at
```

Required indexes:

```text
idx_tasks_workflow_id
idx_tasks_phase
idx_tasks_executor_type
idx_tasks_created_at
```

Task may exist without workflow_id for legacy direct execution.

---

## 14. plugins

Purpose: stores Plugin resources.

Important fields:

```text
category
version
provider
capabilities
```

Required indexes:

```text
idx_plugins_category
idx_plugins_phase
idx_plugins_provider
```

---

## 15. users

Purpose: stores User resources.

Important fields:

```text
username
email
source
```

Required indexes:

```text
idx_users_username
idx_users_email
idx_users_source
idx_users_phase
```

Uniqueness:

```text
unique(username) where deleted_at is null
unique(email) where deleted_at is null
```

---

## 16. resource_events

Purpose: stores resource lifecycle and state propagation events.

Fields:

```text
id
event_type
resource_kind
resource_id
resource_name
actor_id
payload
created_at
```

Rules:

```text
1. Append-only.
2. Used by WebSocket, audit bridge and monitoring.
3. Must not be used as the primary resource state store.
```

Indexes:

```text
idx_resource_events_resource
idx_resource_events_type
idx_resource_events_created_at
```

---

## 17. audit_events

Purpose: stores immutable audit records.

Fields:

```text
id
actor_id
actor_name
action
target_kind
target_id
result
request_id
workflow_id
task_id
payload
created_at
```

Rules:

```text
1. Append-only.
2. Normal DELETE must never remove audit records.
3. Correction requires a new audit event.
```

Indexes:

```text
idx_audit_events_actor
idx_audit_events_target
idx_audit_events_action
idx_audit_events_created_at
idx_audit_events_workflow_id
```

---

## 18. Compatibility Rules

SQLite/PostgreSQL compatibility rules:

```text
1. Use text IDs.
2. Use RFC3339 UTC timestamps as text at API boundary.
3. Store JSON as text in SQLite and jsonb in PostgreSQL through repository adapters.
4. Avoid database-specific business logic.
5. Do not depend on SQLite-only locking semantics.
```

---

## 19. Frozen Decisions

```text
1. SQLite first, PostgreSQL target.
2. Alembic-style versioned migrations.
3. Common resource fields are mandatory.
4. Resource tables use plural snake_case.
5. Events and audit are separate tables.
6. Audit is append-only.
7. Repository Pattern is mandatory.
8. Task may exist independently outside Workflow.
```

---

## 20. Next Document

```text
FROZEN-P3-API-SPECIFICATION-v1.0
```
