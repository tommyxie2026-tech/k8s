# P1-01 Domain Model Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on: FROZEN-P0-02 System Architecture v1.0
> Scope: CPP core domain model

---

## 1. Purpose

This document defines the first version of the CPP domain model.

The domain model is the shared language for:

```text
API design
Database design
Workflow design
RBAC design
Audit design
Plugin SDK design
Web Console design
```

This document follows the frozen P0-02 principle:

> Everything Is A Resource.

---

## 2. Domain Boundaries

CPP V2.0 contains the following core domains:

```text
Cluster Domain
Node Domain
Storage Domain
Virtualization Domain
Backup Domain
Workflow Domain
Task Runtime Domain
Plugin Domain
Identity Domain
Observability Domain
```

Each domain owns a set of resources and lifecycle rules.

---

## 3. Universal Resource Contract

All resources must share a common contract.

```yaml
Resource:
  id: string
  kind: string
  name: string
  display_name: string
  description: string
  labels: map[string]string
  annotations: map[string]string
  status: string
  spec: object
  created_at: datetime
  updated_at: datetime
  deleted_at: datetime|null
```

Rules:

```text
1. Every resource must have id, kind, name and status.
2. spec is desired state.
3. status is observed state.
4. labels are query and grouping metadata.
5. annotations are non-query metadata.
6. deleted_at supports soft delete.
```

---

## 4. Core Resources

Frozen core resource kinds from P0-02:

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
```

P1 adds the following supporting resources:

```text
Network
Snapshot
Restore
AuditEvent
CredentialRef
Inventory
```

These supporting resources require review before freeze.

---

## 5. Cluster Domain

### 5.1 Cluster

Cluster represents a managed Kubernetes cluster.

```yaml
Cluster:
  id: string
  name: string
  version: string
  mode: standalone|ha|management|edge
  api_endpoint: string
  kubeconfig_ref: CredentialRef
  status: pending|ready|degraded|failed|unknown
  node_count: int
  vm_count: int
  storage_summary: object
```

Lifecycle:

```text
Created -> Provisioning -> Ready -> Degraded -> Failed
Ready -> Upgrading -> Ready
Ready -> Deleting -> Deleted
```

Cluster owns:

```text
Node
StoragePool
StorageClass
VM
Backup
Workflow
```

---

## 6. Node Domain

### 6.1 Node

Node represents a physical or virtual node in a cluster.

```yaml
Node:
  id: string
  cluster_id: string
  hostname: string
  ip_addresses: list[string]
  roles: list[string]
  labels: map[string]string
  taints: list[object]
  cpu: object
  memory: object
  disks: list[object]
  nics: list[object]
  gpu: list[object]
  status: ready|not_ready|cordoned|draining|failed|unknown
```

Node roles:

```text
control-plane
compute
storage
vm
gpu
edge
```

---

## 7. Storage Domain

### 7.1 StoragePool

StoragePool represents a logical storage capability.

```yaml
StoragePool:
  id: string
  cluster_id: string
  name: string
  type: local_lvm|nfs|iscsi|ceph_rbd|cephfs|external
  capacity_total: int
  capacity_used: int
  reclaim_policy: retain|delete
  failure_domain: node|rack|zone|region
  status: ready|degraded|failed|unknown
```

### 7.2 StorageClass

StorageClass represents a Kubernetes StorageClass managed by CPP.

```yaml
StorageClass:
  id: string
  cluster_id: string
  storage_pool_id: string
  name: string
  provisioner: string
  access_modes: list[string]
  volume_binding_mode: immediate|wait_for_first_consumer
  reclaim_policy: retain|delete
  allow_volume_expansion: bool
  default: bool
  status: ready|degraded|failed|unknown
```

### 7.3 Snapshot

Snapshot represents a point-in-time copy of a PVC or VM disk.

```yaml
Snapshot:
  id: string
  cluster_id: string
  source_kind: pvc|vm|disk
  source_ref: string
  snapshot_class: string
  status: creating|ready|failed|deleting
