# P2-01 Database Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on: FROZEN-P1-01-DOMAIN-MODEL-v1.0
> Scope: CPP V2.0 persistence model

---

## 1. Purpose

This document defines the first database design for CPP V2.0.

It maps the frozen P1 domain resources to database tables, indexes and migration rules.

This document does not define REST API paths. API contracts are defined in P3.

---

## 2. Database Strategy

CPP V2.0 uses a staged database strategy:

```text
V2.0: SQLite for standalone and simple deployments
V2.1: SQLite with migration discipline and backup tooling
V2.2: PostgreSQL support
V3.0: PostgreSQL HA as enterprise default
```

Rationale:

```text
1. SQLite is simple for development and single-node environments.
2. PostgreSQL is required for HA and multi-instance API deployments.
3. The schema must be designed to migrate cleanly from SQLite to PostgreSQL.
```

---

## 3. Design Principles

```text
1. Every frozen resource has a table.
2. Common resource fields must be consistent across tables.
3. spec and status are JSON fields in V2.0.
4. Frequently queried fields must have explicit columns and indexes.
5. Soft deletion is preferred over hard deletion for resources.
6. Audit logs are append-only.
7. Workflow and Task records must be durable.
8. Database schema changes must use migrations.
```

---

## 4. Common Table Contract

Every resource table must include:

```sql
id TEXT PRIMARY KEY,
kind TEXT NOT NULL,
name TEXT NOT NULL,
display_name TEXT,
description TEXT,
labels_json TEXT,
annotations_json TEXT,
spec_json TEXT NOT NULL,
status_json TEXT NOT NULL,
created_at TEXT NOT NULL,
updated_at TEXT NOT NULL,
deleted_at TEXT
```

PostgreSQL mapping:

```text
TEXT -> text
labels_json -> jsonb
annotations_json -> jsonb
spec_json -> jsonb
status_json -> jsonb
```

---

## 5. Tables

### 5.1 clusters

```sql
CREATE TABLE clusters (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL UNIQUE,
  display_name TEXT,
  description TEXT,
  provider TEXT,
  mode TEXT,
  kubernetes_version TEXT,
  api_endpoint TEXT,
  control_plane_endpoint TEXT,
  inventory_ref TEXT,
  phase TEXT NOT NULL,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_clusters_phase ON clusters(phase);
CREATE INDEX idx_clusters_mode ON clusters(mode);
```

---

### 5.2 nodes

```sql
CREATE TABLE nodes (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  name TEXT NOT NULL,
  hostname TEXT NOT NULL,
  management_ip TEXT,
  phase TEXT NOT NULL,
  roles_json TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  UNIQUE(cluster_id, hostname)
);
```

Indexes:

```sql
CREATE INDEX idx_nodes_cluster_id ON nodes(cluster_id);
CREATE INDEX idx_nodes_phase ON nodes(phase);
CREATE INDEX idx_nodes_hostname ON nodes(hostname);
```

---

### 5.3 storage_pools

```sql
CREATE TABLE storage_pools (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  plugin TEXT,
  phase TEXT NOT NULL,
  capacity_total INTEGER,
  capacity_used INTEGER,
  snapshot_supported INTEGER,
  expansion_supported INTEGER,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  UNIQUE(cluster_id, name)
);
```

Indexes:

```sql
CREATE INDEX idx_storage_pools_cluster_id ON storage_pools(cluster_id);
CREATE INDEX idx_storage_pools_type ON storage_pools(type);
CREATE INDEX idx_storage_pools_phase ON storage_pools(phase);
```

---

### 5.4 storage_classes

```sql
CREATE TABLE storage_classes (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  storage_pool_id TEXT,
  name TEXT NOT NULL,
  provisioner TEXT,
  reclaim_policy TEXT,
  volume_binding_mode TEXT,
  allow_volume_expansion INTEGER,
  is_default INTEGER,
  phase TEXT NOT NULL,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  UNIQUE(cluster_id, name)
);
```

Indexes:

```sql
CREATE INDEX idx_storage_classes_cluster_id ON storage_classes(cluster_id);
CREATE INDEX idx_storage_classes_pool_id ON storage_classes(storage_pool_id);
CREATE INDEX idx_storage_classes_default ON storage_classes(is_default);
```

---

### 5.5 vms

```sql
CREATE TABLE vms (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  name TEXT NOT NULL,
  cpu INTEGER,
  memory INTEGER,
  phase TEXT NOT NULL,
  node_name TEXT,
  backup_policy_id TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  UNIQUE(cluster_id, namespace, name)
);
```

Indexes:

