# IMPL-00 Design-to-Code Gap Analysis v1.0

> Status: Implementation Planning
> Version: v1.0
> Depends on: FROZEN-P0-01 through FROZEN-P8
> Scope: Gap analysis between the frozen CPP V2.0 design baseline and the current repository implementation

---

## 1. Purpose

This document identifies the implementation gaps that must be closed before CPP can claim conformance with the frozen design baseline.

The analysis focuses on:

```text
Architecture boundaries
Resource model
Persistence
API
Workflow
Executor/runtime
Plugin framework
Web Console
Engineering and validation
```

The objective is not to rewrite the repository. The objective is to migrate incrementally while preserving working playbooks and existing API behavior where possible.

---

## 2. Overall Assessment

Current repository maturity:

```text
Automation assets: strong
Playbook coverage: strong
Platform API skeleton: present
Workflow prototype: present
Persistence layer: incomplete
Unified resource model: not implemented
Executor abstraction: duplicated
Plugin framework: design only
Web Console: not implemented
Release validation: partial
```

Overall conclusion:

> The repository has enough automation and API assets to evolve into CPP, but the current implementation is still a playbook-oriented API facade rather than the frozen resource/workflow control plane.

---

## 3. P0 Architecture Boundary Gaps

### GAP-A01: API routers still call executors directly

Frozen design:

```text
API -> Resource Service / Workflow Service
Workflow -> Runtime -> Executor
```

Current implementation contains routers that submit playbooks or call executor services directly.

Impact:

```text
API Plane and Runtime Plane boundaries are mixed.
Complex operations bypass Workflow semantics.
Audit, retry, approval and rollback cannot be enforced consistently.
```

Required change:

```text
Move all infrastructure-changing router operations behind Workflow Service.
Keep read-only query endpoints in Resource Service.
Deprecate direct executor submission from routers.
```

Priority: P0

---

### GAP-A02: Resource Plane is missing as an implementation layer

Frozen design requires Resource Service and repositories for:

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

Current routers mostly return hardcoded, transient or playbook-derived data.

Required change:

```text
Introduce resource schemas, services and repositories.
Expose metadata/spec/status consistently.
Persist resource identity and lifecycle.
```

Priority: P0

---

## 4. Executor and Runtime Gaps

### GAP-R01: Two executor implementations exist

Current implementation has two execution paths:

```text
app.core.executor
app.services.executor
```

Observed differences:

```text
One path uses asynchronous subprocess submission and task_store.
One path runs playbooks synchronously and stores jobs in memory.
Routers use both implementations.
```

Impact:

```text
Inconsistent task lifecycle
Inconsistent logs and status
Duplicate responsibilities
Difficult recovery after restart
```

Required change:

```text
Define one RuntimeService.
Define one Executor interface.
Implement AnsibleExecutor behind that interface.
Migrate both existing paths to the unified runtime.
```

Priority: P0

---

### GAP-R02: Task completion lifecycle is incomplete

The asynchronous executor records task start but does not provide a complete durable terminal-state lifecycle.

Required change:

```text
Persist queued/running/succeeded/failed/cancelled states.
Persist return code, timestamps and log reference.
Add worker completion handling.
Recover running tasks after service restart.
```

Priority: P0

---

### GAP-R03: Runtime state is memory/file based

Current jobs, tasks and workflows depend on in-memory structures and files under `/tmp`.

Impact:

```text
Restart loses runtime indexes.
HA deployment is impossible.
Concurrency control is weak.
```

Required change:

```text
Persist durable Workflow and Task state through repositories.
Keep only recoverable queue/worker context in memory.
Prepare optional Redis runtime adapter after SQLite baseline.
```

Priority: P0

---

## 5. Workflow Gaps

### GAP-W01: Duplicate workflow service implementations

Current repository contains both:

```text
app.services.workflow
app.services.workflow_service
```

Only one is wired to the current router.

Required change:

```text
Select one WorkflowEngine implementation.
Merge persistence, audit and execution behavior.
Delete or deprecate the unused implementation after migration.
```

Priority: P0

---

### GAP-W02: Workflow API does not fully match frozen resource API

Current API uses a generic workflow create request with template names.

Frozen design requires Workflow as a first-class resource with stable metadata/spec/status and consistent create/get/list semantics.

Required change:

```text
Return full Workflow resource shape.
Add resource_version and generation.
Standardize target_kind/target_id.
Standardize destructive confirmation semantics.
Add pagination and filtering.
```

Priority: P1

---

### GAP-W03: Retry, timeout, cancellation and compensation are incomplete

Current workflow runner primarily executes steps sequentially and stops on failure.

Required change:

```text
Define step timeout.
Define retry policy and retry counters.
Define cancellation checkpoints.
Define compensation task metadata.
Persist step attempts.
```

Priority: P1

