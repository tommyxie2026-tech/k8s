# CPP V2.0 Implementation Tracker v1.0

> Status: ACTIVE
> Source of truth:
> - `DESIGN-TO-CODE-GAP-ANALYSIS-v1.0.md`
> - `IMPLEMENTATION-PLAN-v1.0.md`
> - `docs/frozen/FROZEN-P0-01-*` through `FROZEN-P8-*`

---

## Programme Status

- [ ] M0 Engineering Baseline
- [ ] M1 Persistence Foundation
- [ ] M2 Runtime Convergence
- [ ] M3 Workflow Engine
- [ ] M4 Resource Plane and API
- [ ] M5 Security, Audit and Events
- [ ] M6 Plugin SDK
- [ ] M7 Web Console
- [ ] M8 Release Validation

---

## P0 Blockers

- [ ] Remove dual executor architecture
- [ ] Converge Task and Job into one Task resource
- [ ] Replace in-memory/file persistence with repositories and SQLite/Alembic
- [ ] Remove Router -> Executor direct dependencies
- [ ] Make workflow execution asynchronous and durable

---

## Sprint 1: Engineering and Persistence Baseline

### M0 / E0.1 Quality Gates

- [x] T0.1 Add pytest baseline and test directory structure
- [x] T0.2 Add Python lint configuration
- [x] T0.3 Add type-check baseline
- [x] T0.4 Add CI workflow for lint, tests and import validation
- [x] T0.5 Add application startup smoke test
- [x] T0.6 Add architecture dependency test preventing Router -> Executor imports

### M0 / E0.2 Compatibility Inventory

- [x] T0.7 Inventory current API routes
- [x] T0.8 Inventory executor call sites
- [x] T0.9 Inventory TaskInfo and JobRecord consumers
- [x] T0.10 Define compatibility and deprecation map

Inventory artifact:

```text
docs/implementation/CURRENT-API-EXECUTION-INVENTORY-v1.0.md
```

### M1 / E1.1 Database Bootstrap

- [x] T1.1 Add SQLAlchemy 2.x and Alembic dependencies
- [ ] T1.2 Add database settings and session factory
- [ ] T1.3 Add initial Alembic environment
- [ ] T1.4 Create SQLite development database path
- [ ] T1.5 Add PostgreSQL compatibility test configuration

### M1 / E1.2 Resource Persistence Baseline

- [ ] T1.6 Add UUIDv7-compatible ID generator
- [ ] T1.7 Add common metadata/spec/status ORM mixin
- [ ] T1.8 Implement generation and resource_version rules
- [ ] T1.9 Implement soft-delete repository behaviour
- [ ] T1.10 Implement optimistic concurrency exception model

### M1 / E1.3 Initial Repositories

- [ ] T1.11 Implement TaskRepository
- [ ] T1.12 Implement WorkflowRepository
- [ ] T1.13 Implement AuditEventRepository
- [ ] T1.14 Implement ResourceEventRepository

---

## Sprint 1 Exit Criteria

- [x] Platform API imports and starts successfully
- [x] CI executes lint, tests and architecture dependency checks
- [ ] Workflow and Task records survive process restart
- [ ] Database schema initializes through Alembic
- [ ] Repository tests pass on SQLite
- [x] No existing playbook capability is removed
- [x] No new Router -> Executor dependency is introduced

---

## M2 Runtime Convergence

- [ ] T2.1 Define canonical Task schema
- [ ] T2.2 Add legacy TaskInfo compatibility adapter
- [ ] T2.3 Add JobRecord compatibility adapter
- [ ] T2.4 Persist Task lifecycle
- [ ] T2.5 Enforce terminal-state immutability
- [ ] T2.6 Define Executor protocol
- [ ] T2.7 Implement ExecutorRegistry
- [ ] T2.8 Implement AnsibleExecutor
- [ ] T2.9 Add command argument safety validation
- [ ] T2.10 Add kubectl/virtctl interface stubs
- [ ] T2.11 Add timeout/cancellation contract
- [ ] T2.12 Implement queued TaskService
- [ ] T2.13 Implement local worker loop
- [ ] T2.14 Implement worker claim/heartbeat
- [ ] T2.15 Persist log references
- [ ] T2.16 Recover orphaned tasks

---

## M3 Workflow Engine

- [ ] T3.1 Persist Workflow and WorkflowStep models
- [ ] T3.2 Implement workflow state machine
- [ ] T3.3 Implement step dependency validation
- [ ] T3.4 Implement failure propagation
- [ ] T3.5 Implement cancellation
- [ ] T3.6 Implement timeout handling
- [ ] T3.7 Add retry policy
- [ ] T3.8 Implement bounded retry/backoff