```sql
CREATE INDEX idx_vms_cluster_id ON vms(cluster_id);
CREATE INDEX idx_vms_namespace ON vms(namespace);
CREATE INDEX idx_vms_phase ON vms(phase);
CREATE INDEX idx_vms_node_name ON vms(node_name);
```

---

### 5.6 backups

```sql
CREATE TABLE backups (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  target_ref TEXT,
  backend TEXT,
  location TEXT,
  phase TEXT NOT NULL,
  created_by_workflow_id TEXT,
  expires_at TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_backups_cluster_id ON backups(cluster_id);
CREATE INDEX idx_backups_scope ON backups(scope);
CREATE INDEX idx_backups_target_ref ON backups(target_ref);
CREATE INDEX idx_backups_phase ON backups(phase);
CREATE INDEX idx_backups_expires_at ON backups(expires_at);
```

---

### 5.7 workflows

```sql
CREATE TABLE workflows (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  cluster_id TEXT,
  target_kind TEXT,
  target_id TEXT,
  destructive INTEGER NOT NULL,
  phase TEXT NOT NULL,
  created_by TEXT,
  started_at TEXT,
  finished_at TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_workflows_phase ON workflows(phase);
CREATE INDEX idx_workflows_target ON workflows(target_kind, target_id);
CREATE INDEX idx_workflows_cluster_id ON workflows(cluster_id);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
```

---

### 5.8 tasks

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  workflow_id TEXT,
  name TEXT NOT NULL,
  executor_type TEXT NOT NULL,
  command_ref TEXT,
  phase TEXT NOT NULL,
  return_code INTEGER,
  log_path TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX idx_tasks_phase ON tasks(phase);
CREATE INDEX idx_tasks_executor_type ON tasks(executor_type);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

---

### 5.9 plugins

```sql
CREATE TABLE plugins (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  version TEXT,
  provider TEXT,
  phase TEXT NOT NULL,
  capabilities_json TEXT,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_plugins_category ON plugins(category);
CREATE INDEX idx_plugins_phase ON plugins(phase);
```

---

### 5.10 users

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT,
  email TEXT,
  source TEXT,
  phase TEXT NOT NULL,
  labels_json TEXT,
  annotations_json TEXT,
  spec_json TEXT NOT NULL,
  status_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
```

Indexes:

```sql
CREATE INDEX idx_users_source ON users(source);
CREATE INDEX idx_users_phase ON users(phase);
```

---

## 6. Audit Tables

### 6.1 audit_events

Audit events are append-only.

```sql
CREATE TABLE audit_events (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  actor_id TEXT,
  resource_kind TEXT,
  resource_id TEXT,
  workflow_id TEXT,
  task_id TEXT,
  request_id TEXT,
  message TEXT,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
```

Indexes:

```sql
CREATE INDEX idx_audit_events_actor_id ON audit_events(actor_id);
CREATE INDEX idx_audit_events_resource ON audit_events(resource_kind, resource_id);
CREATE INDEX idx_audit_events_workflow_id ON audit_events(workflow_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);
```

---

## 7. Migration Strategy

CPP must use explicit database migrations.

Recommended tool:

```text
Alembic
```

Migration rules:

```text
1. No manual schema mutation in application startup.
2. Every schema change must have a migration file.
3. Destructive migrations require review.
4. JSON shape changes must be backward compatible where possible.
5. Downgrade scripts are recommended for development but not mandatory for production.
```

---

## 8. SQLite To PostgreSQL Compatibility Rules

```text
1. Use TEXT ids instead of auto-increment integer ids.
2. Store timestamps as ISO-8601 UTC strings in SQLite.
3. Avoid SQLite-specific SQL where possible.
4. Use JSON text in SQLite and jsonb in PostgreSQL.
5. Avoid relying on SQLite foreign key enforcement in early V2.0.
6. Use application-level validation for cross-resource references.
```

---

## 9. Data Retention

Default retention proposal:

```text
Workflow: 90 days
Task: 90 days
Audit: 365 days
Backup metadata: until backup expires + 30 days
Deleted resource records: 30 days
```

Retention policy should be configurable in later implementation.

---

## 10. Review Items

Before freezing P2-01, confirm:

1. Should V2.0 use one table per resource instead of a single generic resources table?
2. Should spec/status remain JSON in V2.0?
3. Should foreign keys be enforced in SQLite V2.0 or delayed until PostgreSQL?
4. Should audit_events be database-backed immediately, replacing file-based audit logs?
5. Is SQLite -> PostgreSQL staged evolution acceptable?

---

## 11. Not Frozen Here

The following are deferred:

```text
ORM implementation details
Migration file layout
Repository pattern implementation
API response schemas
RBAC tables
Plugin registry package format
Multi-tenant schema separation
```