---

### GAP-W04: Workflow execution is synchronous in request path

Current create path can run workflow steps before returning.

Impact:

```text
Long API requests
Poor scalability
No reliable worker isolation
```

Required change:

```text
POST creates Workflow in pending/queued state.
Runtime worker executes asynchronously.
API immediately returns workflow resource and location.
```

Priority: P0

---

## 6. Persistence and Data Model Gaps

### GAP-D01: No repository layer for core resources

Frozen P2 requires:

```text
Service -> Repository -> Database
```

Current implementation uses files, in-memory dictionaries and direct service state.

Required change:

```text
Create repository interfaces.
Implement SQLite repositories first.
Prohibit SQL/file persistence from routers, workflows, plugins and executors.
```

Priority: P0

---

### GAP-D02: SQLite/Alembic baseline is not implemented

Frozen design requires versioned schema migration and future PostgreSQL compatibility.

Required change:

```text
Add SQLAlchemy or equivalent persistence layer.
Add Alembic configuration.
Create initial schema for workflows, tasks, audit_events and resource_events.
Add later resource tables incrementally.
```

Priority: P0

---

### GAP-D03: metadata/spec/status contract is not implemented consistently

Current request and response models are operation-specific.

Required change:

```text
Create common ResourceMetadata schema.
Create common ResourceEnvelope schema.
Model spec and status separately.
Increment generation only on spec changes.
Update resource_version on every persisted mutation.
```

Priority: P0

---

### GAP-D04: UUIDv7, soft deletion and optimistic concurrency are absent

Required change:

```text
Adopt UUIDv7-compatible ID generator.
Add deleted_at to resource tables.
Add generation and resource_version.
Require If-Match/resource_version for conflicting updates where applicable.
```

Priority: P1

---

### GAP-D05: Audit is file-based rather than append-only repository based

Current audit writes JSON lines to a local file.

Required change:

```text
Create audit_events table and append-only repository.
Keep optional JSONL export adapter.
Record actor, action, target, workflow/task, request ID and result.
```

Priority: P1

---

## 7. API Gaps

### GAP-P01: Resource endpoints are incomplete

Frozen resource APIs are required for all core resources.

Current API has partial operational routers but lacks consistent CRUD/read models.

Required change:

```text
Implement common list/get/create/update/delete conventions.
Add pagination, label filtering and phase filtering.
Return metadata/spec/status envelopes.
```

Priority: P1

---

### GAP-P02: Mixed operation naming and behavior

Some endpoints are resource-oriented while others are playbook/action-oriented.

Required change:

```text
Use resource paths for resource state.
Use Workflow submission for complex actions.
Keep compatibility aliases temporarily with deprecation headers.
```

Priority: P1

---

### GAP-P03: Destructive confirmation is inconsistent

Current destructive confirmation uses different booleans and phrases across operations.

Required change:

```text
Define one confirmation object.
Require explicit confirm=true.
Require operation-specific confirmation phrase for high-risk workflows.
Persist confirmation in Workflow spec and AuditEvent.
```

Priority: P0

---

### GAP-P04: Authentication and authorization are missing

Frozen product scope includes a User resource and later enterprise identity integration.

Required change:

```text
Implement minimal local identity and request actor context.
Add authorization service boundary.
Add OIDC/LDAP only after local RBAC baseline.
```

Priority: P1

---

## 8. Resource-Specific Gaps

### Cluster and Node

Current playbooks can inspect and manage clusters/nodes, but durable Cluster and Node resources are missing.

Required:

```text
Cluster inventory import/reconcile
Node discovery and status reconciliation
Stable resource identity independent of inventory file path
```

Priority: P1

---

### StoragePool and StorageClass

Current governance and snapshot checks exist, but resources are not persisted or reconciled.

Required:

```text
StoragePool catalog
StorageClass discovery
Plugin reference
Capacity/status reconciliation
```

Priority: P1

---

### VM

Current KubeVirt operations are workflow/playbook oriented, but no unified VM resource repository exists.

Required:

```text
VM discovery and identity
VM spec/status mapping
Workflow actions for start/stop/migrate/backup/restore
```

Priority: P1

---

### Backup

Backup playbooks and preflight checks exist, but Backup artifacts are not cataloged as durable resources.

Required:

```text
Backup catalog
Polymorphic target_kind/target_id
Artifact location and retention
Restore relationship
```

Priority: P1

---

## 9. Plugin Framework Gaps

### GAP-PL01: Plugin SDK exists only as frozen design

Required change:

```text
Create Plugin manifest schema.
Create capability registry.
Create plugin lifecycle service.
Create version compatibility validation.
Prevent direct database and executor access.
```

Priority: P2

---

### GAP-PL02: Existing storage integrations are not pluginized

Current storage-specific logic remains in roles/playbooks.

Required change:

