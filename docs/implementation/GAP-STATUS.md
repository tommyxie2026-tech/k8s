# CPP V2.0 Implementation Status

> Tracking mode: repository-native because GitHub Issues are disabled
> Baseline: IMPLEMENTATION-PLAN-v1.0.md
> Last updated: 2026-07-11

## Status Legend

```text
[ ] planned
[~] in progress
[!] blocked
[x] done
```

---

## M0 Engineering Baseline

Status: `[~] in progress`

### E0.1 Project Quality Gates

- [ ] T0.1 Add pytest baseline and test directory structure
- [ ] T0.2 Add Ruff configuration
- [ ] T0.3 Add mypy or pyright baseline
- [ ] T0.4 Add CI workflow for lint, unit tests and import validation
- [ ] T0.5 Add application startup smoke test
- [ ] T0.6 Add architecture dependency test preventing router -> executor imports

### E0.2 Compatibility Inventory

- [~] T0.7 Inventory current API routes
- [x] T0.8 Inventory executor call sites
- [x] T0.9 Inventory TaskInfo and JobRecord consumers
- [ ] T0.10 Define compatibility and deprecation map

Current findings:

```text
app.core.executor.PlaybookExecutor
app.services.executor.Executor
TaskInfo / TaskStatus
JobRecord / JobStatus
WorkflowStep embeds execution result
Routers use mixed executor paths
```

M0 acceptance:

- [ ] CI runs on every pull request
- [ ] Platform API startup smoke test passes
- [ ] Router-to-executor imports are blocked by tests
- [ ] Compatibility/deprecation map is committed

---

## M1 Persistence Foundation

Status: `[ ] planned`

### E1.1 Database Bootstrap

- [ ] T1.1 Add SQLAlchemy 2.x and Alembic dependencies
- [ ] T1.2 Add database settings and engine/session factory
- [ ] T1.3 Add Alembic environment
- [ ] T1.4 Add SQLite development database
- [ ] T1.5 Add PostgreSQL test configuration

### E1.2 Common Resource Persistence

- [ ] T1.6 UUIDv7-compatible ID generator
- [ ] T1.7 metadata/spec/status ORM mixin
- [ ] T1.8 generation/resource_version rules
- [ ] T1.9 soft-delete repository behaviour
- [ ] T1.10 optimistic concurrency exceptions

### E1.3 Core Repositories

- [ ] TaskRepository
- [ ] WorkflowRepository
- [ ] AuditEventRepository
- [ ] ResourceEventRepository
- [ ] ClusterRepository
- [ ] NodeRepository
- [ ] StoragePoolRepository
- [ ] StorageClassRepository
- [ ] VMRepository
- [ ] BackupRepository
- [ ] PluginRepository
- [ ] UserRepository

---

## M2 Runtime Convergence

Status: `[ ] planned`

### E2.1 Unified Task Model

- [ ] Define canonical Task schema
- [ ] Map legacy TaskInfo to Task
- [ ] Map JobRecord to compatibility Task response
- [ ] Persist Task lifecycle
- [ ] Enforce terminal-state immutability

### E2.2 Executor Abstraction

- [ ] Define Executor protocol
- [ ] Add ExecutorRegistry
- [ ] Implement AnsibleExecutor
- [ ] Add command argument safety validation
- [ ] Add kubectl/virtctl executor interface stubs
- [ ] Add timeout and cancellation contract

### E2.3 Worker Runtime

- [ ] Implement queued TaskService
- [ ] Implement local worker loop
- [ ] Implement claim/heartbeat model
- [ ] Persist log references
- [ ] Recover orphaned tasks

---

## M3 Workflow Engine

Status: `[ ] planned`

- [ ] Persist Workflow and WorkflowStep
- [ ] Add queued lifecycle
- [ ] Add dependency validation
- [ ] Add failure propagation
- [ ] Add cancellation and timeout
- [ ] Add bounded retry and backoff
- [ ] Add compensation model
- [ ] Centralize destructive confirmation
- [ ] Migrate existing workflow templates

---

## M4 Resource Plane and API

Status: `[ ] planned`

- [ ] Common Resource envelope
- [ ] Cluster resource API
- [ ] Node resource API
- [ ] StoragePool resource API
- [ ] StorageClass resource API
- [ ] VM resource API
- [ ] Backup resource API
- [ ] Pagination/filter/sort
- [ ] resource_version conflict handling
- [ ] compatibility/deprecation headers

---

## M5 Security, Audit and Events

Status: `[ ] planned`

- [ ] Request correlation middleware
- [ ] Structured AuditEvent persistence
- [ ] ResourceEvent persistence
- [ ] Actor/action/target/result model
- [ ] Audit query API
- [ ] Append-only enforcement

---

## M6 Plugin SDK

Status: `[ ] planned`

- [ ] Plugin manifest
- [ ] Capability model
- [ ] Plugin registry
- [ ] Lifecycle validation
- [ ] NFS adapter
- [ ] iSCSI adapter
- [ ] Ceph adapter

---

## M7 Web Console

Status: `[ ] planned`

- [ ] Console scaffold
- [ ] Resource navigation
- [ ] Cluster/Node views
- [ ] Storage views
- [ ] VM views
- [ ] Backup/restore workflows
- [ ] Workflow/Task views
- [ ] Audit views

---

## M8 Release Validation

Status: `[ ] planned`

- [ ] Unit test gate
- [ ] Migration test gate
- [ ] API contract gate
- [ ] Workflow safety gate
- [ ] Container packaging
- [ ] SQLite backup/restore validation
- [ ] PostgreSQL compatibility
- [ ] Upgrade test matrix
- [ ] P8 acceptance report

---

## Immediate Next Task

```text
T0.10 Define compatibility and deprecation map
```

After T0.10, implementation begins with T0.1–T0.6, then M1 persistence foundation.
