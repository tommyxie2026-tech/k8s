# P1-01 Domain Model Design

> Status: Design Review
> Version: v0.9
> Depends on: FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> Principle: Everything Is A Resource

---

## 1. Goal

This document defines the first-class domain resources for CPP.

The goal is to convert the frozen P0-02 architecture principle:

```text
Everything Is A Resource
```

into a concrete domain model that can later drive:

```text
Database schema
REST API design
RBAC policy
Audit model
Workflow input/output
Plugin contract
Web Console information architecture
```

---

## 2. Domain Design Rules

### 2.1 Resource First

Every manageable object must be represented as a Resource.

Frozen core resources:

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

No module may introduce duplicate resource concepts without design review.

---

### 2.2 Resource Shape

All resources share the following base shape:

```yaml
apiVersion: cpp.io/v1
kind: <ResourceKind>
metadata:
  id: string
  name: string
  namespace: string optional
  labels: map
  annotations: map
  createdAt: datetime
  updatedAt: datetime
spec: object
status: object
```

Rules:

```text
metadata describes identity and classification
spec describes desired state
status describes observed state
```

---

### 2.3 Spec / Status Separation

The platform must preserve Kubernetes-style separation:

```text
spec = desired state
status = observed state
```

Examples:

```text
VM.spec.powerState = running
VM.status.phase = Running
```

Controllers, workflows, or executors reconcile actual state toward desired state.

---

### 2.4 Resource Ownership

Resources may own other resources.

Examples:

```text
Cluster owns Node
Cluster owns StoragePool
VM owns Backup references
Workflow owns Task references
```

Ownership must be explicit and auditable.

---

## 3. Domain Boundaries

CPP contains the following domains.

```text
Cluster Domain
Node Domain
Storage Domain
Virtualization Domain
Backup Domain
Workflow Domain
Plugin Domain
Identity Domain
Observability Domain
```

Each domain maps to one or more frozen resources.

---

## 4. Cluster Resource

### 4.1 Purpose

Cluster represents a Kubernetes cluster managed by CPP.

### 4.2 Spec

```yaml
kind: Cluster
spec:
  mode: standalone | ha | management | edge
  kubernetesVersion: string
  apiEndpoint: string
  inventoryRef: string
  ha:
    enabled: bool
    vip: string
  features:
    kubevirt: bool
    csi: bool
    observability: bool
    backup: bool
```

### 4.3 Status

```yaml
status:
  phase: Unknown | Provisioning | Running | Degraded | Failed | Deleting
  nodeCount: int
  controlPlaneReady: bool
  apiReachable: bool
  lastHealthCheckAt: datetime
```

---

## 5. Node Resource

### 5.1 Purpose

Node represents a physical or virtual machine participating in a managed cluster.

### 5.2 Spec

```yaml
kind: Node
spec:
  clusterRef: string
  hostname: string
  address: string
  roles:
    - control-plane
    - compute
    - storage
    - vm
    - edge
  labels: map
  taints: list
  hardware:
    cpu: string
    memory: string
    disks: list
    nics: list
    gpu: list
```

### 5.3 Status

```yaml
status:
  phase: Unknown | Ready | NotReady | Draining | Maintenance | Failed
  kubeletReady: bool
  runtimeReady: bool
  storageReady: bool
  lastSeenAt: datetime
```

---

## 6. StoragePool Resource

### 6.1 Purpose

StoragePool represents a logical storage backend or pool.

Examples:

```text
local-lvm
nfs-csi
iscsi-san
ceph-rbd
cephfs
```

### 6.2 Spec

```yaml
kind: StoragePool
spec:
  clusterRef: string
  type: local-lvm | nfs | iscsi | ceph-rbd | cephfs
  failureDomain: host | rack | zone | region
  capacityPolicy:
    warningThresholdPercent: int
    criticalThresholdPercent: int
  snapshotSupported: bool
  expansionSupported: bool
```

### 6.3 Status

```yaml
status:
  phase: Unknown | Available | Degraded | Full | Failed
  totalCapacity: string
  usedCapacity: string
  availableCapacity: string
  health: string
```

---

## 7. StorageClass Resource

### 7.1 Purpose

StorageClass represents a Kubernetes StorageClass governed by CPP.

### 7.2 Spec

