# CPP V2.0 Implementation Plan v1.0

> Status: APPROVED BASELINE
> Depends on: FROZEN-P0-01 through FROZEN-P8
> Input: DESIGN-TO-CODE-GAP-ANALYSIS-v1.0
> Goal: Convert frozen design into an executable delivery programme with milestones, epics, tasks and acceptance gates.

---

## 1. Delivery Strategy

Implementation proceeds in dependency order.

```text
M0 Engineering Baseline
M1 Persistence Foundation
M2 Runtime Convergence
M3 Workflow Engine
M4 Resource Plane and API
M5 Security, Audit and Events
M6 Plugin SDK
M7 Web Console
M8 Release Validation
```

No milestone may bypass the frozen P8 validation gates.

---

## 2. Milestone M0: Engineering Baseline

### Goal

Create a safe implementation foundation before core refactoring.

### Epic E0.1: Project Quality Gates

Tasks:

```text
T0.1 Add pytest baseline and test directory structure
T0.2 Add ruff or equivalent Python lint configuration
T0.3 Add mypy or pyright baseline for platform-api
T0.4 Add CI workflow for lint, unit tests and import validation
T0.5 Add application startup smoke test
T0.6 Add architecture dependency tests preventing router -> executor imports
```

Acceptance:

```text
CI runs on every pull request.
Platform API imports successfully.
New router-to-executor dependencies fail CI.
```

### Epic E0.2: Compatibility Inventory

Tasks:

```text
T0.7 Inventory all current API routes
T0.8 Inventory all executor call sites
T0.9 Inventory TaskInfo and JobRecord consumers
T0.10 Define compatibility and deprecation map
```

---

## 3. Milestone M1: Persistence Foundation

### Goal

Implement frozen P2 data architecture.

### Epic E1.1: Database Bootstrap

Tasks:

```text
T1.1 Add SQLAlchemy 2.x and Alembic dependencies
T1.2 Add database settings and engine/session factory
T1.3 Add initial Alembic environment
T1.4 Create SQLite development database path
T1.5 Add PostgreSQL test configuration
```

### Epic E1.2: Common Resource Persistence

Tasks:

```text
T1.6 Implement UUIDv7-compatible ID generator
T1.7 Implement common metadata/spec/status ORM mixin
T1.8 Implement generation and resource_version rules
T1.9 Implement soft-delete repository behaviour
T1.10 Implement optimistic concurrency exception model
```

### Epic E1.3: Core Repositories

Tasks:

```text
T1.11 TaskRepository
T1.12 WorkflowRepository
T1.13 AuditEventRepository
T1.14 ResourceEventRepository
T1.15 ClusterRepository
T1.16 NodeRepository
T1.17 StoragePoolRepository
T1.18 StorageClassRepository
T1.19 VMRepository
T1.20 BackupRepository
T1.21 PluginRepository
T1.22 UserRepository
```

Acceptance:

```text
SQLite migrations complete from empty database.
Repository tests pass on SQLite.
Core migration compatibility test passes on PostgreSQL.
No service writes directly to SQL.
```

---

## 4. Milestone M2: Runtime Convergence

### Goal

Create one Runtime Plane implementation.

### Epic E2.1: Unified Task Model

Tasks:

```text
T2.1 Define canonical Task domain and API schema
T2.2 Map legacy TaskInfo to canonical Task
T2.3 Map JobRecord to canonical Task compatibility response
T2.4 Persist task lifecycle in TaskRepository
T2.5 Define terminal-state immutability
```

### Epic E2.2: Executor Abstraction

Tasks:

```text
T2.6 Define Executor protocol
T2.7 Implement ExecutorRegistry
T2.8 Implement AnsibleExecutor
T2.9 Implement command argument safety validation
T2.10 Add kubectl/virtctl executor interface stubs
T2.11 Add executor timeout and cancellation contract
```

### Epic E2.3: Worker Runtime

Tasks:

```text
T2.12 Implement queued TaskService
T2.13 Implement local worker loop for V2.0
T2.14 Implement worker claim/heartbeat model
T2.15 Persist stdout/stderr log references
T2.16 Recover orphaned running tasks at startup
```

