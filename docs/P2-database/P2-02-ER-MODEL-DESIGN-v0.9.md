# P2-02 ER Model Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on:
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> Scope: CPP logical entity relationship model

---

## 1. Purpose

This document defines the logical ER model for CPP V2.0.

It translates the frozen resource model into entity relationships.

It does not define final SQL DDL. Physical tables, indexes, constraints and migrations are defined in later P2 documents.

---

## 2. Core Entities

CPP V2.0 contains the following primary entities:

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
AuditEvent
ResourceEvent
```

The following entities are logical extension entities and may be implemented after V2.0 core:

```text
Network
Approval
Policy
Role
Permission
```

---

## 3. ER Overview

Logical relationship overview:

```text
User
  ├── creates Workflow
  ├── triggers AuditEvent
  └── owns ResourceEvent actor context

Cluster
  ├── has many Node
  ├── has many StoragePool
  ├── has many StorageClass
  ├── has many VM
  ├── has many Backup
  └── has many Workflow

StoragePool
  └── has many StorageClass

VM
  ├── uses many StorageClass through disks/spec
  ├── has many Backup
  └── has many Workflow as target

Workflow
  ├── has many Task
  ├── targets one Resource optionally
  └── emits many ResourceEvent

Task
  ├── belongs to Workflow optionally
  └── emits ResourceEvent and AuditEvent

Plugin
  ├── provides capabilities for StoragePool/Backup/Identity/Observability
  └── emits ResourceEvent when lifecycle changes

AuditEvent
  └── references actor and target resource

ResourceEvent
  └── references resource and optional workflow/task
```

---

## 4. Relationship Cardinality

| Source | Target | Cardinality | Required | Notes |
|---|---|---:|---|---|
| Cluster | Node | 1:N | Node requires Cluster | Node belongs to exactly one managed cluster |
| Cluster | StoragePool | 1:N | StoragePool requires Cluster | StoragePool is cluster-scoped |
| Cluster | StorageClass | 1:N | StorageClass requires Cluster | StorageClass is independently addressable |
| StoragePool | StorageClass | 1:N | StorageClass requires StoragePool | StorageClass maps to one logical backend |
| Cluster | VM | 1:N | VM requires Cluster | VM is cluster-scoped and namespace-scoped |
| VM | Backup | 1:N | Optional | Backup may target VM, PVC, namespace, cluster or etcd |
| Cluster | Backup | 1:N | Backup requires Cluster | Every backup is cluster-scoped |
| Cluster | Workflow | 1:N | Optional | Some global workflows may have no cluster |
| Workflow | Task | 1:N | Task may exist without Workflow | Allows legacy direct task execution |
| User | Workflow | 1:N | Workflow requires creator when authenticated | created_by references User |
| User | AuditEvent | 1:N | Optional for system actors | System actors allowed |
| Resource | ResourceEvent | 1:N | Event requires target resource | ResourceEvent records lifecycle and state changes |
| Workflow | ResourceEvent | 1:N | Optional | Events may be workflow-generated |
| Task | ResourceEvent | 1:N | Optional | Events may be task-generated |
| Plugin | ResourceEvent | 1:N | Optional | Plugin lifecycle emits events |

---

## 5. Entity Definitions

### 5.1 Cluster

Cluster is the root entity for managed Kubernetes environments.

Key logical fields:

```yaml
Cluster:
  id: uuidv7
  kind: Cluster
  name: string
  metadata: object
  spec: object
  status: object
  generation: integer
  resource_version: string
  created_at: datetime
  updated_at: datetime
  deleted_at: datetime|null
```

Relationships:

```text
Cluster 1 -> N Node
Cluster 1 -> N StoragePool
Cluster 1 -> N StorageClass
Cluster 1 -> N VM
Cluster 1 -> N Backup
Cluster 1 -> N Workflow
```

Deletion rule:

```text
Cluster deletion is soft deletion by default.
Child resources must not be hard deleted automatically.
Destructive cleanup must be represented by Workflow.
```

---

### 5.2 Node

Node represents a physical or virtual host in a Cluster.

Key logical fields:

```yaml
Node:
  id: uuidv7
  cluster_id: uuidv7
  kind: Node
  name: string
  spec: object
  status: object
