# FROZEN-P8 Validation and Acceptance Specification v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P3-API-SPECIFICATION-v1.0
> - FROZEN-P4-WORKFLOW-ENGINE-v1.0
> - FROZEN-P5-PLUGIN-SDK-v1.0
> - FROZEN-P6-WEB-CONSOLE-v1.0
> - FROZEN-P7-ENGINEERING-v1.0
> Scope: CPP V2.0 validation strategy, acceptance criteria, test layers and release gates
> Rule: Any incompatible change to release gates, validation layers or acceptance baseline must create a new design version and pass review again.

---

## 1. Purpose

This specification freezes the CPP V2.0 validation and acceptance baseline.

A feature is not complete when it is coded. A feature is complete when it passes design, implementation, testing, safety and documentation gates.

---

## 2. Validation Principle

CPP freezes the following principle:

```text
Every product capability must be validated at design, API, workflow, persistence and operational levels.
```

Validation must prove:

```text
Correctness
Safety
Recoverability
Auditability
Compatibility
```

---

## 3. Test Layers

Required test layers:

```text
Design consistency checks
Unit tests
Repository tests
Service tests
API tests
Workflow tests
Executor tests
Playbook syntax tests
Integration smoke tests
Security baseline tests
Documentation checks
```

---

## 4. Design Consistency Checks

Implementation must be checked against frozen design documents.

Examples:

```text
Resource names match P1
metadata/spec/status match P2
API paths match P3
Workflow lifecycle matches P4
Plugin boundaries match P5
UI resource views match P6
CI pipeline matches P7
```

---

## 5. API Acceptance

API acceptance criteria:

```text
1. OpenAPI schema is generated successfully.
2. API uses /api/v1 base path.
3. Resource endpoints expose metadata/spec/status where applicable.
4. Destructive operations require workflow submission and confirmation.
5. API does not directly invoke executor commands.
6. Error responses are structured and stable.
```

---

## 6. Persistence Acceptance

Persistence acceptance criteria:

```text
1. All database access goes through repositories.
2. Migrations are versioned.
3. SQLite runs by default.
4. Schema design does not block PostgreSQL migration.
5. generation/resource_version are supported.
6. deleted_at soft deletion is supported.
```

---

## 7. Workflow Acceptance

Workflow acceptance criteria:

```text
1. Workflow and Task are durable resources.
2. Workflow lifecycle transitions are persisted.
3. Task lifecycle transitions are persisted.
4. Failed tasks fail workflow unless retry/compensation applies.
5. Destructive workflows require explicit confirmation.
6. Workflow and Task events are emitted.
7. Logs are linked from Task status.
```

---

## 8. Plugin Acceptance

Plugin acceptance criteria:

```text
1. Plugin is a Resource.
2. Plugin declares category and capabilities.
3. Plugin cannot access database directly.
4. Plugin lifecycle is auditable.
5. Plugin operations use Resource/Workflow APIs or stable extension interfaces.
```

---

## 9. Web Console Acceptance

Web Console acceptance criteria:

```text
1. Primary navigation follows Resource Model.
2. Resource detail pages show Spec, Status, Events, Workflows and Audit.
3. Workflow is visible as a first-class object.
4. Destructive actions require confirmation UX.
5. Task logs and workflow progress are visible.
```

---

## 10. Safety Acceptance

Safety gates:

```text
1. Destructive operations are opt-in.
2. Dangerous playbooks default to disabled or dry-run.
3. Confirmation phrase is required where specified.
4. Secrets are not logged.
5. Audit records are created for destructive confirmations.
```

---

## 11. Operational Acceptance

Operational gates:

```text
1. Health endpoint works.
2. Version endpoint or version metadata exists.
3. Workflow status survives process restart.
4. Task logs are retained or referenced.
5. Failed workflows provide diagnosis reason.
6. Backup and restore preflight paths are testable without destructive action.
```

---

## 12. CI Release Gates

A release must pass:

```text
lint
unit-test
api-schema-check
migration-check
playbook-syntax-check
docs-check
security-baseline-check
container-build-check
```

Release must fail when:

```text
OpenAPI schema is invalid
Alembic migration chain is broken
Ansible syntax check fails
destructive operation lacks confirmation
repository boundary is bypassed
frozen design contradiction is detected
```

---

## 13. Minimum V2.0 Acceptance Scenarios

V2.0 must validate these scenarios:

```text
Cluster preflight
Storage governance
Volume snapshot check
Velero preflight
etcd backup dry/safe execution
VM backup plan
VM restore preflight / confirmed workflow
Workflow listing and detail
Task log visibility
Audit event creation
Plugin capability listing
```

---

## 14. Non-Goals

The following are not required for V2.0 acceptance:

```text
Full multi-tenant enterprise RBAC
Plugin marketplace
Visual workflow designer
Billing
Air-gapped installer
Full HA PostgreSQL deployment
```

---

## 15. Definition of Done

A V2.0 capability is done only when:

```text
1. It conforms to frozen design docs.
2. It has API or Workflow entrypoint.
3. It has tests.
4. It has safety behavior for destructive operations.
5. It emits events/audit where applicable.
6. It is documented.
7. It passes CI gates.
```

---

## 16. Frozen Decisions

```text
1. Validation must cover design, API, persistence, workflow, plugin, UI and operations.
2. CI release gates are mandatory.
3. Destructive operation safety is a release blocker.
4. Repository boundary violations are release blockers.
5. Frozen design contradiction is a release blocker.
6. V2.0 acceptance scenarios are explicitly defined.
```