```text
Wrap existing NFS, iSCSI and Ceph capabilities behind plugin manifests and workflow templates.
Do not rewrite working playbooks initially.
```

Priority: P2

---

## 10. Web Console Gaps

### GAP-UI01: Web Console implementation is absent

Required minimum V2.0 console:

```text
Resource navigation
Cluster/Node/Storage/VM/Backup views
Workflow and Task progress
Audit view
Destructive confirmation UX
```

Priority: P2

The console should start only after stable P3 resource APIs and P4 asynchronous workflow APIs exist.

---

## 11. Engineering and Validation Gaps

### GAP-E01: Platform API test coverage is insufficient

Required:

```text
Unit tests for schemas/services/repositories
API contract tests
Workflow state-machine tests
Executor adapter tests
SQLite migration tests
```

Priority: P0

---

### GAP-E02: No design-conformance CI gate

Required:

```text
Lint and type-check platform-api
Run migration upgrade/downgrade tests
Validate OpenAPI compatibility
Run workflow safety tests
Check frozen-document references
```

Priority: P1

---

### GAP-E03: Packaging and deployment are incomplete

Required:

```text
Container image for API/worker
Standalone SQLite deployment
HA PostgreSQL deployment profile
Configuration and secret separation
Health/readiness endpoints
```

Priority: P1

---

## 12. Migration Principles

Implementation must follow these principles:

```text
1. Preserve working playbooks.
2. Add abstraction before replacing implementation.
3. Migrate one router/domain at a time.
4. Keep temporary compatibility endpoints.
5. Do not introduce Web Console before API stability.
6. Do not implement Plugin SDK before Runtime/Workflow boundaries are stable.
7. Every implementation milestone must pass P8 acceptance gates.
```

---

## 13. Recommended Implementation Epics

### EPIC-01 Foundation Persistence

```text
Repository interfaces
SQLite database
Alembic migrations
UUIDv7 IDs
Resource metadata/spec/status base models
Audit and ResourceEvent repositories
```

### EPIC-02 Unified Runtime and Executor

```text
RuntimeService
Task state machine
AnsibleExecutor adapter
Durable logs and completion status
Removal of duplicate executor paths
```

### EPIC-03 Workflow Engine V2

```text
Asynchronous workflow submission
Durable workflow/task state
Retry, timeout and cancellation
Destructive confirmation
Audit integration
```

### EPIC-04 Resource Services and APIs

```text
Cluster and Node
StoragePool and StorageClass
VM
Backup
Plugin and User baseline
```

### EPIC-05 Compatibility Migration

```text
Move existing routers behind Workflow Service
Add deprecation aliases
Map existing playbooks to workflow templates
Remove direct router-to-executor calls
```

### EPIC-06 Security and Governance

```text
Request actor context
Local authentication
RBAC service
Approval hooks
Audit query APIs
```

### EPIC-07 Plugin Framework

```text
Plugin manifest
Capability registry
Storage plugin wrappers
Compatibility validation
```

### EPIC-08 Web Console

```text
Resource-first UI
Workflow and Task visibility
Audit view
Safe destructive operation UX
```

### EPIC-09 Delivery and Acceptance

```text
CI gates
Container packaging
Standalone and HA deployment
End-to-end acceptance tests
Release checklist
```

---

## 14. Recommended Execution Order

```text
EPIC-01 Foundation Persistence
        ↓
EPIC-02 Unified Runtime and Executor
        ↓
EPIC-03 Workflow Engine V2
        ↓
EPIC-04 Resource Services and APIs
        ↓
EPIC-05 Compatibility Migration
        ↓
EPIC-06 Security and Governance
        ↓
EPIC-07 Plugin Framework
        ↓
EPIC-08 Web Console
        ↓
EPIC-09 Delivery and Acceptance
```

---

## 15. First Implementation Milestone

The first milestone should be:

```text
M1 Control Plane Foundation
```

Scope:

```text
SQLite + Alembic
Repository interfaces
Workflow/Task/Audit persistence
Unified RuntimeService
AnsibleExecutor adapter
Asynchronous Workflow API
Migration of one low-risk workflow: governance.full_check
```

Acceptance criteria:

```text
1. API restart does not lose Workflow or Task state.
2. One workflow is executed asynchronously.
3. Task reaches durable terminal state.
4. Audit event is persisted.
5. No router in the migrated path calls executor directly.
6. Existing playbook remains unchanged.
7. Unit, migration and API tests pass.
```

---

## 16. Implementation Gate

No feature implementation should begin without:

```text
Mapped frozen requirement
Defined Epic and task
Migration/compatibility impact
Test and acceptance criteria
Rollback plan
```

The immediate next artifact is:

```text
IMPL-01-M1-CONTROL-PLANE-FOUNDATION-PLAN-v1.0.md
```