```

Relationships:

```text
Node N -> 1 Cluster
Node 1 -> N ResourceEvent
```

Placement notes:

```text
VM runtime placement may reference Node by node name or node id.
The ER model does not require a strict VM -> Node foreign key because KubeVirt placement can change externally.
```

---

### 5.3 StoragePool

StoragePool represents a logical storage backend.

Key logical fields:

```yaml
StoragePool:
  id: uuidv7
  cluster_id: uuidv7
  kind: StoragePool
  name: string
  spec: object
  status: object
```

Relationships:

```text
StoragePool N -> 1 Cluster
StoragePool 1 -> N StorageClass
StoragePool 1 -> N ResourceEvent
```

---

### 5.4 StorageClass

StorageClass is an independent resource and aggregate root.

Key logical fields:

```yaml
StorageClass:
  id: uuidv7
  cluster_id: uuidv7
  storage_pool_id: uuidv7
  kind: StorageClass
  name: string
  spec: object
  status: object
```

Relationships:

```text
StorageClass N -> 1 Cluster
StorageClass N -> 1 StoragePool
StorageClass 1 -> N ResourceEvent
```

Design decision:

```text
StorageClass remains independent because governance, default selection, reclaim policy and binding mode require separate lifecycle.
```

---

### 5.5 VM

VM represents a KubeVirt VM.

Key logical fields:

```yaml
VM:
  id: uuidv7
  cluster_id: uuidv7
  namespace: string
  kind: VM
  name: string
  spec: object
  status: object
```

Relationships:

```text
VM N -> 1 Cluster
VM 1 -> N Backup
VM 1 -> N Workflow as target
VM 1 -> N ResourceEvent
```

Storage relationship:

```text
VM uses StorageClass through disk spec and Kubernetes PVC/DataVolume references.
This is modeled logically, not as a mandatory relational join table in v0.9.
```

---

### 5.6 Backup

Backup represents etcd, VM, PVC, namespace or cluster backup.

Key logical fields:

```yaml
Backup:
  id: uuidv7
  cluster_id: uuidv7
  target_kind: string
  target_id: uuidv7|string|null
  kind: Backup
  name: string
  spec: object
  status: object
```

Relationships:

```text
Backup N -> 1 Cluster
Backup N -> 0..1 VM
Backup N -> 0..1 Workflow
Backup 1 -> N ResourceEvent
```

Target rule:

```text
target_kind + target_id identify the protected object.
The target may be VM, PVC, Namespace, Cluster or etcd logical target.
```

---

### 5.7 Workflow

Workflow represents orchestrated operation state.

Key logical fields:

```yaml
Workflow:
  id: uuidv7
  cluster_id: uuidv7|null
  target_kind: string|null
  target_id: uuidv7|string|null
  created_by: uuidv7|string
  kind: Workflow
  name: string
  spec: object
  status: object
```

Relationships:

```text
Workflow 1 -> N Task
Workflow N -> 0..1 Cluster
Workflow N -> 0..1 target Resource
Workflow 1 -> N ResourceEvent
Workflow 1 -> N AuditEvent
```

---

### 5.8 Task

Task represents a single executable unit.

Key logical fields:

```yaml
Task:
  id: uuidv7
  workflow_id: uuidv7|null
  kind: Task
  name: string
  spec: object
  status: object
```

Relationships:

```text
Task N -> 0..1 Workflow
Task 1 -> N ResourceEvent
Task 1 -> N AuditEvent
```

Design decision:

```text
Task may exist without Workflow to support direct legacy playbook/API execution.
```

---

### 5.9 Plugin

Plugin represents installed extension capability.

Key logical fields:

```yaml
Plugin:
  id: uuidv7
  kind: Plugin
  name: string
  category: string
  version: string
  spec: object
  status: object
```

Relationships:

```text
Plugin 1 -> N ResourceEvent
Plugin may be referenced by StoragePool, Backup or Identity configuration through spec fields.
```

---

### 5.10 User

User represents authenticated subject.

Key logical fields:

```yaml
User:
  id: uuidv7
  kind: User
  name: string
  spec: object
  status: object
