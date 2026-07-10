# CPP V2.0 Implementation Tracker

> Status: ACTIVE
> Source: IMPLEMENTATION-PLAN-v1.0
> Design baseline: FROZEN-P0-01 through FROZEN-P8
> Tracking mode: repository Markdown, because GitHub Issues is disabled for this repository.

---

## Overall Progress

| Milestone | Status | Progress | Primary outcome |
|---|---|---:|---|
| M0 Engineering Baseline | In Progress | 5/10 | Quality gates and compatibility inventory |
| M1 Persistence Foundation | Not Started | 0/22 | SQLite, Alembic and repositories |
| M2 Runtime Convergence | Not Started | 0/16 | One Task model and one Executor boundary |
| M3 Workflow Engine | Not Started | 0/20 | Persistent asynchronous workflows |
| M4 Resource Plane and API | Not Started | 0/? | Frozen resource APIs and compatibility adapters |
| M5 Security, Audit and Events | Not Started | 0/? | AuditEvent, ResourceEvent and policy controls |
| M6 Plugin SDK | Not Started | 0/? | Stable plugin contract and lifecycle |
| M7 Web Console | Not Started | 0/? | Resource-first management console |
| M8 Release Validation | Not Started | 0/? | P8 release and acceptance gates |

---

## P0 Architecture Blockers

| Gap | Status | Required result |
|---|---|---|
| GAP-001 Duplicate executors | Open | One Executor interface and registry |
| GAP-002 Duplicate Task/Job models | Open | Canonical Task resource with compatibility adapter |
| GAP-003 Non-compliant persistence | Open | Repository + SQLite + Alembic |
| GAP-004 Routers bypass Workflow | Open | Router -> Service -> Workflow/Resource boundary |
| GAP-005 Synchronous workflow execution | Open | Persistent asynchronous worker execution |

---

## M0 Engineering Baseline

### E0.1 Project Quality Gates

| Task | Status | Evidence / next action |
|---|---|---|
| T0.1 Add pytest baseline | Done | `platform-api/tests/test_health.py` |
| T0.2 Add Ruff configuration | Done | `platform-api/pyproject.toml` |
| T0.3 Add Mypy configuration | Done | `platform-api/pyproject.toml` |
| T0.4 Add CI for lint/type/test | Done | `.github/workflows/platform-api-ci.yml` |
| T0.5 Add startup smoke test | Done | Health TestClient imports `app.main` |
| T0.6 Add architecture dependency tests | Pending | Prevent new Router -> Executor imports while legacy violations are migrated |

### E0.2 Compatibility Inventory

| Task | Status | Evidence / next action |
|---|---|---|
| T0.7 Inventory current API routes | Pending | Create `CURRENT-API-INVENTORY.md` |
| T0.8 Inventory executor call sites | Pending | Create `EXECUTOR-CALL-SITE-INVENTORY.md` |
| T0.9 Inventory TaskInfo/JobRecord consumers | Pending | Map legacy models and endpoints |
| T0.10 Define compatibility/deprecation map | Pending | Freeze endpoint and model adapters for M2/M4 |

### M0 Exit Gate

```text
[ ] CI passes lint, type checks and tests
[ ] Platform API imports successfully
[ ] Architecture dependency test blocks new Router -> Executor imports
[ ] API and executor inventories are complete
[ ] Compatibility/deprecation map is approved
```

---

## M1 Persistence Foundation

### E1.1 Database Bootstrap

```text
[ ] T1.1 Add SQLAlchemy 2.x and Alembic dependencies
[ ] T1.2 Add database settings and engine/session factory
[ ] T1.3 Add initial Alembic environment
[ ] T1.4 Create SQLite development database path
[ ] T1.5 Add PostgreSQL test configuration
```

### E1.2 Common Resource Persistence

```text
[ ] T1.6 UUIDv7-compatible ID generator
[ ] T1.7 metadata/spec/status ORM mixin
[ ] T1.8 generation/resource_version rules
[ ] T1.9 soft-delete repository behaviour
[ ] T1.10 optimistic concurrency exception model
```

### E1.3 Core Repositories

```text
[ ] T1.11 TaskRepository
[ ] T1.12 WorkflowRepository
[ ] T1.13 AuditEventRepository
[ ] T1.14 ResourceEventRepository
[ ] T1.15 ClusterRepository
[ ] T1.16 NodeRepository
[ ] T1.17 StoragePoolRepository
[ ] T1.18 StorageClassRepository
[ ] T1.19 VMRepository
[ ] T1.20 BackupRepository
[ ] T1.21 PluginRepository
[ ] T1.22 UserRepository
```

---

## M2 Runtime Convergence

```text
[ ] Canonical Task resource
[ ] TaskInfo compatibility adapter
[ ] JobRecord compatibility adapter
[ ] Executor protocol and registry
[ ] AnsibleExecutor
[ ] kubectl/virtctl executor interfaces
[ ] timeout and cancellation contract
[ ] local worker queue
[ ] orphaned-task recovery
```

---

## M3 Workflow Engine

```text
[ ] Persistent Workflow and WorkflowStep
[ ] asynchronous state machine
[ ] step dependency validation
[ ] failure propagation
[ ] cancellation and timeout
[ ] bounded retry and backoff
[ ] compensation model
[ ] resume support
[ ] central destructive confirmation policy
[ ] migrate governance, backup, restore and observability templates
```

---

## M4-M8 Summary

```text
M4: frozen Resource Plane APIs, pagination, optimistic concurrency and legacy adapters
M5: authentication boundary, audit immutability, ResourceEvent and policy enforcement
M6: plugin manifest, capability model, lifecycle, security and conformance tests
M7: resource-first Web Console, workflow/task visibility and destructive UX
M8: unit/integration/contract/e2e tests, packaging, upgrade, recovery and release gates
```

---

## Execution Rule

Each task must follow this sequence:

```text
Frozen design reference
-> implementation change
-> automated tests
-> compatibility assessment
-> documentation update
-> tracker update
```

A task must not be marked Done solely because code was written.
