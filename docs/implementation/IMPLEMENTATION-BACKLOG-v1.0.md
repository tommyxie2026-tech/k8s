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

- [x] T001 Define unified Executor protocol and ExecutionResult — DONE
- [x] T002 Implement AnsibleExecutor — DONE
- [x] T003 Implement ExecutorRegistry — DONE
- [ ] T004 Define unified Task resource — NEXT
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

1. T004 unified Task schema.
2. T020-T023 SQLite persistence baseline.
3. T006 RuntimeService.
4. T007 WorkflowEngine migration.
5. Migrate one non-destructive endpoint as vertical slice.

## Completed Evidence

### T001-T003

```text
Design references: FROZEN-P0-02, FROZEN-P4
Files:
- platform-api/app/executors/base.py
- platform-api/app/executors/ansible.py
- platform-api/app/executors/registry.py
Compatibility impact: additive only; legacy executors remain active
Migration impact: none
Tests: pending with RuntimeService vertical slice
Acceptance evidence: executor-neutral request/result, Ansible implementation and registry exist
```

## Update Rule

Every implementation commit must update this backlog when task status changes and must identify:

```text
Design reference
Compatibility impact
Migration impact
Tests
Acceptance evidence
```