Acceptance:

```text
Only one executor service is used by new code.
Direct operations create persistent Task resources.
API requests do not block for playbook completion.
Legacy job endpoint remains available through compatibility adapter.
```

---

## 5. Milestone M3: Workflow Engine

### Goal

Implement the frozen P4 asynchronous workflow model.

### Epic E3.1: Workflow State Machine

Tasks:

```text
T3.1 Persist Workflow and WorkflowStep models
T3.2 Implement pending -> queued -> running -> terminal transitions
T3.3 Implement step ordering and dependency validation
T3.4 Implement failure propagation
T3.5 Implement workflow cancellation
T3.6 Implement timeout handling
```

### Epic E3.2: Retry and Compensation

Tasks:

```text
T3.7 Define retry policy fields
T3.8 Implement bounded retry with backoff
T3.9 Define compensation step model
T3.10 Add resume-from-failed-step design support
T3.11 Persist retry and compensation events
```

### Epic E3.3: Safety and Approval

Tasks:

```text
T3.12 Centralize destructive confirmation policy
T3.13 Add confirmation phrase validation
T3.14 Add approval state interface
T3.15 Audit rejected and approved destructive workflows
```

### Epic E3.4: Template Migration

Tasks:

```text
T3.16 Migrate governance.full_check
T3.17 Migrate backup.vm
T3.18 Migrate restore.vm
T3.19 Migrate observability.preflight
T3.20 Add schema validation for workflow parameters
```

Acceptance:

```text
POST workflow returns immediately.
Worker executes persisted steps.
Failure, cancellation and retry are testable.
Destructive workflows cannot run without central policy approval.
```

---

## 6. Milestone M4: Resource Plane and API

### Goal

Replace action facades with frozen resource APIs.

### Epic E4.1: Common Resource API

Tasks:

```text
T4.1 Implement common resource response model
T4.2 Implement pagination and filtering
T4.3 Implement labels and annotations queries
T4.4 Implement resource_version precondition handling
T4.5 Implement consistent error envelope
T4.6 Implement request correlation ID
```

### Epic E4.2: Core Resource Services

Tasks:

```text
T4.7 ClusterService and routes
T4.8 NodeService and routes
T4.9 StoragePoolService and routes
T4.10 StorageClassService and routes
T4.11 VMService and routes
T4.12 BackupService and routes
T4.13 PluginService and routes
T4.14 UserService minimum routes
```

### Epic E4.3: Action Adapters

Tasks:

```text
T4.15 Convert cluster actions to Workflow submission
T4.16 Convert governance routes to Workflow submission
T4.17 Convert backup routes to Workflow submission
T4.18 Convert KubeVirt actions to Workflow submission
T4.19 Convert observability actions to Task/Workflow submission
T4.20 Remove direct router imports of executors
```

### Epic E4.4: Compatibility API

Tasks:

```text
T4.21 Preserve existing routes with deprecation headers
T4.22 Add legacy job-to-task adapter
T4.23 Document API migration path
T4.24 Add OpenAPI contract snapshots
```

Acceptance:

```text
All resource responses use metadata/spec/status.
All complex actions produce Workflows.
No router executes playbooks directly.
API v1 compatibility tests pass.
```

---

## 7. Milestone M5: Security, Audit and Events

### Goal

Implement minimum enterprise governance baseline.

### Epic E5.1: Identity Context and RBAC

Tasks:

```text
T5.1 Add request identity context
T5.2 Add local development identity provider
T5.3 Define RBAC interface and policy evaluator
T5.4 Protect resource read/write/action permissions
T5.5 Audit denied requests
T5.6 Define OIDC/LDAP extension interface
```

### Epic E5.2: AuditEvent

Tasks:

```text
T5.7 Replace JSONL-only audit with AuditRepository
T5.8 Add actor, action, target, result, request_id and source fields
T5.9 Add audit query API
T5.10 Preserve optional JSONL export adapter
```

### Epic E5.3: ResourceEvent

Tasks:

```text
T5.11 Emit resource lifecycle events
T5.12 Emit workflow and task events
T5.13 Implement transactional outbox-compatible write path
T5.14 Add event query API
T5.15 Add WebSocket event stream adapter
```

