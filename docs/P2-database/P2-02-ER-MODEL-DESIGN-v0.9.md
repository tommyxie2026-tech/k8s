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

---

## 3. High-Level ER View

```text
User
  ├── creates Workflow
  ├── triggers AuditEvent
  └── owns ResourceEvent indirectly

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

Plugin
  ├── provides capability to StoragePool
  ├── provides capability to Backup
  └── emits ResourceEvent
```

---

## 4. Entity: Cluster

Cluster is the top-level infrastructure aggregate.

Relationships:

```text
Cluster 1 -> N Node
Cluster 1 -> N StoragePool
Cluster 1 -> N StorageClass
Cluster 1 -> N VM
Cluster 1 -> N Backup
Cluster 1 -> N Workflow
Cluster 1 -> N ResourceEvent
Cluster 1 -> N AuditEvent
```

Logical fields:

```yaml
Cluster:
  id: uuidv7
  name: string
  metadata: json
  spec: json
  status: json
```

Rules:

```text
1. Cluster deletion is soft delete.
2. Deleting a Cluster must not automatically hard-delete child resources.
3. Cluster lifecycle operations must be represented by Workflow.
```

---

## 5. Entity: Node

Node belongs to exactly one Cluster.

Relationships:

```text
Node N -> 1 Cluster
Node 1 -> N VM runtime placement optional
Node 1 -> N ResourceEvent
```

Rules:

```text
1. Node is not a standalone infrastructure universe.
2. Node must always reference cluster_id.
3. VM placement may refer to node_id or observed node_name depending on discovery maturity.
```

---

## 6. Entity: StoragePool

StoragePool represents storage backend capability.

Relationships:

```text
StoragePool N -> 1 Cluster
StoragePool 1 -> N StorageClass
StoragePool 1 -> N Backup optional
StoragePool N -> 1 Plugin optional
```

Rules:

```text
1. StoragePool is independent from StorageClass.
2. StoragePool may be created by a storage plugin.
3. StoragePool lifecycle changes must emit ResourceEvent.
```

---

## 7. Entity: StorageClass

StorageClass is an independent resource and belongs to one Cluster and one StoragePool.

Relationships:

```text
StorageClass N -> 1 Cluster
StorageClass N -> 1 StoragePool
StorageClass 1 -> N VM disk references indirectly
```

Rules:

```text
1. StorageClass may be managed even if the StoragePool is degraded.
2. Default StorageClass selection is a governance concern.
3. StorageClass deletion must not silently delete volumes.
```

---

## 8. Entity: VM

VM represents a KubeVirt VirtualMachine.

Relationships:

```text
VM N -> 1 Cluster
VM 1 -> N Backup
VM 1 -> N Workflow
VM N -> 1 Node optional observed placement
VM N -> N StorageClass indirect through disks
```

Rules:

```text
1. VM lifecycle actions must be Workflow based.
2. VM observed placement belongs to status.
3. VM disk details may be JSON in V2.0 and normalized later if required.
```

---

## 9. Entity: Backup

Backup is unified across etcd, VM, PVC, namespace and cluster scopes.

Relationships:

```text
Backup N -> 1 Cluster
Backup N -> 0..1 VM
Backup N -> 0..1 Workflow
Backup N -> 0..1 StoragePool
```

Rules:

```text
1. Backup target is represented by target_kind + target_id.
2. Backup location must be stored in spec.
3. Backup runtime result must be stored in status.
```

---

## 10. Entity: Workflow

Workflow represents orchestration.

Relationships:

```text
Workflow N -> 0..1 Cluster
Workflow N -> 1 User created_by
Workflow 1 -> N Task
Workflow N -> 0..1 target resource via target_kind + target_id
```

Rules:

```text
1. Workflow may target any resource kind.
2. Workflow owns orchestration state, not resource truth.
3. Destructive workflows must store confirmation evidence.
```

---

## 11. Entity: Task

Task is an executable unit and may exist inside or outside Workflow.

Relationships:

```text
Task N -> 0..1 Workflow
Task N -> 0..1 Cluster
Task N -> 0..1 User created_by
```

Rules:

