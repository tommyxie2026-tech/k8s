# FROZEN-P7 Engineering, CI and Packaging Specification v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P3-API-SPECIFICATION-v1.0
> - FROZEN-P4-WORKFLOW-ENGINE-v1.0
> Scope: CPP V2.0 engineering structure, repository standards, CI, packaging, release and compatibility rules
> Rule: Any incompatible change to repository layout, build pipeline, packaging target or release compatibility policy must create a new design version and pass review again.

---

## 1. Purpose

This specification freezes CPP V2.0 engineering and delivery rules.

The goal is to turn CPP from scripts and playbooks into a maintainable product engineering system.

---

## 2. Engineering Principles

CPP freezes the following engineering principles:

```text
Design before code
API first
Testable by default
Safe by default
Backward compatible
Automation-first delivery
```

---

## 3. Repository Layout

Recommended repository layout:

```text
platform-api/
  app/
  tests/
  migrations/
platform-web/
  src/
  tests/
roles/
playbooks/
inventories/
docs/
  frozen/
  P0-product/
  P1-domain/
  P2-database/
  P3-api/
  P4-workflow/
  P5-plugin/
  P6-ui/
  P7-engineering/
  P8-validation/
scripts/
tools/
```

V2.0 may keep existing playbook layout, but new platform code must follow clear module boundaries.

---

## 4. Module Boundaries

Frozen module boundaries:

```text
routers -> services -> repositories -> database
workflow -> runtime -> executor
plugins -> public API or extension interface
observability -> event/audit/log streams
```

Forbidden:

```text
Router -> SQL
Router -> ansible-playbook
Workflow -> SQL
Plugin -> SQL
Executor -> Resource mutation
```

---

## 5. Build Targets

V2.0 build targets:

```text
platform-api Python package
platform-api container image
Ansible playbook collection
Documentation bundle
Optional platform-web static bundle
```

---

## 6. CI Pipeline

Minimum CI stages:

```text
lint
unit-test
api-schema-check
migration-check
playbook-syntax-check
docs-link-check
security-baseline-check
container-build-check
```

CI must fail on:

```text
broken imports
invalid OpenAPI schema
Alembic migration mismatch
Ansible syntax failure
unsafe default destructive operations
```

---

## 7. Testing Layers

Required testing layers:

```text
Unit tests
Repository tests
Service tests
Workflow tests
API tests
Playbook syntax tests
Integration smoke tests
```

Destructive tests must be opt-in.

---

## 8. Packaging

V2.0 packaging options:

```text
Docker image for platform-api
Python wheel or source package for platform-api
Ansible collection/archive
Helm chart or deployment manifests for control plane
```

RPM/DEB packaging is deferred unless required by enterprise deployment.

---

## 9. Configuration Management

Configuration must be explicit.

Recommended config sources:

```text
environment variables
config file
Kubernetes Secret/ConfigMap when deployed in cluster
```

Secrets must not be committed to repository.

---

## 10. Release Versioning

CPP follows semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Rules:

```text
MAJOR: incompatible API or data model changes
MINOR: backward-compatible features
PATCH: bug fixes and documentation corrections
```

---

## 11. Compatibility Policy

V2.0 must maintain compatibility across:

```text
Frozen Resource Model
API v1 baseline
Workflow template names
Repository interfaces
Migration chain
```

Breaking change requires new design review.

---

## 12. Documentation Policy

Frozen design documents are source of truth.

Implementation must not contradict:

```text
docs/frozen/*.md
```

Any implementation conflict must be resolved by:

```text
1. Update design through review
2. Freeze new version
3. Then modify implementation
```

---

## 13. Security Baseline

Minimum security engineering rules:

```text
No secrets in logs
No secrets in repository
Destructive operations require confirmation
Audit security-relevant actions
Least privilege for plugins and executors
```

---

## 14. Observability Baseline

Platform services must expose:

```text
health endpoint
version endpoint
workflow status
task status
structured logs
audit events
```

Metrics endpoint is recommended for V2.0 and required for V2.1.

---

## 15. Release Artifacts

Each release should include:

```text
source tag
container image
migration revision
OpenAPI specification
frozen design version list
changelog
upgrade notes
```

---

## 16. Deferred

The following are deferred:

```text
Enterprise installer
Air-gapped installation bundle
RPM/DEB official packaging
Multi-arch image matrix
Signed plugin registry
Commercial license enforcement
```

---

## 17. Frozen Decisions

```text
1. Design docs are source of truth.
2. CI must validate API, migrations, playbooks and docs.
3. Platform code must follow router/service/repository boundaries.
4. Workflow/runtime/executor boundaries are mandatory.
5. Semantic versioning is required.
6. Destructive tests and operations must be opt-in.
7. Release artifacts must include design version and migration revision.
```