```

Relationships:

```text
User 1 -> N Workflow created_by
User 1 -> N AuditEvent actor
```

RBAC note:

```text
Role, Permission and Policy are deferred to Identity/RBAC design and are not part of the P2-02 core ER model.
```

---

### 5.11 AuditEvent

AuditEvent records security and operation history.

Key logical fields:

```yaml
AuditEvent:
  id: uuidv7
  actor_id: uuidv7|string|null
  actor_type: user | system | service
  action: string
  target_kind: string|null
  target_id: uuidv7|string|null
  result: success | failure | denied
  reason: string|null
  created_at: datetime
```

Relationships:

```text
AuditEvent N -> 0..1 User
AuditEvent N -> 0..1 Workflow
AuditEvent N -> 0..1 Task
AuditEvent N -> 0..1 target Resource
```

Audit rule:

```text
AuditEvent is append-only.
It must not be updated in place.
```

---

### 5.12 ResourceEvent

ResourceEvent records resource lifecycle and state changes.

Key logical fields:

```yaml
ResourceEvent:
  id: uuidv7
  resource_kind: string
  resource_id: uuidv7|string
  event_type: string
  reason: string|null
  message: string|null
  workflow_id: uuidv7|null
  task_id: uuidv7|null
  created_at: datetime
```

Relationships:

```text
ResourceEvent N -> 1 target Resource
ResourceEvent N -> 0..1 Workflow
ResourceEvent N -> 0..1 Task
```

---

## 6. Polymorphic Target References

Several entities need to reference arbitrary resources.

Examples:

```text
Workflow.target_kind + Workflow.target_id
Backup.target_kind + Backup.target_id
AuditEvent.target_kind + AuditEvent.target_id
ResourceEvent.resource_kind + ResourceEvent.resource_id
```

P2-02 accepts polymorphic references as a logical model.

Reason:

```text
1. Workflow may target VM, Cluster, StoragePool, Backup or other future resources.
2. Audit and event systems must support all resource kinds.
3. Strict foreign keys for polymorphic targets would complicate schema evolution.
```

Physical schema may enforce partial constraints where practical, but the logical model is polymorphic.

---

## 7. Soft Deletion Relationships

All core resources use soft deletion.

Rules:

```text
1. Parent soft deletion does not automatically hard-delete children.
2. Child cleanup is performed by Workflow where needed.
3. Query APIs hide deleted resources by default.
4. AuditEvent and ResourceEvent are not soft-deleted by normal resource deletion.
```

---

## 8. Event and Audit Relationship

ResourceEvent and AuditEvent are different.

```text
ResourceEvent = what changed on a resource
AuditEvent = who did what and with what result
```

One user operation may create both:

```text
User starts VM
  -> AuditEvent(action=vm.start, result=success)
  -> ResourceEvent(event_type=VMStartRequested)
  -> WorkflowCreated
  -> TaskStarted
  -> VMStarted
```

---

## 9. ER Constraints Candidate

The following constraints are logical candidates for P2-03 physical schema:

```text
clusters.name unique where deleted_at is null
nodes unique(cluster_id, name) where deleted_at is null
storage_pools unique(cluster_id, name) where deleted_at is null
storage_classes unique(cluster_id, name) where deleted_at is null
vms unique(cluster_id, namespace, name) where deleted_at is null
plugins unique(name, version) where deleted_at is null
users unique(name) where deleted_at is null
workflow.id globally unique
task.id globally unique
audit_event.id globally unique
resource_event.id globally unique
```

---

## 10. Deferred Items

The following are deferred to P2-03 or later specs:

```text
Physical table DDL
Concrete indexes
Foreign key enforcement strategy
JSON column strategy
SQLite/PostgreSQL compatibility details
Alembic migration layout
RBAC role/permission tables
Network resource ER model
Retention and partition strategy for events/audit
```

---

## 11. Review Items

Before freezing P2-02, confirm:

1. Is the ER model centered on Cluster as the primary infrastructure root acceptable?
2. Is StorageClass as an independent aggregate root acceptable?
3. Is Task as optionally independent from Workflow acceptable?
4. Are polymorphic target references acceptable for Workflow, Backup, AuditEvent and ResourceEvent?
5. Should ResourceEvent and AuditEvent remain separate entities?
6. Should VM -> StorageClass remain logical through spec rather than a mandatory join table in V2.0?
