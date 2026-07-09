# FROZEN-P2-02 ER Model v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> Scope: CPP logical entity relationship model
> Rule: Any incompatible change to entity identity, aggregate ownership, cardinality, or event separation must create a new design version and pass review again.

---

## 1. Purpose

This frozen specification defines the logical ER model for CPP V2.0.

It translates the frozen resource model into entity relationships.

This document does not define final SQL DDL. Physical tables, indexes, constraints and migrations are defined in later P2 documents.

---

## 2. Frozen Core Entities

CPP V2.0 freezes the following primary entities:

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

The first ten entities are frozen resources from P1. AuditEvent and ResourceEvent are supporting entities required by P2-01.

---

## 3. High-Level ER Diagram

```text
Cluster
  ├── Node
  ├── StoragePool
  │     └── StorageClass
  ├── VM
  │     └── Backup
  ├── Workflow
  │     └── Task
  ├── ResourceEvent
  └── AuditEvent

User
  ├── Workflow(created_by)
  ├── AuditEvent(actor)
  └── ResourceEvent(actor optional)

Plugin
  ├── StoragePool(plugin)
  └── future extension resources
```

---

## 4. Cluster Relationships

Cluster is the top-level aggregate boundary for managed infrastructure.

Relationships:

```text
Cluster 1 -> N Node
Cluster 1 -> N StoragePool
Cluster 1 -> N StorageClass
Cluster 1 -> N VM
Cluster 1 -> N Backup
Cluster 1 -> N Workflow
Cluster 1 -> N ResourceEvent
Cluster 1 -> N AuditEvent optional
```

Rules:

```text
1. Node, StoragePool, StorageClass, VM and Backup must belong to a Cluster.
2. Workflow may be cluster-scoped or platform-scoped.
3. User and Plugin are platform-scoped resources.
```

---

## 5. Storage Relationships

```text
StoragePool 1 -> N StorageClass
StorageClass N -> 1 StoragePool
StorageClass N -> 1 Cluster
```

Rules:

```text
1. StorageClass is an independent resource.
2. StorageClass must reference one StoragePool when managed by CPP.
3. Externally discovered StorageClass may have storage_pool_id=null until classified.
```

---

## 6. VM Relationships

```text
VM N -> 1 Cluster
VM N -> N StorageClass logically through disks/PVC/DataVolume references
VM 1 -> N Backup
VM 1 -> N Workflow as target
```

Rules:

```text
1. VM belongs to one Cluster.
2. VM identity includes cluster_id, namespace and name.
3. VM disk references are stored in spec and may reference StorageClass by name or id.
4. Backup may target a VM.
```

---

## 7. Backup Relationships

```text
Backup N -> 1 Cluster
Backup N -> 0..1 VM
Backup N -> 0..1 Workflow
Backup N -> 0..1 User created_by through Workflow or Audit
```

Backup target model:

```text
target_kind: cluster | namespace | vm | pvc | etcd
target_id: resource id or external reference
```

Rules:

```text
1. Backup is standalone and queryable.
2. Backup may be created by Workflow.
3. Backup may represent etcd snapshot, Velero backup, VM backup, PVC snapshot or cluster backup.
```

---

## 8. Workflow and Task Relationships

```text
Workflow 1 -> N Task
Task N -> 0..1 Workflow
Workflow N -> 0..1 target resource
Task N -> 0..1 target resource optional
```

Rules:

```text
1. Workflow is an aggregate root.
2. Task is also an independent resource for legacy direct actions.
3. A Task may exist without a Workflow.
4. Workflow target is represented by target_kind + target_id.
```

---

## 9. Plugin Relationships

```text
Plugin 1 -> N resource capabilities
Plugin 0..N -> StoragePool by plugin name or plugin_id
```

Rules:

```text
1. Plugin is platform-scoped.
2. Plugin must declare capabilities.
3. Plugin must not directly own core resources.
4. Plugin can enable or reconcile resources through public APIs and workflows.
```

---

## 10. User Relationships

```text
User 1 -> N Workflow created_by
User 1 -> N AuditEvent actor
User 1 -> N ResourceEvent actor optional
```

Rules:

```text
1. User is platform-scoped.
2. RBAC relationships are deferred to Identity/RBAC spec.
3. User deletion must preserve audit history.
```

---

## 11. Event Relationships

### 11.1 ResourceEvent

ResourceEvent records resource lifecycle and status transitions.

```text
ResourceEvent N -> 1 Resource logical reference
ResourceEvent N -> 0..1 User actor
ResourceEvent N -> 0..1 Workflow
ResourceEvent N -> 0..1 Task
```

### 11.2 AuditEvent

AuditEvent records security and operation history.

```text
AuditEvent N -> 0..1 User actor
AuditEvent N -> 0..1 target resource
AuditEvent N -> 0..1 Workflow
AuditEvent N -> 0..1 Task
```

Rules:

```text
1. AuditEvent is append-only.
2. ResourceEvent may be used for WebSocket and UI event streams.
3. AuditEvent and ResourceEvent are not substitutes for resource status.
```

---

## 12. Logical Cardinality Summary

| Source | Target | Cardinality |
|---|---|---|
| Cluster | Node | 1:N |
| Cluster | StoragePool | 1:N |
| StoragePool | StorageClass | 1:N |
| Cluster | VM | 1:N |
| VM | Backup | 1:N |
| Cluster | Backup | 1:N |
| Workflow | Task | 1:N |
| User | Workflow | 1:N |
| User | AuditEvent | 1:N |
| Resource | ResourceEvent | 1:N |
| Plugin | StoragePool | 1:N optional |

---

## 13. Identity and Uniqueness

Recommended unique constraints:

```text
Cluster: name
Node: cluster_id + hostname
StoragePool: cluster_id + name
StorageClass: cluster_id + name
VM: cluster_id + namespace + name
Backup: id
Workflow: id
Task: id
Plugin: name + version
User: username + source
```

All public resource identifiers use UUIDv7-compatible ids.

---

## 14. Soft Delete Behavior

Soft deletion applies to core resources.

Rules:

```text
1. deleted_at marks resource deletion.
2. Unique constraints must consider deleted_at where supported.
3. AuditEvent is never soft-deleted by normal resource deletion.
4. ResourceEvent retention is defined separately.
```

---

## 15. Frozen Review Decisions

The following review decisions are frozen:

```text
1. Cluster remains the top-level infrastructure aggregate.
2. User and Plugin are platform-scoped, not cluster-scoped.
3. StorageClass remains independent and references StoragePool.
4. Task remains standalone and optionally attached to Workflow.
5. AuditEvent and ResourceEvent are separate entities.
```

---

## 16. Deferred To Later Specs

The following are intentionally deferred:

```text
Physical table definitions
Indexes
Foreign key enforcement details
Polymorphic target implementation
ResourceEvent retention policy
RBAC join tables
Multi-cluster federation tables
```

Next document:

```text
P2-03 Table Schema and Index Design
```
