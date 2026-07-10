# P8 Test, Validation and Acceptance Specification v0.9

> Status: Design Review
> Depends on P0-P7 design documents

## 1. Purpose

Defines how CPP V2.0 is verified before release, including functional correctness, safety, compatibility, resilience, performance, security, upgrade and disaster recovery acceptance.

## 2. Test Pyramid

```text
Unit Tests
Repository Integration Tests
API Contract Tests
Workflow Integration Tests
Executor Adapter Tests
Plugin Conformance Tests
End-to-End Tests
Upgrade and Disaster Recovery Tests
```

## 3. Functional Acceptance Domains

Required domains:

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
User/Audit
```

Each domain must support create/read/update/delete semantics where applicable, lifecycle transitions, validation, concurrency conflict handling, audit and event generation.

## 4. Architecture Conformance

Tests must prove:

```text
Routers do not call executors directly.
Plugins do not access the database directly.
Workflow Engine does not execute infrastructure commands.
Runtime does not own resource desired state.
All core resources follow metadata/spec/status.
```

Architecture violations fail CI.

## 5. API Contract Acceptance

Verify:

```text
OpenAPI generation
Standard resource envelope
Standard error envelope
HTTP 202 for async actions
Idempotency-Key behavior
If-Match/resource_version conflicts
Cursor pagination
Backward-compatible additive fields
```

## 6. Database Acceptance

Verify on SQLite and PostgreSQL:

```text
Fresh installation
All Alembic upgrades
Upgrade from supported previous version
Unique constraints
Foreign key behavior
Soft deletion
Optimistic concurrency
Append-only audit/event repositories
Backup and restore of control-plane data
```

## 7. Workflow Acceptance

For each core template verify:

```text
Success path
Validation failure
Executor failure
Timeout
Retry classification
Cancellation
Engine restart and lease recovery
Audit events
Compensation behavior where defined
```

Core templates include cluster validation, governance scan, etcd backup/preflight, VM backup/restore and storage health/snapshot checks.

## 8. Executor Acceptance

Each executor adapter must pass:

```text
Command construction
Input validation
Timeout
Cancellation
Output capture
Secret redaction
Exit/error classification
Idempotency expectations
Health check
```

## 9. Plugin Conformance

Every plugin must pass manifest, version negotiation, capability discovery, authorization scope, timeout, failure isolation, upgrade and rollback tests.

Reference conformance requires at least three storage plugins.

## 10. Security Acceptance

Required:

```text
Authentication tests
Authorization denial tests
Destructive confirmation tests
Secret redaction
Injection resistance
Path traversal protection
SSRF boundary for plugins
Dependency and container scans
Audit completeness
```

## 11. Resilience Acceptance

Simulate:

```text
Platform API restart
Workflow Engine restart
Worker crash during Task
Database temporary outage
Plugin timeout/failure
Kubernetes API outage
Executor process failure
Event stream reconnect
```

Durable resource/workflow state must recover without silent success or duplication.

## 12. Performance Baseline

Initial V2.0 targets for one management instance:

```text
10,000 persisted resources
1,000,000 audit/event records
100 concurrent active workflows
20 concurrent executor tasks by default
P95 resource read API under 500 ms in reference environment
P95 workflow creation under 1 s excluding execution
```

Targets are reference baselines and must be measured with documented hardware and dataset.

## 13. Upgrade Acceptance

A release is blocked unless:

```text
Database migration succeeds from every supported version.
API compatibility suite passes.
Plugin SDK compatibility suite passes.
Rollback or forward-recovery procedure is documented.
Backup is verified before destructive migration.
```

## 14. Disaster Recovery Acceptance

Verify:

```text
Control database backup and restore
Audit retention/recovery
Workflow recovery after restart
etcd backup preflight
VM backup and restore plan
Object storage unavailability behavior
```

Destructive restore execution requires a dedicated controlled test environment.

## 15. Release Gates

A V2.0 release requires:

```text
All mandatory CI checks green
No unresolved critical security findings
No open P0/P1 severity defects
Migration and upgrade tests green
Core E2E scenarios green
Architecture conformance green
SBOM and signed artifacts available
Release notes and runbooks complete
```

## 16. Acceptance Matrix

Each requirement must map to:

```text
Design document
Implementation issue/PR
Automated test
Result artifact
Release version
```

No requirement may be marked complete without evidence.

## 17. Review Items

1. Accept architecture conformance as a CI release gate.
2. Accept dual-database testing for SQLite and PostgreSQL.
3. Accept the initial performance baseline.
4. Accept mandatory restart/recovery and upgrade tests.
5. Accept evidence-based requirement traceability.
