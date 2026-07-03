# FROZEN-P0-02 System Architecture v1.0

> Status: FROZEN
> Version: v1.0
> Scope: CPP / Cloud Control Platform system architecture
> Rule: Any future incompatible change must create a new design version and pass review again.

---

## 1. Architecture Vision

CPP is an enterprise Cloud Control Plane built on four permanent pillars:

```text
Resource
Workflow
API
Plugin
```

The platform is not an API-to-Ansible wrapper. It is a resource-model-driven control plane where workflows orchestrate changes and runtime executors perform operations against Kubernetes ecosystem components.

---

## 2. Frozen Architecture Planes

The system is divided into six permanent architecture planes.

```text
API Plane
Resource Plane
Workflow Plane
Runtime Plane
Plugin Plane
Observability Plane
```

Every module must belong to exactly one primary plane. Cross-plane interaction must follow the dependency rules defined in this document.

---

## 3. API Plane

The API Plane is the only external entrypoint.

Responsibilities:

```text
Authentication
Authorization
REST API
OpenAPI
WebSocket
Rate limiting
Request validation
```

The API Plane must not directly access Kubernetes, KubeVirt, CSI, etcd, storage systems, or shell commands.

Allowed calls:

```text
API Plane -> Resource Plane
API Plane -> Workflow Plane
```

---

## 4. Resource Plane

The Resource Plane owns the platform resource model and resource state.

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

Resource Plane stores and exposes state. It must not own execution procedure logic.

Example:

```text
VM state: Running / Stopped / Paused / Error
```

The Resource Plane does not define how a VM is started. That responsibility belongs to Workflow and Runtime.

---

## 5. Workflow Plane

The Workflow Plane owns orchestration.

Responsibilities:

```text
Workflow creation
Step ordering
Retry policy
Timeout policy
Approval model
Rollback model
Resume model
Failure handling
```

Workflow Plane must not execute kubectl, virtctl, ansible-playbook, shell, or direct infrastructure commands.

Allowed calls:

```text
Workflow Plane -> Runtime Plane
```

---

## 6. Runtime Plane

The Runtime Plane performs execution.

Responsibilities:

```text
Task queue
Worker
Scheduler
Executor dispatch
Task lifecycle
Execution logs
```

Runtime Plane may call executors.

Executor types:

```text
Ansible Executor
kubectl Executor
virtctl Executor
helm Executor
terraform Executor
shell Executor
```

Ansible is one executor type, not the platform core.

---

## 7. Plugin Plane

The Plugin Plane provides extension mechanisms.

Plugin categories:

```text
Storage Plugin
Network Plugin
Identity Plugin
VM Plugin
Backup Plugin
Observability Plugin
```

Plugins must not directly access the database. Plugins must interact through public platform APIs or stable service interfaces.

Forbidden:

```text
Plugin -> Database
Plugin -> Private internal implementation
```

Allowed:

```text
Plugin -> Resource API
Plugin -> Workflow API
```

---

## 8. Observability Plane

The Observability Plane provides metrics, logs, events, tracing, and audit.

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

Observability Plane must not perform business operations or mutate infrastructure state.

---

## 9. Frozen Dependency Rules

Allowed:

```text
API -> Resource
API -> Workflow
Workflow -> Runtime
Runtime -> Executor
Executor -> Kubernetes ecosystem
Plugin -> Public API
Observability -> Read-only event/log/metric streams
```

Forbidden:

```text
API -> Executor
API -> Kubernetes directly
Workflow -> kubectl directly
Workflow -> Ansible directly
Plugin -> Database directly
Resource -> Runtime directly
Observability -> Infrastructure mutation
```

---

## 10. Everything Is A Resource

The following principle is frozen:

> Everything Is A Resource.

Workflow, Backup, Plugin, Task, VM, Node, Cluster and StoragePool are all resources.

Consequences:

```text
Unified API design
Unified database design
Unified RBAC design
Unified audit design
Unified lifecycle design
```

No module may invent new resource concepts that duplicate existing frozen resources without a new design review.

---

## 11. Deployment Modes

Four deployment modes are frozen.

### 11.1 Standalone

Used for development, testing, and single-node validation.

### 11.2 HA

Enterprise deployment mode with highly available API, workflow, runtime, database and external monitoring.

### 11.3 Management Cluster

Recommended production architecture. One management cluster controls one or more workload clusters.

### 11.4 Edge

Future mode for distributed edge environments. Not required in V2.0 implementation.

---

## 12. Technology Boundary

CPP is a Control Plane.

CPP is not:

```text
A Kubernetes distribution
A hypervisor
A storage system
A CI/CD system
An application marketplace
A business application platform
```

CPP orchestrates and governs existing infrastructure capabilities.

---

## 13. Frozen Items

The following items are frozen in this version:

```text
Six-plane architecture
Plane dependency rules
Executor as abstraction
Ansible as executor, not core
Everything Is A Resource
Four deployment modes
Control Plane product boundary
```

---

## 14. Not Frozen In This Document

The following are intentionally not frozen here and must be designed in later specs:

```text
Database schema details
Worker concurrency implementation
Plugin SDK interface details
Web Console technology stack
RBAC policy model
Multi-cluster resource federation
```

---

## 15. Next Design Documents

After this freeze, design must continue in the following order:

```text
P1 Domain Model Design
P2 Database Design
P3 API Specification
P4 Workflow Engine Specification
P5 Plugin SDK Specification
P6 Web Console Design
P7 Engineering and CI/CD Specification
P8 Test and Validation Specification
```