```yaml
kind: StorageClass
spec:
  clusterRef: string
  storagePoolRef: string
  provisioner: string
  reclaimPolicy: Delete | Retain
  volumeBindingMode: Immediate | WaitForFirstConsumer
  allowVolumeExpansion: bool
  defaultClass: bool
```

### 7.3 Status

```yaml
status:
  phase: Unknown | Active | Misconfigured | Deprecated
  pvcCount: int
  pvCount: int
```

---

## 8. VM Resource

### 8.1 Purpose

VM represents a KubeVirt virtual machine managed by CPP.

### 8.2 Spec

```yaml
kind: VM
spec:
  clusterRef: string
  namespace: string
  cpu: string
  memory: string
  powerState: running | stopped
  disks:
    - name: string
      storageClass: string
      size: string
      boot: bool
  networks:
    - name: string
      type: pod | bridge | sriov
  backupPolicyRef: string optional
```

### 8.3 Status

```yaml
status:
  phase: Unknown | Running | Stopped | Starting | Stopping | Migrating | Error
  nodeName: string
  ipAddresses: list
  ready: bool
  lastBackupAt: datetime optional
```

---

## 9. Backup Resource

### 9.1 Purpose

Backup represents a backup operation or backup artifact.

### 9.2 Spec

```yaml
kind: Backup
spec:
  clusterRef: string
  targetKind: Cluster | Namespace | VM | PVC | etcd
  targetRef: string
  backend: local | nfs | s3
  retentionDays: int
  snapshot: bool
```

### 9.3 Status

```yaml
status:
  phase: Pending | Running | Succeeded | Failed | Expired
  artifactRef: string
  size: string
  startedAt: datetime
  completedAt: datetime
```

---

## 10. Workflow Resource

### 10.1 Purpose

Workflow represents an orchestrated operation composed of ordered tasks.

### 10.2 Spec

```yaml
kind: Workflow
spec:
  name: string
  destructive: bool
  confirmRequired: bool
  steps:
    - name: string
      taskRef: string
```

### 10.3 Status

```yaml
status:
  phase: Pending | Running | Succeeded | Failed | Cancelled
  currentStep: string
  startedAt: datetime
  completedAt: datetime
```

---

## 11. Task Resource

### 11.1 Purpose

Task represents one executable unit.

### 11.2 Spec

```yaml
kind: Task
spec:
  workflowRef: string optional
  executor: ansible | kubectl | virtctl | helm | terraform | shell
  command: list
  timeoutSeconds: int
  retryPolicy:
    maxRetries: int
```

### 11.3 Status

```yaml
status:
  phase: Pending | Running | Succeeded | Failed | Cancelled
  returnCode: int
  logRef: string
  startedAt: datetime
  completedAt: datetime
```

---

## 12. Plugin Resource

### 12.1 Purpose

Plugin represents a platform extension.

### 12.2 Spec

```yaml
kind: Plugin
spec:
  category: storage | network | identity | vm | backup | observability
  version: string
  enabled: bool
  capabilities: list
```

### 12.3 Status

```yaml
status:
  phase: Unknown | Installed | Enabled | Disabled | Failed
  health: string
```

---

## 13. User Resource

### 13.1 Purpose

User represents an authenticated platform user or service account.

### 13.2 Spec

```yaml
kind: User
spec:
  type: human | serviceAccount
  displayName: string
  email: string optional
  provider: local | oidc | ldap
  roles: list
```

### 13.3 Status

```yaml
status:
  phase: Active | Disabled | Locked
  lastLoginAt: datetime
```

---

## 14. Domain Relationships

```text
Cluster 1 -> N Node
Cluster 1 -> N StoragePool
StoragePool 1 -> N StorageClass
Cluster 1 -> N VM
VM 1 -> N Backup
Workflow 1 -> N Task
Plugin N -> N Resource capability
User N -> N Role binding
```

---

## 15. Not In This Document

The following are not frozen in this P1 draft:

```text
Database tables
REST endpoint paths
RBAC policy grammar
Plugin SDK method signatures
Workflow state machine details
UI layout
```

These are handled in later documents.

---

## 16. Review Items

Before freezing P1-01, confirm:

```text
1. Are the ten core resources sufficient for V2.0?
2. Should Namespace be a first-class CPP resource or remain a Kubernetes-scoped attribute?
3. Should BackupPolicy be first-class in V2.0 or deferred to V2.1?
4. Should Role/RoleBinding be first-class now or deferred to Identity design?
```