```text
1. Task may exist independently for legacy direct playbook execution.
2. Task must record executor_type.
3. Task logs are referenced, not stored as large inline database blobs in V2.0.
```

---

## 12. Entity: Plugin

Plugin represents installed platform extension.

Relationships:

```text
Plugin 1 -> N StoragePool optional
Plugin 1 -> N ResourceEvent
Plugin 1 -> N AuditEvent
```

Rules:

```text
1. Plugin capability is declared in spec.
2. Plugin health is stored in status.
3. Plugin must not own private persistent state outside Resource model without a design extension.
```

---

## 13. Entity: User

User represents authenticated actor.

Relationships:

```text
User 1 -> N Workflow
User 1 -> N Task
User 1 -> N AuditEvent
```

Rules:

```text
1. User is a resource.
2. RBAC details are deferred to the Identity/RBAC specification.
3. User source may be local, OIDC, LDAP or external.
```

---

## 14. Entity: ResourceEvent

ResourceEvent records resource lifecycle and state changes.

Relationships:

```text
ResourceEvent N -> 1 resource via resource_kind + resource_id
ResourceEvent N -> 0..1 Cluster
ResourceEvent N -> 0..1 Workflow
ResourceEvent N -> 0..1 Task
```

Rules:

```text
1. ResourceEvent is append-only.
2. ResourceEvent is used by WebSocket, audit, monitoring and UI timelines.
3. ResourceEvent must not replace current resource status.
```

---

## 15. Entity: AuditEvent

AuditEvent records user and security relevant operations.

Relationships:

```text
AuditEvent N -> 0..1 User actor
AuditEvent N -> 0..1 target resource via target_kind + target_id
AuditEvent N -> 0..1 Workflow
AuditEvent N -> 0..1 Task
```

Rules:

```text
1. AuditEvent is append-only.
2. AuditEvent must include actor, action, target, result and timestamp where applicable.
3. AuditEvent must not be soft-deleted by normal resource deletion.
```

---

## 16. Generic Target Reference Pattern

For cross-resource references where target type varies, CPP uses:

```yaml
target_kind: string
target_id: uuidv7
```

Used by:

```text
Workflow
Backup
AuditEvent
ResourceEvent
```

Reason:

```text
1. Workflow may target Cluster, VM, StoragePool, Backup or Plugin.
2. Backup may target etcd, VM, PVC, namespace or cluster.
3. Audit/Event must support all resource kinds.
```

---

## 17. Cardinality Summary

```text
Cluster 1 -> N Node
Cluster 1 -> N StoragePool
Cluster 1 -> N StorageClass
StoragePool 1 -> N StorageClass
Cluster 1 -> N VM
VM 1 -> N Backup
Cluster 1 -> N Backup
Workflow 1 -> N Task
User 1 -> N Workflow
User 1 -> N AuditEvent
Resource 1 -> N ResourceEvent
Resource 1 -> N AuditEvent
Plugin 1 -> N StoragePool optional
```

---

## 18. Normalization Strategy

V2.0 uses mixed normalization.

Normalized:

```text
Core resources
Workflow
Task
AuditEvent
ResourceEvent
```

JSON payload:

```text
metadata
labels
annotations
spec
status
VM disks/networks
Plugin capabilities
Node hardware summary
```

Reason:

```text
1. Resource shape must remain flexible during V2.0.
2. API and Workflow should stabilize before over-normalizing internals.
3. PostgreSQL JSONB can later index high-value fields.
```

---

## 19. ER Review Items

Before freezing P2-02, confirm:

```text
1. Cluster is the top-level infrastructure aggregate.
2. StorageClass remains independent and references StoragePool.
3. Task may exist outside Workflow.
4. Backup uses target_kind + target_id for unified backup target modeling.
5. ResourceEvent and AuditEvent are separate entities.
6. metadata/spec/status remain JSON payloads in V2.0.
```

---

## 20. Deferred To P2-03

The following are deferred:

```text
Concrete SQL table columns
Indexes
Foreign key constraints
JSON index strategy
Alembic migration layout
SQLite/PostgreSQL compatibility details
```
