# CPP V2.0 Implementation Backlog v1.0

> Status: ACTIVE
> Note: GitHub Issues are disabled in this repository, so this file is the version-controlled implementation task ledger.

## Status Legend

```text
TODO
IN_PROGRESS
BLOCKED
DONE
```

## M0 Architecture Foundation

### EPIC-001 Unified Runtime and Executor

Status: IN_PROGRESS

- [ ] T001 Define unified Executor protocol and ExecutionResult — IN_PROGRESS
- [ ] T002 Implement AnsibleExecutor — IN_PROGRESS
- [ ] T003 Implement ExecutorRegistry — IN_PROGRESS
- [ ] T004 Define unified Task resource
- [ ] T005 Implement TaskRepository
- [ ] T006 Implement RuntimeService
- [ ] T007 Migrate WorkflowEngine to RuntimeService
- [ ] T008 Migrate routers away from executor imports
- [ ] T009 Add compatibility adapters
- [ ] T010 Remove duplicate JobRecord/executor path

### EPIC-002 Persistence Foundation

Status: TODO

- [ ] T020 Add SQLAlchemy/Alembic dependencies
- [ ] T021 Add database configuration and session factory
- [ ] T022 Add initial migration
- [ ] T023 Implement Task persistence
- [ ] T024 Implement Workflow persistence
- [ ] T025 Implement AuditEvent persistence
- [ ] T026 Implement ResourceEvent persistence
- [ ] T027 Add repository tests

### EPIC-003 Workflow Engine v2

Status: TODO

- [ ] T030 Queue workflow without blocking API
- [ ] T031 Persist workflow tasks atomically
- [ ] T032 Add worker claim/execute loop
- [ ] T033 Add workflow reconciliation
- [ ] T034 Add cancellation/retry/timeout baseline
- [ ] T035 Migrate workflow templates

### EPIC-004 API Boundary Migration

Status: TODO

- [ ] T040 Add service dependency boundary
- [ ] T041 Remove direct executor imports from routers
- [ ] T042 Add response envelope and pagination
- [ ] T043 Add compatibility/deprecation behavior
- [ ] T044 Add OpenAPI contract tests

## M1 Resource Control Plane

- [ ] EPIC-005 Universal Resource and core repositories
- [ ] EPIC-006 Audit, ResourceEvent and observability

## M2 Product Surface

- [ ] EPIC-007 Plugin SDK
- [ ] EPIC-008 Web Console

## M3 Production Readiness

- [ ] EPIC-009 CI, packaging, migration and acceptance gates

## Current Sprint S0

1. T001 Executor protocol.
2. T002 AnsibleExecutor.
3. T003 ExecutorRegistry.
4. T004 unified Task schema.
5. T020-T023 SQLite persistence baseline.
6. T006 RuntimeService.
7. Migrate one non-destructive endpoint as vertical slice.

## Update Rule

Every implementation commit must update this backlog when task status changes and must identify:

```text
Design reference
Compatibility impact
Migration impact
Tests
Acceptance evidence
```