```

---

## 8. Virtualization Domain

### 8.1 VM

VM represents a KubeVirt VirtualMachine.

```yaml
VM:
  id: string
  cluster_id: string
  namespace: string
  name: string
  cpu: int
  memory: string
  disks: list[object]
  networks: list[object]
  node_selector: map[string]string
  status: stopped|starting|running|stopping|error|unknown
  backup_policy_id: string|null
```

VM lifecycle:

```text
Stopped -> Starting -> Running -> Stopping -> Stopped
Running -> Error
Stopped -> Deleting -> Deleted
```

VM operations must be expressed as Workflow.

---

## 9. Backup Domain

### 9.1 Backup

Backup represents a backup operation or backup artifact.

```yaml
Backup:
  id: string
  cluster_id: string
  name: string
  type: etcd|velero|vm|pvc|snapshot
  source_kind: cluster|namespace|vm|pvc
  source_ref: string
  target: local|nfs|s3
  status: pending|running|succeeded|failed|expired
  started_at: datetime|null
  finished_at: datetime|null
```

### 9.2 Restore

Restore represents a restore operation.

```yaml
Restore:
  id: string
  cluster_id: string
  backup_id: string
  target_namespace: string|null
  status: pending|running|succeeded|failed|cancelled
  destructive: bool
  confirm_required: bool
```

---

## 10. Workflow Domain

### 10.1 Workflow

Workflow represents an orchestration instance.

```yaml
Workflow:
  id: string
  name: string
  template: string
  status: pending|running|succeeded|failed|cancelled
  destructive: bool
  params: object
  created_by: string
  started_at: datetime|null
  finished_at: datetime|null
```

### 10.2 Task

Task represents an executable unit in a workflow.

```yaml
Task:
  id: string
  workflow_id: string
  name: string
  executor: ansible|kubectl|virtctl|helm|terraform|shell
  command: list[string]
  status: pending|running|succeeded|failed|cancelled
  return_code: int|null
  log_ref: string
```

---

## 11. Plugin Domain

### 11.1 Plugin

Plugin represents an extension installed into CPP.

```yaml
Plugin:
  id: string
  name: string
  category: storage|network|identity|vm|backup|observability
  version: string
  provider: string
  status: installed|enabled|disabled|failed
  capabilities: list[string]
```

Plugins must not write directly to the database.

---

## 12. Identity Domain

### 12.1 User

User represents a platform identity.

```yaml
User:
  id: string
  username: string
  display_name: string
  email: string
  source: local|oidc|ldap
  status: active|disabled|locked
```

Future resources:

```text
Role
RoleBinding
Policy
Token
```

These are not frozen in P1-01.

---

## 13. Observability Domain

### 13.1 AuditEvent

AuditEvent records platform activity.

```yaml
AuditEvent:
  id: string
  actor: string
  action: string
  resource_kind: string
  resource_id: string
  result: success|failure|denied
  message: string
  created_at: datetime
```

AuditEvent is append-only.

---

## 14. Aggregate Boundaries

Suggested aggregate roots:

```text
Cluster
VM
Workflow
Backup
Plugin
User
```

Cluster aggregate includes Node and StoragePool references but does not own their full lifecycle in database terms.

Workflow aggregate owns Task lifecycle.

Backup aggregate owns Restore references.

---

## 15. Review Items

Before freezing P1-01, confirm:

```text
1. Whether supporting resources Snapshot, Restore, AuditEvent, CredentialRef and Inventory should be frozen in V2.0.
2. Whether Network should be included in V2.0 or delayed to V2.1.
3. Whether User should be minimal in V2.0 and RBAC delayed to a later spec.
4. Whether Task is a child of Workflow only, or can also exist independently.
5. Whether Backup should represent both operation and artifact, or split into BackupJob and BackupArtifact.
```

---

## 16. Next Step

After review, generate:

```text
FROZEN-P1-01-DOMAIN-MODEL-v1.0.md
```

Then continue to:

```text
P2 Database Design
P3 API Specification
P4 Workflow Engine Specification
```
