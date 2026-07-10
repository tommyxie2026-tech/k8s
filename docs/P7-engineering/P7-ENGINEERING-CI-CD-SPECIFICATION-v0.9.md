# P7 Engineering and CI/CD Specification v0.9

> Status: Design Review
> Depends on P0-P6 design documents

## 1. Purpose

Defines repository structure, coding boundaries, build, test, packaging, release, compatibility and operational engineering standards.

## 2. Repository Structure

```text
platform-api/
  app/
    api/
    domain/
    services/
    repositories/
    workflows/
    runtime/
    executors/
    plugins/
    observability/
  migrations/
  tests/
web-console/
plugin-sdk/
plugins/
playbooks/
roles/
docs/
```

Legacy paths may remain temporarily but must migrate toward these boundaries.

## 3. Dependency Rules

```text
API -> Services
Services -> Domain + Repositories + Workflow client
Workflow -> Runtime interface
Runtime -> Executor interface
Repository -> Database
Plugin -> Public contracts
```

Forbidden imports are checked in CI. Routers must not import executors, subprocess, SQLAlchemy sessions or Ansible internals.

## 4. Development Workflow

```text
Design/ADR
Issue
Feature branch
Tests
Pull request
Review
CI
Merge
Release note
```

Frozen design changes require a design version update before implementation.

## 5. Quality Gates

Required checks:

```text
format
lint
static type check
unit tests
API contract tests
database migration tests
workflow conformance tests
plugin conformance tests
Ansible syntax checks
security scan
container build
```

No release artifact is produced when a required gate fails.

## 6. Python Baseline

Recommended:

```text
Python 3.12+
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
pytest
mypy or pyright
ruff
```

Exact versions are pinned through lock files and updated through controlled dependency PRs.

## 7. Testing Layers

```text
Unit
Repository integration
API contract
Workflow integration
Executor adapter
Plugin conformance
End-to-end
Upgrade/migration
Disaster recovery
```

External infrastructure is replaced with fakes only in unit tests; integration tests must run against representative Kubernetes/KubeVirt/CSI environments.

## 8. Packaging

Deliverables:

```text
OCI image: platform-api
OCI image: worker
OCI image: web-console
Python package: plugin-sdk
Helm chart or deployment manifests
Ansible collection/playbooks
SBOM
Checksums/signatures
```

## 9. Configuration

Configuration is environment-driven and validated at startup. Secrets are referenced from Kubernetes Secrets or external secret systems, never committed to source.

## 10. Release Strategy

Semantic versioning:

```text
MAJOR: incompatible API or persisted model change
MINOR: backward-compatible capability
PATCH: backward-compatible fix
```

Release channels: development, preview, stable, LTS. Database migrations and compatibility notes are mandatory.

## 11. Branch and Compatibility Policy

`master` remains releasable. Breaking work uses versioned feature branches or feature flags. API v1 and plugin SDK v1 compatibility are maintained through the V2 product lifecycle.

## 12. Supply Chain Security

Required:

```text
Dependency scanning
Secret scanning
SAST
Container vulnerability scanning
SBOM
Image signing
Provenance metadata
Least-privilege CI credentials
```

## 13. Observability Baseline

Each service emits structured logs, metrics, traces/request IDs and health/readiness endpoints. Logs must not contain secrets.

## 14. Definition of Done

A feature is done only when:

```text
Design references are identified
Code boundaries are respected
Tests pass
API/docs are updated
Audit/observability are implemented
Upgrade impact is documented
Rollback path exists
```

## 15. Review Items

1. Accept the proposed module boundaries and dependency checks.
2. Accept mandatory migration, contract and conformance tests.
3. Accept signed OCI artifacts, SBOM and supply-chain controls.
4. Accept semantic versioning and stable/LTS channels.
5. Accept Definition of Done as a release gate.