Acceptance:

```text
Every mutating API action is authorized and audited.
Resource and workflow transitions emit events.
Audit records are append-only.
```

---

## 8. Milestone M6: Plugin SDK

### Goal

Implement the frozen P5 extension boundary.

### Epic E6.1: Plugin Manifest and Registry

Tasks:

```text
T6.1 Define plugin manifest schema
T6.2 Implement capability registry
T6.3 Implement install/enable/disable lifecycle
T6.4 Implement compatibility validation
T6.5 Implement plugin health status
```

### Epic E6.2: Plugin Security and API

Tasks:

```text
T6.6 Define plugin API client
T6.7 Prevent direct database access by SDK contract
T6.8 Define credentials and secret reference model
T6.9 Add plugin audit events
```

### Epic E6.3: Reference Plugins

Tasks:

```text
T6.10 Convert one storage backend into reference plugin
T6.11 Add backup capability reference plugin
T6.12 Add observability capability reference plugin
```

Acceptance:

```text
At least one external plugin is installed and queried through public APIs.
Plugin cannot bypass Resource/Workflow boundaries.
```

---

## 9. Milestone M7: Web Console

### Goal

Implement the frozen P6 resource-first user experience.

### Epic E7.1: Console Foundation

Tasks:

```text
T7.1 Select and scaffold frontend stack
T7.2 Generate typed API client from OpenAPI
T7.3 Implement authentication/session shell
T7.4 Implement global error and request ID display
```

### Epic E7.2: Resource Views

Tasks:

```text
T7.5 Cluster views
T7.6 Node views
T7.7 StoragePool and StorageClass views
T7.8 VM views
T7.9 Backup views
T7.10 Plugin views
```

### Epic E7.3: Operations and Governance Views

Tasks:

```text
T7.11 Workflow list/detail/timeline
T7.12 Task logs and status
T7.13 Destructive confirmation UX
T7.14 Audit explorer
T7.15 Live event updates
```

Acceptance:

```text
Core resources are manageable without direct playbook knowledge.
Workflow and Task states are visible.
Destructive actions require explicit UX confirmation.
```

---

## 10. Milestone M8: Release Validation

### Goal

Pass frozen P7/P8 release gates.

### Epic E8.1: Test Completion

Tasks:

```text
T8.1 Unit test coverage for services and repositories
T8.2 API contract tests
T8.3 Workflow state-machine tests
T8.4 SQLite/PostgreSQL migration tests
T8.5 Executor integration tests
T8.6 Destructive safety tests
T8.7 Backup/restore scenario tests
T8.8 Plugin compatibility tests
T8.9 Web Console end-to-end tests
```

### Epic E8.2: Packaging and Operations

Tasks:

```text
T8.10 Container image build
T8.11 Development compose deployment
T8.12 Kubernetes deployment manifests or Helm chart
T8.13 Database backup and migration runbook
T8.14 Upgrade and rollback runbook
T8.15 Security and dependency scan
```

### Epic E8.3: Release Readiness

Tasks:

```text
T8.16 Traceability matrix from P0-P8 to code/tests
T8.17 Known limitations document
T8.18 API deprecation document
T8.19 V2.0 acceptance report
T8.20 Release candidate sign-off
```

---

## 11. Recommended Implementation Order

First implementation sequence:

```text
1. T0.1-T0.6 Engineering gates
2. T1.1-T1.10 Database and common persistence
3. T1.11-T1.14 Task/Workflow/Audit/Event repositories
4. T2.1-T2.16 Runtime convergence
5. T3.1-T3.20 Workflow migration
6. T4.1-T4.24 Resource/API convergence
7. M5 security and event governance
8. M6-M8 product completion
```

---

## 12. Definition of Done

A Task is complete only when:

```text
Code implemented
Unit tests added
Integration/contract tests added where applicable
Documentation updated
Migration included where applicable
Audit and safety behaviour verified
No frozen-spec violation introduced
CI passes
```

An Epic is complete only when all tasks meet Definition of Done and its acceptance criteria pass.

A Milestone is complete only when the applicable P8 release gates pass.
