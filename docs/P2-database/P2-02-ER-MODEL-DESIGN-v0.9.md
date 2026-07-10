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

These entities are derived from the frozen P1 resource model and P2 data architecture.

---

## 3. Logical ER Overview

```text
User
  │
  ├── creates ───────────────┐
  │                          ▼
  │                       Workflow
  │                          │
  │                          └── owns 1..N Task
  │
  └── emits 1..N AuditEvent

Cluster
  │
  ├── owns 1..N Node
  ├── owns 1..N StoragePool
  ├── owns 1..N StorageClass
  ├── owns 1..N VM
  ├── owns 1..N Backup
  ├── owns 1..N Workflow
  └── emits 1..N ResourceEvent

StoragePool
  └── owns 1..N StorageClass

StorageClass
  └── referenced by VM disks

VM
  ├── owns 0..N Backup
  ├── targeted by 0..N Workflow
  └── emits 0..N ResourceEvent

Backup
  ├── targets 1 resource
  └── created by 0..1 Workflow

Plugin
  └── provides capabilities for StoragePool / Backup / Identity / Observability
```

---

## 4. Entity Cardinality Matrix

| Source | Relationship | Target | Cardinality |
|---|---|---|---|
| Cluster | owns | Node | 1:N |
| Cluster | owns | StoragePool | 1:N |
| Cluster | owns | StorageClass | 1:N |
| Cluster | owns | VM | 1:N |
| Cluster | owns | Backup | 1:N |
| Cluster | owns | Workflow | 1:N |
| StoragePool | provides | StorageClass | 1:N |
| StorageClass | backs | VM disk | 1:N logical |
| VM | has | Backup | 1:N |
| Workflow | owns | Task | 1:N |
| User | creates | Workflow | 1:N |
| User | triggers | AuditEvent | 1:N |
| Resource | emits | ResourceEvent | 1:N |
| Workflow | emits | AuditEvent | 1:N |
| Task | emits | AuditEvent | 1:N |
| Plugin | provides | capability | 1:N embedded/list |

---

## 5. Cluster-Centric Model

Cluster is the top-level infrastructure aggregate.

```text
Cluster
 ├── Node
 ├── StoragePool
 ├── StorageClass
 ├── VM
 ├── Backup
 └── Workflow
```

Rules:

```text
1. Node, StoragePool, StorageClass, VM and Backup must belong to one Cluster.
2. Workflow may belong to one Cluster or be global.
3. Plugin and User are global resources.
4. AuditEvent and ResourceEvent may reference Cluster but are not owned by Cluster lifecycle.
```

---

## 6. Storage Model

Storage has two independent entities:

```text
StoragePool
StorageClass
```

StorageClass is not merely an attribute of StoragePool.

Relationship:

```text
StoragePool 1 -> N StorageClass
StorageClass N -> 1 Cluster
StorageClass N -> 1 StoragePool
```

Reason:

```text
1. StorageClass is independently manageable in Kubernetes.
2. Default class, reclaim policy and binding mode require independent governance.
3. VM disks and backups may reference StorageClass directly.
```

---

## 7. VM Model

VM belongs to exactly one Cluster and may reference multiple storage and network descriptors in spec.

```text
Cluster 1 -> N VM
VM 1 -> N logical disks
VM disk N -> 1 StorageClass logical reference
VM 1 -> N Backup
VM 1 -> N Workflow target references
```

In V2.0, VM disks and networks may be embedded inside VM.spec rather than normalized as first-class tables.

A future P1.x Network Domain may promote networks into first-class resources.

---

## 8. Backup Model

Backup is a unified entity.

Supported backup scopes:

```text
cluster
namespace
vm
pvc
etcd
```

Relationship:

```text
Backup N -> 1 Cluster
Backup N -> 0..1 Workflow
Backup N -> 1 target reference
```

The target is represented by:

```text
target_kind
target_id
target_ref
```

This allows Backup to target Cluster, VM, namespace, PVC or etcd snapshot without creating separate backup tables for each type.

---

## 9. Workflow and Task Model

Workflow is an orchestration entity.

Task is an execution entity.

Relationship:

```text
Workflow 1 -> N Task
Task N -> 0..1 Workflow
```

Task is allowed to exist without Workflow to support legacy direct playbook execution.

Rules:

```text
1. New multi-step operations should use Workflow.
2. Legacy single-playbook actions may create Task directly.
3. Task must always record executor_type, command_ref, status and log reference.
```

---

## 10. Event and Audit Model

CPP uses two event-like entities:

```text
ResourceEvent
AuditEvent
```

ResourceEvent records resource lifecycle and state transitions.

AuditEvent records actor-driven security and operation history.

Relationship:

```text
Resource 1 -> N ResourceEvent
User 1 -> N AuditEvent
Workflow 1 -> N AuditEvent
Task 1 -> N AuditEvent
```

Rules:

```text
1. ResourceEvent may be consumed by WebSocket, monitoring and UI.
2. AuditEvent is append-only and compliance-oriented.
3. A single operation may produce both ResourceEvent and AuditEvent.
```

---

## 11. Plugin Model

Plugin is global.

Plugin may provide capabilities for:

```text
StoragePool
Backup
Identity
Observability
VM
Network future extension
```

In V2.0, Plugin capability declarations may be stored as structured JSON/list fields.

Relationship is logical rather than strict foreign key:

```text
Plugin.capabilities -> services/features
StoragePool.spec.plugin -> Plugin.name or Plugin.id
```

---

## 12. User Model

User is a global identity entity.

Relationships:

```text
User 1 -> N Workflow created_by
User 1 -> N AuditEvent actor_id
```

Detailed RBAC relations are deferred to a future Identity/RBAC design.

---

## 13. Global Reference Pattern

Some entities need generic references to arbitrary resources.

The standard reference pattern is:

```text
target_kind
target_id
target_ref
```

Usage:

```text
Workflow target
Backup target
AuditEvent target
ResourceEvent subject
```

Rules:

```text
1. target_kind must match a known resource kind or extension kind.
2. target_id should be used for CPP-managed resources.
3. target_ref may be used for external resources such as Kubernetes namespace, PVC or etcd snapshot path.
```

---

## 14. ER Boundary Decisions

Frozen candidates:

```text
1. Cluster is the top-level infrastructure aggregate.
2. StorageClass is an independent entity.
3. Task may exist without Workflow.
4. Backup uses target_kind/target_id/target_ref instead of separate backup tables.
5. ResourceEvent and AuditEvent are separate entities.
6. VM disks and networks are embedded in VM.spec for V2.0.
7. Plugin capabilities are modeled as structured declarations, not hard foreign-key tables in V2.0.
```

---

## 15. Deferred To P2-03

The following are intentionally deferred:

```text
Physical table schema
Indexes
Foreign keys
JSON column strategy
Enum storage strategy
Alembic migration layout
SQLite/PostgreSQL compatibility details
```

---

## 16. Review Items

Before freezing P2-02, confirm:

1. Is Cluster accepted as the top-level infrastructure aggregate?
2. Is StorageClass accepted as an independent entity?
3. Is Task allowed to exist without Workflow?
4. Is generic target_kind/target_id/target_ref accepted for Backup, Workflow and Events?
5. Should ResourceEvent and AuditEvent remain separate entities?
6. Is embedding VM disks/networks in VM.spec acceptable for V2.0?
