# FROZEN-P6 Web Console Design v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P3-API-SPECIFICATION-v1.0
> - FROZEN-P4-WORKFLOW-ENGINE-v1.0
> Scope: CPP V2.0 Web Console information architecture, resource views, workflow UX and safety model
> Rule: Any incompatible change to resource-first UI structure, destructive confirmation UX or workflow visibility model must create a new design version and pass review again.

---

## 1. Purpose

This specification freezes the CPP V2.0 Web Console design baseline.

The Web Console is a Resource-first control interface, not a collection of scripts or operation buttons.

---

## 2. Core Principle

Web Console must reflect the frozen Resource Model.

Primary navigation:

```text
Clusters
Nodes
Storage
Virtual Machines
Backups
Workflows
Tasks
Plugins
Audit
```

The UI must not expose implementation details such as playbook names as the primary user model.

---

## 3. Resource-First UX

Each core resource must provide:

```text
List view
Detail view
Spec view
Status view
Events view
Related workflows
Audit history
Allowed actions
```

Resource page structure:

```text
Overview
Spec
Status
Events
Workflows
Audit
Actions
```

---

## 4. Cluster Views

Cluster pages must show:

```text
Cluster phase
Kubernetes version
API endpoint
Node summary
Storage summary
VM summary
Backup summary
Recent workflows
Recent events
```

Allowed actions must create Workflows where complex or destructive.

---

## 5. Node Views

Node pages must show:

```text
Phase
Roles
Labels
Taints
Capacity
Disk summary
NIC summary
GPU summary
Placed VMs
Related storage pools
Recent events
```

Node drain, cordon and maintenance operations must be Workflow-based.

---

## 6. Storage Views

Storage area contains:

```text
StoragePools
StorageClasses
Volume snapshot capability
Governance checks
```

StoragePool and StorageClass are separate resource views.

---

## 7. VM Views

VM pages must show:

```text
Phase
Namespace
CPU
Memory
Disks
Networks
Node placement
Backup status
Recent workflows
Events
```

VM actions:

```text
Start
Stop
Restart
Backup
Restore
Migrate
```

Backup and restore must create Workflows. Restore must require destructive confirmation.

---

## 8. Backup Views

Backup pages must support:

```text
List backups
Filter by scope
Filter by target
Show backend and location
Show expiry
Show created workflow
Show restore eligibility
```

Restore actions must be Workflow-based and auditable.

---

## 9. Workflow Views

Workflow is a first-class UI object.

Workflow detail page must show:

```text
Workflow phase
Target resource
Destructive flag
Confirmation record
Task list
Task timeline
Logs
Events
Audit records
Retry / cancel actions where allowed
```

Task logs must be linked, not hidden in backend files only.

---

## 10. Plugin Views

Plugin pages must show:

```text
Category
Version
Provider
Capabilities
Config schema
Status phase
Health check result
Related workflows
Events
```

Plugin enable/disable actions must be auditable.

---

## 11. Audit Views

Audit page must support:

```text
Actor filter
Action filter
Resource filter
Workflow filter
Time range filter
Result filter
```

Audit events are append-only and must not be edited from UI.

---

## 12. Safety UX

Destructive operations must show explicit confirmation.

Rules:

```text
1. UI must display target resource and impact.
2. UI must require confirm phrase when API requires it.
3. UI must create Workflow, not direct backend command.
4. UI must show resulting workflow immediately.
```

Examples:

```text
VM restore
Backup deletion
Node drain
StorageClass disable
Cluster upgrade
```

---

## 13. Real-Time Updates

Web Console should consume events through WebSocket or polling.

V2.0 acceptable:

```text
Polling for resource/workflow status
```

V2.1 target:

```text
WebSocket event stream
```

The UI data model must be event-ready.

---

## 14. Technology Boundary

V2.0 Web Console technology stack is not frozen here.

Acceptable future choices:

```text
React
Vue
Svelte
```

What is frozen is the information architecture and interaction model, not the JavaScript framework.

---

## 15. Deferred

The following are deferred:

```text
Visual workflow designer
Plugin marketplace UI
Multi-tenant billing UI
Advanced RBAC editor
Topology graph editor
Mobile-first UI
```

---

## 16. Frozen Decisions

```text
1. Web Console is Resource-first.
2. Workflow is a first-class UI object.
3. Destructive operations must use Workflow-based confirmation UX.
4. Spec, Status, Events, Workflows and Audit must be visible on resource detail pages.
5. StoragePool and StorageClass have separate resource views.
6. Web framework is not frozen in this spec.
```
