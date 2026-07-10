# CPP V2.0 Implementation Roadmap v1.0

> Status: ACTIVE
> Input: Frozen P0-P8 design baseline and Implementation Gap Analysis
> Delivery model: Milestone -> Epic -> Task -> Acceptance Gate

## 1. Delivery Principles

1. Resolve architectural blockers before adding product features.
2. Preserve compatibility through adapters and deprecation windows.
3. Every Epic must trace to one or more frozen specifications.
4. No task is complete without tests, documentation and safety validation.
5. Implement in vertical slices that produce a runnable platform.

## 2. Milestones

### M0 — Architecture Foundation

Goal: establish one execution model and one persistence boundary.

Exit criteria:

- Unified Task model.
- Runtime Service and Executor protocol.
- SQLite repository layer and Alembic baseline.
- Workflow/Task/Audit persistence.
- Routers no longer import executor implementations.

### M1 — Resource Control Plane

Goal: implement frozen metadata/spec/status resource services.

Exit criteria:

- Universal Resource schema.
- Cluster, Node, StoragePool, StorageClass, VM and Backup repositories.
- generation/resource_version enforcement.
- ResourceEvent production.
- Frozen API response and pagination conventions.

### M2 — Workflow and Operations

Goal: implement asynchronous workflow orchestration.

Exit criteria:

- Queue/claim/run/reconcile lifecycle.
- Retry, timeout and cancellation baseline.
- Destructive confirmation policy.
- Workflow templates for governance, VM backup/restore and observability.
- Compatibility adapters for existing operation endpoints.

### M3 — Plugin and Product Surface

Goal: deliver extension and user-facing platform capabilities.

Exit criteria:

- Plugin manifest, registry, capability and lifecycle API.
- Initial storage plugin adapters.
- Resource-first Web Console baseline.
- Audit and workflow views.

### M4 — Production Readiness

Goal: satisfy P7/P8 release and validation gates.

Exit criteria:

- PostgreSQL compatibility test.
- CI quality/security/migration gates.
- Packaging and deployment artifacts.
- Backup/restore and upgrade tests.
- Acceptance evidence for V2.0 release.

## 3. Epic Breakdown

### EPIC-001 Unified Runtime and Executor

Traceability: P0-02, P1-01, P4, P7.

Tasks:

- Define Executor protocol and ExecutionResult.
- Implement AnsibleExecutor.
- Introduce ExecutorRegistry.
- Implement RuntimeService submit/claim/execute.
- Replace JobRecord and TaskInfo with one Task resource.
- Add compatibility adapters for old executor callers.
- Remove duplicate executor after migration.

### EPIC-002 Persistence Foundation

Traceability: P2-01, P2-02, P2-03.

Tasks:

- Add SQLAlchemy and Alembic dependencies.
- Add database settings and session management.
- Create initial migration.
- Create Workflow, Task, AuditEvent and ResourceEvent models.
- Define repository interfaces and SQL implementations.
- Add optimistic concurrency helpers.
- Add SQLite tests and PostgreSQL compatibility job.

### EPIC-003 Workflow Engine v2

Traceability: P3 and P4.

Tasks:

- Create queued Workflow without blocking API request.
- Persist workflow steps/tasks transactionally.
- Add worker execution loop.
- Add workflow reconciliation.
- Implement failure, cancellation and retry baseline.
- Add confirmation policy service.
- Migrate existing workflow templates.

### EPIC-004 API Boundary Migration

Traceability: P0-02 and P3.

Tasks:

- Remove direct executor imports from routers.
- Add WorkflowService and RuntimeService dependencies.
- Implement frozen response envelope.
- Add compatibility endpoints and deprecation headers.
- Normalize errors, pagination and request IDs.
- Add OpenAPI contract tests.

### EPIC-005 Core Resource Services

Traceability: P1, P2 and P3.

Tasks:

- Implement universal metadata/spec/status schemas.
- Implement Cluster resource.
- Implement Node resource.
- Implement StoragePool and StorageClass resources.
- Implement VM and Backup resources.
- Emit ResourceEvent on lifecycle transitions.

### EPIC-006 Audit and Observability

Traceability: P2, P6 and P8.

Tasks:

- Replace JSONL audit with AuditRepository.
- Add actor/action/target/result/request metadata.
- Add audit query API.
- Add workflow/task metrics.
- Add structured logging and correlation IDs.

### EPIC-007 Plugin SDK

Traceability: P5.

Tasks:

- Define plugin manifest schema.
- Add plugin discovery and registry.
- Add capability declaration.
- Add enable/disable lifecycle.
- Enforce API-only plugin boundary.
- Implement initial storage plugin examples.

### EPIC-008 Web Console

Traceability: P6.

Tasks:

- Create frontend project skeleton.
- Implement resource navigation.
- Implement Cluster/Node/Storage/VM views.
- Implement Workflow/Task/Audit views.
- Add destructive operation confirmation UX.

### EPIC-009 Engineering and Validation

Traceability: P7 and P8.

Tasks:

- Unit, repository, API and workflow tests.
- Migration upgrade/downgrade tests.
- Lint, type and security checks.
- Container/package build.
- Release versioning and changelog.
- End-to-end acceptance scenarios.

## 4. Execution Order

```text
EPIC-001 + EPIC-002
        ↓
EPIC-003 + EPIC-004
        ↓
EPIC-005 + EPIC-006
        ↓
EPIC-007 + EPIC-008
        ↓
EPIC-009 release gates
```

EPIC-001 and EPIC-002 may progress in parallel but must converge on one Task repository contract.

## 5. First Implementation Sprint

### Sprint S0 — Foundation

Tasks:

1. Add database and migration dependencies.
2. Add database configuration/session module.
3. Define unified Task schema and status lifecycle.
4. Define Executor protocol and Ansible executor.
5. Add TaskRepository interface.
6. Add SQLite Task repository implementation.
7. Add RuntimeService.
8. Migrate one low-risk endpoint as a reference vertical slice.
9. Add tests for task submission and state transition.

Acceptance:

- API submits a Task through RuntimeService.
- Task is persisted in SQLite.
- AnsibleExecutor runs through ExecutorRegistry.
- Task reaches succeeded or failed terminal state.
- Router has no direct executor implementation import.

## 6. Priority Rules

- P0: architecture blocker; no dependent feature work should bypass it.
- P1: required for V2.0 functional baseline.
- P2: required for product completeness.
- P3: post-V2.0 enhancement.

## 7. Completion Reporting

Every implementation task must record:

```text
Design references
Files changed
Migration impact
Compatibility impact
Tests added
Safety considerations
Acceptance evidence
```
