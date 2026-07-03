# FROZEN-P0-02 System Architecture v1.0

> Status: Frozen
> Version: v1.0
> Scope: System architecture baseline for CPP
> Rule: Any breaking change requires a new versioned design review.

## 1. Architecture Vision

CPP is an enterprise Cloud Control Plane built around four permanent architecture pillars:

```text
Resource
Workflow
API
Plugin
```

The platform is not an Ansible wrapper. It is a resource-model-driven control plane where API requests create or modify resources, complex operations are expressed as workflows, workflows are executed by runtime workers, and integrations are extended through plugins.

---

## 2. Frozen Architecture Planes

CPP is divided into six permanent planes.

### 2.1 API Plane

Responsibilities:

```text
Authentication
Authorization
REST API
OpenAPI
WebSocket
Rate limit
Request validation
```

Restrictions:

```text
API Plane must not directly operate Kubernetes, KubeVirt, storage, or hosts.
```

---

### 2.2 Resource Plane

Responsibilities:

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

The Resource Plane owns resource state. It does not own execution flow.

---

### 2.3 Workflow Plane

Responsibilities:

```text
Workflow creation
Step orchestration
Retry
Timeout
Approval
Rollback
Resume
Cancel
```

Restrictions:

```text
Workflow Plane must not directly call kubectl, virtctl, shell, or Ansible.
```

---

### 2.4 Runtime Plane

Responsibilities:

```text
Worker
Scheduler
Queue
Executor dispatch
Task lifecycle
```

The Runtime Plane bridges workflows and actual executors.

---

### 2.5 Plugin Plane

Responsibilities:

```text
Storage plugins
Network plugins
Identity plugins
VM plugins
Backup plugins
Monitoring plugins
```

Restrictions:

```text
Plugins must not directly modify core database state.
Plugins interact with the platform through public service/API contracts.
```

---

### 2.6 Observability Plane

Responsibilities:

```text
Metrics
Logs
Events
Audit
Tracing
Workflow visibility
Task visibility
```

Restrictions:

```text
Observability Plane observes and records. It does not control workload state.
```

---

## 3. Frozen Plane Dependency Rules

Allowed dependencies:

```text
API Plane -> Resource Plane
API Plane -> Workflow Plane
Workflow Plane -> Runtime Plane
Runtime Plane -> Executor
Executor -> Kubernetes / KubeVirt / CSI / Hosts
Plugin Plane -> Public API / Service Contracts
Observability Plane -> Events / Logs / Metrics / Audit
```

Forbidden dependencies:

```text
API Plane -> Kubernetes directly
Workflow Plane -> kubectl directly
Workflow Plane -> Ansible directly
Plugin Plane -> Database directly
Observability Plane -> Resource mutation directly
Executor -> Resource model mutation except through approved result reporting
```

---

## 4. Executor Abstraction

Ansible is not the platform core. It is one executor implementation.

Frozen executor model:

```text
Executor
├── AnsibleExecutor
├── KubectlExecutor
├── VirtctlExecutor
├── HelmExecutor
├── TerraformExecutor
└── ShellExecutor
```

Upper layers must depend on the Executor contract, not on a specific executable.

---

## 5. Everything Is A Resource

CPP freezes the following architecture principle:

> Everything Is A Resource.

The platform recognizes these first-class resources:

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

New platform objects must be evaluated against existing resources before introducing new resource types.

---

## 6. Deployment Architecture

CPP supports four deployment modes.

### 6.1 Standalone

For development, testing, and PoC.

### 6.2 HA

For enterprise deployment of the control plane itself.

### 6.3 Management Cluster

Recommended production model. CPP runs in a management environment and controls one or more workload clusters.

### 6.4 Edge

Future mode for constrained or remote environments.

---

## 7. Technology Boundary

CPP is a control plane. It does not become:

```text
A Kubernetes distribution
A hypervisor
A storage system
A CI/CD platform
An application platform
```

CPP orchestrates and governs these systems through APIs, workflows, runtime workers, and plugins.

---

## 8. Frozen Items

The following are frozen in P0-02 v1.0:

```text
Six-plane architecture
Plane dependency rules
Executor abstraction
Four deployment modes
Everything Is A Resource principle
Control-plane-only product boundary
```

---

## 9. Deferred Items

The following are intentionally deferred:

```text
Database implementation details
Worker concurrency model
Plugin SDK interface details
Web Console technology stack
RBAC policy model
Multi-cluster scheduling model
```

These belong to later P-series design documents.
