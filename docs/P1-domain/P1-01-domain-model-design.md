# P1-01 Domain Model Design

> Status: Design Review
> Version: v0.9
> Depends on: FROZEN-P0-02-system-architecture-v1.0

## 1. Goal

This document defines the first version of the CPP domain model.

It follows the frozen principle:

```text
Everything Is A Resource
```

The goal of P1 is to define stable domain boundaries and resource ownership before database schema, API schema, or implementation details are designed.

---

## 2. Domain Boundary Overview

CPP V2.0 is divided into the following domains:

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

Each domain owns its own concepts and must expose state through the Resource Plane.

---

## 3. Core Resource Types

The frozen first-class resource set is:

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

Additional resource types require design review.

---

## 4. Cluster Domain

### 4.1 Responsibility

The Cluster Domain represents a Kubernetes cluster controlled by CPP.

It owns:

```text
Cluster identity
Cluster endpoint
Cluster mode
Cluster version
Cluster health
Cluster inventory reference
```

### 4.2 Resource: Cluster

Fields:

```yaml
id: string
name: string
mode: standalone | ha | management | edge
kubernetes_version: string
api_endpoint: string
vip: string
status: pending | ready | degraded | failed | unknown
created_at: datetime
updated_at: datetime
```

### 4.3 Non-responsibility

Cluster Domain does not own VM lifecycle, storage provisioning, or backup execution.

---

## 5. Node Domain

### 5.1 Responsibility

The Node Domain represents physical or virtual machines participating in a cluster.

It owns:

```text
Node identity
Roles
Labels
Taints
Capacity
Health
```

### 5.2 Resource: Node

Fields:

```yaml
id: string
cluster_id: string
hostname: string
ip: string
roles: list[string]
labels: map[string]string
taints: list[string]
cpu_capacity: string
memory_capacity: string
status: ready | not_ready | degraded | unknown
```

### 5.3 NodePool as View

NodePool is not frozen as a first-class resource in P0-02. It is initially treated as a view over Node labels and roles.

Future design may promote NodePool to a first-class resource if required.

---

## 6. Storage Domain

### 6.1 Responsibility

The Storage Domain owns storage abstractions exposed to workloads and VMs.

It owns:

```text
StoragePool
StorageClass
Snapshot capability
Capacity
Health
Storage backend metadata
```

### 6.2 Resource: StoragePool

Fields:

```yaml
id: string
cluster_id: string
name: string
backend: local-lvm | nfs | iscsi | ceph-rbd | cephfs
failure_domain: string
capacity_total: string
capacity_used: string
status: ready | degraded | failed | unknown
```

### 6.3 Resource: StorageClass

Fields:

```yaml
id: string
cluster_id: string
name: string
provisioner: string
storage_pool_id: string
reclaim_policy: delete | retain
volume_binding_mode: immediate | wait_for_first_consumer
allow_expansion: bool
snapshot_supported: bool
status: active | deprecated | disabled
```

---

## 7. Virtualization Domain

### 7.1 Responsibility

The Virtualization Domain owns VM-level resource state.

It owns:

```text
VM identity
CPU / Memory
Disks
Networks
Runtime status
Backup relation
```

### 7.2 Resource: VM

Fields:

```yaml
id: string
cluster_id: string
namespace: string
name: string
cpu: string
memory: string
disks: list[object]
networks: list[object]
status: running | stopped | paused | error | unknown
created_at: datetime
updated_at: datetime
```

### 7.3 Non-responsibility

The VM resource records desired and observed state. It does not execute start/stop/backup directly. Those actions are represented as Workflow resources.

---

## 8. Backup Domain

### 8.1 Responsibility

The Backup Domain owns backup metadata and restore intent.

It owns:

```text
Backup record
Backup scope
Backup target
Restore plan
Retention
Validation status
```

### 8.2 Resource: Backup

Fields:

```yaml
id: string
cluster_id: string
name: string
scope: cluster | namespace | vm | pvc | etcd
source_ref: string
target: local | nfs | s3
status: pending | running | succeeded | failed | expired
created_at: datetime
expires_at: datetime
```

---

## 9. Workflow Domain

### 9.1 Responsibility

The Workflow Domain owns multi-step orchestration state.

It owns:

```text
Workflow definition
Workflow instance
Step sequence
Step status
Confirmation requirements
```

### 9.2 Resource: Workflow

Fields:

```yaml
id: string
name: string
status: pending | running | succeeded | failed | cancelled
destructive: bool
steps: list[WorkflowStep]
created_at: datetime
finished_at: datetime
```

---

## 10. Task Runtime Domain

### 10.1 Responsibility

The Task Runtime Domain owns executable task state.

It owns:

```text
Task command
Executor type
Process status
Logs
Exit code
```

### 10.2 Resource: Task

Fields:

```yaml
id: string
workflow_id: string
step_name: string
executor: ansible | kubectl | virtctl | helm | terraform | shell
command: list[string]
status: pending | running | succeeded | failed | cancelled
return_code: int
log_path: string
```

---

## 11. Plugin Domain

### 11.1 Responsibility

The Plugin Domain owns extension registration and lifecycle.

It owns:

```text
Plugin identity
Plugin type
Plugin version
Capability declaration
Health
```

### 11.2 Resource: Plugin

Fields:

```yaml
id: string
name: string
type: storage | network | identity | vm | backup | monitoring
version: string
status: enabled | disabled | failed
capabilities: list[string]
```

---

## 12. Identity Domain

### 12.1 Responsibility

The Identity Domain owns users, authentication identity, and future RBAC linkage.

### 12.2 Resource: User

Fields:

```yaml
id: string
username: string
display_name: string
email: string
status: active | disabled
roles: list[string]
```

---

## 13. Observability Domain

The Observability Domain does not create a first-class resource in P1-01 except through Audit/Event records in later database design.

It observes:

```text
Cluster
Node
VM
StoragePool
Workflow
Task
Backup
```

---

## 14. Domain Rules

Frozen candidates for review:

```text
1. Resource state and execution state are separate.
2. VM action is represented as Workflow, not direct VM mutation.
3. NodePool remains a view until explicitly promoted.
4. Backup metadata is separate from Workflow execution.
5. Plugin declares capability; it does not own core resource state.
6. Task is the only domain that owns command execution details.
```

---

## 15. Review Items

Before freezing P1-01, confirm:

```text
1. Whether NodePool should remain a view or become first-class resource.
2. Whether Backup should be one resource or split into Backup and Restore.
3. Whether StorageClass should be first-class or a child of StoragePool.
4. Whether Task should be user-visible API resource or internal-only resource.
```
