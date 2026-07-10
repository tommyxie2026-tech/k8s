# CPP V2.0 Implementation Backlog

> Tracking mode: Repository Markdown
> Reason: GitHub Issues are disabled for this repository.
> Source: `IMPLEMENTATION-PLAN-v1.0.md`

---

## Programme Status

```text
Design baseline: COMPLETE
Gap analysis: COMPLETE
Implementation planning: COMPLETE
Implementation: NOT STARTED
```

---

## M0 Engineering Baseline

### E0.1 Project Quality Gates

- [ ] T0.1 Add pytest baseline and test directory structure
- [ ] T0.2 Add Python lint configuration
- [ ] T0.3 Add static type checking baseline
- [ ] T0.4 Add CI workflow for lint, tests and import validation
- [ ] T0.5 Add application startup smoke test
- [ ] T0.6 Add architecture dependency tests preventing router-to-executor imports

### E0.2 Compatibility Inventory

- [ ] T0.7 Inventory all current API routes
- [ ] T0.8 Inventory all executor call sites
- [ ] T0.9 Inventory TaskInfo and JobRecord consumers
- [ ] T0.10 Define compatibility and deprecation map

---

## M1 Persistence Foundation

### E1.1 Database Bootstrap

- [ ] T1.1 Add SQLAlchemy and Alembic dependencies
- [ ] T1.2 Add database settings and session factory
- [ ] T1.3 Add initial Alembic environment
- [ ] T1.4 Configure SQLite development database
- [ ] T1.5 Add PostgreSQL compatibility test configuration

### E1.2 Common Resource Persistence

- [ ] T1.6 UUIDv7-compatible ID generator
- [ ] T1.7 metadata/spec/status ORM foundation
- [ ] T1.8 generation/resource_version rules
- [ ] T1.9 soft-delete repository behaviour
- [ ] T1.10 optimistic concurrency exceptions

### E1.3 Core Repositories

- [ ] T1.11 TaskRepository
- [ ] T1.12 WorkflowRepository
- [ ] T1.13 AuditEventRepository
- [ ] T1.14 ResourceEventRepository
- [ ] T1.15 ClusterRepository
- [ ] T1.16 NodeRepository
- [ ] T1.17 StoragePoolRepository
- [ ] T1.18 StorageClassRepository
- [ ] T1.19 VMRepository
- [ ] T1.20 BackupRepository
- [ ] T1.21 PluginRepository
- [ ] T1.22 UserRepository

---

## M2 Runtime Convergence

### E2.1 Unified Task Model

- [ ] T2.1 Define canonical Task schema
- [ ] T2.2 Add TaskInfo compatibility mapping
- [ ] T2.3 Add JobRecord compatibility mapping
- [ ] T2.4 Persist task lifecycle
- [ ] T2.5 Enforce terminal-state immutability

### E2.2 Executor Abstraction

- [ ] T2.6 Define Executor protocol
- [ ] T2.7 Implement ExecutorRegistry
- [ ] T2.8 Implement AnsibleExecutor
- [ ] T2.9 Add argument safety validation
- [ ] T2.10 Add kubectl/virtctl executor stubs
- [ ] T2.11 Add timeout/cancellation contract

### E2.3 Worker Runtime

- [ ] T2.12 Implement queued TaskService
- [ ] T2.13 Implement local worker loop
- [ ] T2.14 Implement task claim/heartbeat
- [ ] T2.15 Persist log references
- [ ] T2.16 Recover orphaned tasks

---

## M3 Workflow Engine

- [ ] T3.1-T3.6 Workflow state machine
- [ ] T3.7-T3.11 Retry, compensation and resume
- [ ] T3.12-T3.15 Safety and approval
- [ ] T3.16-T3.20 Existing workflow template migration

---

## M4 Resource Plane and API

- [ ] T4.1-T4.6 Common resource API
- [ ] T4.7-T4.14 Core resource services and routes
- [ ] T4.15-T4.20 Action-to-workflow adapters
- [ ] T4.21-T4.24 Compatibility and OpenAPI contracts

---

## M5 Security, Audit and Events

- [ ] T5.1-T5.6 Identity context and minimum RBAC
- [ ] T5.7-T5.10 Persistent AuditEvent
- [ ] T5.11-T5.15 ResourceEvent and event stream

---

## M6 Plugin SDK

- [ ] T6.1-T6.5 Manifest, registry and lifecycle
- [ ] T6.6-T6.9 Plugin API and security
- [ ] T6.10-T6.12 Reference plugins

---

## M7 Web Console

- [ ] T7.1-T7.4 Console foundation
- [ ] T7.5-T7.10 Resource views
- [ ] T7.11-T7.15 Workflow, Task, Audit and live events

---

## M8 Release Validation

- [ ] T8.1-T8.9 Test completion
- [ ] T8.10-T8.15 Packaging and operations
- [ ] T8.16-T8.20 Release readiness

---

## Next Task

```text
T0.1 Add pytest baseline and test directory structure
```
