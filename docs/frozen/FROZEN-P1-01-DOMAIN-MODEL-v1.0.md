# FROZEN-P1-01 Domain Model v1.0

> Status: FROZEN
> Version: v1.0
> Depends on: FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> Scope: CPP unified resource domain model
> Rule: Any incompatible change must create a new design version and pass review again.

---

## 1. Purpose

This document freezes the CPP V2.0 domain model.

It implements the P0-02 frozen principle:

```text
Everything Is A Resource
```

The domain model is the shared language for API design, database design, workflow design, RBAC design, audit design, plugin SDK design and Web Console design.

---

## 2. Frozen Domains

CPP V2.0 freezes the following core domains:

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

Network Domain is accepted as a P1 extension domain but is not required for V2.0 core implementation.

---

## 3. Frozen Core Resources

The following core resources are frozen:

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

No module may introduce a duplicated resource concept without a new design review.

---

## 4. Universal Resource Contract

All resources must share this common contract:

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
  deleted_at: datetime | null
```

Rules:

```text
1. Every resource must have id, kind, name and status.
2. spec is desired state.
3. status is observed state.
4. labels are query and grouping metadata.
5. annotations are non-query metadata.
6. deleted_at enables soft deletion where applicable.
```

---

## 5. Cluster Resource

Cluster represents a Kubernetes cluster managed or observed by CPP.

```yaml
Cluster:
  id: string
  name: string
  provider: string
  mode: standalone | ha | management | edge
  kubernetes_version: string
  api_endpoint: string
  control_plane_endpoint: string
  status: provisioning | ready | degraded | failed | deleting
  inventory_ref: string
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

---

## 6. Node Resource

Node represents a physical or virtual host that belongs to a Cluster.

```yaml
Node:
  id: string
  cluster_id: string
  hostname: string
  management_ip: string
  roles: list[string]
  labels: map[string]string
  taints: list[string]
  cpu_total: integer
  memory_total: integer
  disk_summary: json
  nic_summary: json
  gpu_summary: json
  status: unknown | ready | not_ready | cordoned | draining | failed
```

Node does not own VM lifecycle or storage provisioning logic.

---

## 7. StoragePool Resource

StoragePool represents a logical storage backend available to a Cluster.

```yaml
StoragePool:
  id: string
  cluster_id: string
  name: string
  type: local | nfs | iscsi | ceph-rbd | cephfs | external
  plugin: string
  capacity_total: integer
  capacity_used: integer
  snapshot_supported: boolean
  expansion_supported: boolean
  access_modes: list[string]
  status: unknown | ready | degraded | failed | disabled
```

Relationships:

```text
StoragePool 1 -> N StorageClass
StoragePool N -> 1 Cluster
StoragePool N -> N Node optional
```

---

## 8. StorageClass Resource

Decision: StorageClass is frozen as a standalone resource.

Reason:

```text
1. Kubernetes StorageClass is already a first-class resource.
2. Governance requires direct query and policy evaluation.
3. VM disks, PVCs and snapshot policy need stable references to StorageClass.
```

```yaml
StorageClass:
  id: string
  cluster_id: string
  storage_pool_id: string
  name: string
  provisioner: string
  reclaim_policy: Delete | Retain
  volume_binding_mode: Immediate | WaitForFirstConsumer
  allow_volume_expansion: boolean
  is_default: boolean
  status: active | deprecated | disabled | missing
```

---

## 9. VM Resource

VM represents a KubeVirt VirtualMachine managed by CPP.

```yaml
VM:
  id: string
  cluster_id: string
  namespace: string
  name: string
  cpu: integer
  memory: integer
  disks: list[object]
  networks: list[object]
  node_selector: map[string]string
  status: stopped | starting | running | stopping | migrating | error | unknown
  backup_policy_id: string | null
```

VM start, stop, backup, restore and migration must be represented as Workflow operations.

---

## 10. Backup Resource

Decision: Backup is a unified resource covering etcd, VM, PVC, namespace and cluster backups.

```yaml
Backup:
  id: string
  cluster_id: string
  scope: cluster | namespace | vm | pvc | etcd
  target_ref: string
  backend: local | nfs | s3 | external
  location: string
  status: pending | running | succeeded | failed | expired
  created_by_workflow_id: string
  expires_at: datetime | null
```

Backup does not directly execute backup logic. Backup execution is modeled through Workflow and Task.

---

## 11. Workflow Resource

Workflow represents an orchestrated operation composed of ordered steps.

```yaml
Workflow:
  id: string
  name: string
  cluster_id: string | null
  target_kind: string | null
  target_id: string | null
  destructive: boolean
  status: pending | running | succeeded | failed | cancelled
  created_by: string
  started_at: datetime | null
  finished_at: datetime | null
```

Workflow owns orchestration state. It must not execute commands directly.

---

## 12. Task Resource

Decision: Task may exist independently outside Workflow for legacy single-playbook actions.

```yaml
Task:
  id: string
  workflow_id: string | null
  name: string
  executor_type: ansible | kubectl | virtctl | helm | terraform | shell
  command_ref: string
  status: pending | queued | running | succeeded | failed | cancelled
  return_code: integer | null
  log_path: string
  started_at: datetime | null
  finished_at: datetime | null
```

Task owns execution state, logs and return code. It does not own resource state.

---

## 13. Plugin Resource

Plugin represents an extension installed into CPP.

```yaml
Plugin:
  id: string
  name: string
  category: storage | network | identity | vm | backup | observability
  version: string
  provider: string
  status: installed | enabled | disabled | failed
  capabilities: list[string]
```

Plugins must not directly mutate database tables or bypass Resource/Workflow APIs.

---

## 14. User Resource

User represents an authenticated subject.

```yaml
User:
  id: string
  username: string
  display_name: string
  email: string
  source: local | oidc | ldap | external
  status: active | disabled | locked
```

Detailed RBAC is deferred to Identity/RBAC design.

---

## 15. Aggregate Boundaries

Frozen aggregate roots:

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

Task may be a child of Workflow or standalone for direct single-playbook actions.

---

## 16. Lifecycle Rules

General resource lifecycle:

```text
created -> ready/running -> degraded/failed -> deleting -> deleted
```

Workflow and Task lifecycle:

```text
pending -> queued -> running -> succeeded | failed | cancelled
```

Destructive operations must be represented by Workflow and must require explicit confirmation.

---

## 17. Frozen Decisions

The following review decisions are frozen:

```text
Universal Resource Contract is accepted.
StorageClass is a standalone resource.
Task can exist outside Workflow for legacy actions.
Backup is a unified model for etcd, VM, PVC, namespace and cluster backups.
Network Domain is accepted as an extension domain, not V2.0 core.
```

---

## 18. Deferred To Later Specs

The following are intentionally deferred:

```text
Database tables and indexes -> P2
REST API paths -> P3
Workflow retry and rollback details -> P4
Plugin SDK interface -> P5
Web Console resource views -> P6
RBAC model -> Identity/RBAC spec
```
