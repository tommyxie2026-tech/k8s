# FROZEN-P0-01 Product Positioning v1.0

> Status: FROZEN
> Version: v1.0
> Scope: CPP product positioning, target customers, commercial model, product boundary and long-term direction
> Rule: Any incompatible change to product positioning, target market, commercial model or product boundary must create a new design version and pass review again.

---

## 1. Product Codename

The internal product codename is:

```text
CPP
```

CPP is used as the engineering codename. A final external brand name may be selected later without changing the frozen architecture or product scope.

---

## 2. Product Mission

CPP is an open cloud control platform for enterprises, managed service providers and industry solution partners.

It provides one control plane for:

```text
Kubernetes
KubeVirt virtual machines
Storage and CSI
Backup and disaster recovery
Operational workflows
Plugins and extensions
Observability and audit
```

CPP is not a Kubernetes distribution. It is an enterprise control plane built on top of Kubernetes ecosystem capabilities.

---

## 3. Product Positioning

CPP V2.0 primarily targets enterprise private cloud control-plane scenarios.

Long-term evolution expands to:

```text
Hybrid cloud
Multi-cluster management
Edge cloud
Industry-specific cloud platforms
```

The V2.0 implementation must prioritize a stable enterprise private cloud foundation and must not over-expand into all hybrid and edge scenarios at once.

---

## 4. Target Customers

CPP freezes the following customer hierarchy:

```text
1. Enterprise private cloud teams
2. Managed Service Providers (MSP)
3. Industry solution partners, OEMs and system integrators
```

Primary V2.0 users include:

```text
Platform engineers
Kubernetes administrators
Virtualization administrators
Storage administrators
Operations engineers
Platform development teams
```

---

## 5. Commercial Model

CPP adopts an Open Core model.

### 5.1 Community Edition

Community capabilities include the complete foundational control plane:

```text
Kubernetes lifecycle and governance
KubeVirt integration
CSI and storage management
Workflow Engine
Backup framework
Platform API
Basic Plugin SDK
Basic observability and audit
```

### 5.2 Enterprise Edition

Enterprise enhancements may include:

```text
OIDC and LDAP integration
Advanced RBAC and multi-tenancy
Approval workflows
Highly available API and database deployment
Enterprise audit and compliance
Advanced multi-cluster governance
Commercial plugins
Enterprise support and lifecycle services
```

The Community Edition must remain operationally useful and must not be reduced to a non-functional demo.

---

## 6. Core Product Value

CPP delivers four core values:

```text
Unified control
Workflow-based automation
Plugin-based extensibility
Enterprise governance
```

### Unified Control

One resource model and API manage clusters, nodes, storage, VMs, backups, workflows, tasks and plugins.

### Workflow-Based Automation

Complex operations are represented as observable, auditable and resumable workflows rather than opaque scripts.

### Plugin-Based Extensibility

Storage, network, identity, backup, VM and observability capabilities can be extended without modifying core platform internals.

### Enterprise Governance

Destructive confirmation, audit history, resource lifecycle, validation and release gates are built into the product design.

---

## 7. Product Scope For V2.0

V2.0 includes:

```text
Kubernetes cluster lifecycle and validation
HA deployment support
Node and NodePool governance
StoragePool and StorageClass governance
CSI capability lifecycle
KubeVirt and VM lifecycle operations
Workflow Engine and Runtime
Backup and restore framework
Platform API
Basic Plugin SDK
Basic Web Console
Observability and audit
Engineering, packaging and validation baseline
```

---

## 8. Out Of Scope For V2.0

V2.0 does not attempt to become:

```text
A Kubernetes distribution
A hypervisor
A storage system
A CI/CD platform
An application marketplace
A tenant billing platform
A complete enterprise IAM suite
A replacement for all public cloud control planes
```

These boundaries protect focus and engineering quality.

---

## 9. Product Principles

CPP freezes the following product principles:

```text
API First
Workflow Native
Plugin First
Resource Model Driven
Cloud Agnostic
Open Core
Observability by Default
Security by Default
Safe by Default
Backward Compatible
Design Before Code
```

---

## 10. Relationship To Existing Playbooks

Existing Ansible playbooks are valuable execution assets, but they are not the platform architecture.

Frozen relationship:

```text
API
  -> Workflow
    -> Runtime
      -> Executor
        -> Ansible Playbook
```

Ansible is one executor type. Future executors may include:

```text
kubectl
virtctl
helm
terraform
shell
native controllers
```

---

## 11. Competitive Position

CPP is positioned between infrastructure automation collections and large full-stack private-cloud products.

Its differentiation is:

```text
Resource-first control plane
Workflow-native operations
KubeVirt and storage focus
Open plugin boundary
Incremental migration from existing automation assets
```

CPP does not attempt to duplicate every capability of Rancher, OpenShift, OpenStack or Harvester. It focuses on an extensible enterprise control layer.

---

## 12. Success Criteria

CPP V2.0 is successful when it can demonstrate:

```text
1. Unified management of Kubernetes and KubeVirt resources.
2. One stable resource API for core platform resources.
3. Workflow coverage for major operational scenarios.
4. Verified backup and restore procedures.
5. At least three storage backend integration paths.
6. Full task, workflow and audit visibility.
7. Safe defaults for destructive operations.
8. A documented extension model for plugins.
9. Repeatable packaging, release and acceptance validation.
```

---

## 13. Frozen Decisions

The following decisions are frozen:

```text
1. CPP is the internal engineering codename.
2. V2.0 primarily targets enterprise private cloud.
3. Hybrid cloud and edge are long-term evolution directions.
4. CPP uses an Open Core commercial model.
5. Target customers include enterprises, MSPs and industry partners.
6. CPP is a control plane, not a Kubernetes distribution, hypervisor or storage system.
7. Existing playbooks are execution assets behind Workflow and Executor boundaries.
```

---

## 14. Downstream Specifications

This product positioning is implemented by:

```text
FROZEN-P0-02 System Architecture
FROZEN-P1-01 Domain Model
FROZEN-P2-01 Data Architecture
FROZEN-P2-02 ER Model
FROZEN-P2-03 Table Schema
FROZEN-P3 API Specification
FROZEN-P4 Workflow Engine
FROZEN-P5 Plugin SDK
FROZEN-P6 Web Console
FROZEN-P7 Engineering
FROZEN-P8 Validation
```
