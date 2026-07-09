# P2-04 Migration Strategy v0.9

> Status: Design Review
> Version: v0.9
> Depends on:
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - P2-03-TABLE-SCHEMA-AND-INDEX-DESIGN-v0.9
> Scope: schema migration, compatibility, upgrade and rollback strategy

---

## 1. Purpose

This document defines the migration strategy for CPP persistence.

CPP must support:

```text
SQLite first
PostgreSQL later
schema versioning
safe upgrades
controlled rollback
```

---

## 2. Migration Tooling

CPP V2.0 should use Alembic for schema migration.

Rules:

```text
1. Manual schema changes are forbidden.
2. Every schema change must have a migration revision.
3. Migration revisions must be committed to the repository.
4. Migrations must run in CI against SQLite.
5. PostgreSQL compatibility tests are required before PostgreSQL GA.
```

---

## 3. Versioning Model

CPP maintains three version concepts:

```text
Product version
API version
Database schema version
```

They are related but not identical.

Example:

```text
CPP v2.0.0
API /api/v1
DB schema revision 20260710_001
```

---

## 4. Schema Migration Principles

Allowed normal changes:

```text
Add nullable column
Add table
Add non-unique index
Add enum-like value at application layer
Add JSON field inside spec/status
```

Restricted changes:

```text
Rename table
Rename column
Drop column
Change column type
Change ID format
Change resource lifecycle semantics
```

Restricted changes require design review and compatibility plan.

---

## 5. Backward Compatibility

Database migration must preserve old records where possible.

Rules:

```text
1. Old resource IDs must remain stable.
2. Existing workflows and tasks must remain queryable after upgrade.
3. Existing audit events must not be rewritten.
4. Spec/status JSON must support unknown fields for forward compatibility.
5. API may ignore unknown fields but must not delete them unintentionally.
```

---

## 6. SQLite to PostgreSQL Path

Migration path:

```text
V2.0 SQLite
  -> V2.x dual-compatible schema discipline
  -> PostgreSQL compatibility CI
  -> export/import tool
  -> PostgreSQL production mode
```

Rules:

```text
1. Avoid SQLite-only SQL features in repository logic.
2. Keep JSON usage compatible with future JSONB.
3. Keep timestamps as UTC RFC3339 strings at API boundary.
4. Repository layer owns DB dialect adaptation.
```

---

## 7. Migration Execution Flow

Upgrade flow:

```text
1. Stop API writes or enter maintenance mode.
2. Backup database.
3. Run Alembic migration.
4. Run schema verification.
5. Run data integrity checks.
6. Start API/worker.
7. Run smoke test.
```

---

## 8. Rollback Strategy

Rollback is limited.

Preferred model:

```text
backup before migration
restore backup on failure
```

Rules:

```text
1. Destructive migrations must be avoided.
2. Down migrations are useful in dev/test but not guaranteed for production data-loss scenarios.
3. Production rollback must rely on database backup and restore.
4. Migration must fail fast before modifying data when preconditions are not met.
```

---

## 9. Data Integrity Checks

Required checks after migration:

```text
1. All resource tables have valid id/kind/name/spec/status.
2. All active records have deleted_at=null.
3. Workflow-task references are valid where workflow_id is not null.
4. Cluster-scoped resources reference existing clusters.
5. Audit events remain readable.
6. resource_version is present on every resource.
```

---

## 10. Seed Data

Initial seed data may include:

```text
local admin user if local auth is enabled
builtin plugins metadata
default system cluster placeholder only when configured
```

Rules:

```text
1. Seed data must be idempotent.
2. Seed data must not overwrite user-modified resources.
3. Seed data must be version-controlled.
```

---

## 11. Migration Testing

Required tests:

```text
fresh database upgrade to head
upgrade from previous release
migration idempotency where applicable
schema downgrade in dev mode where safe
repository CRUD after migration
workflow/task read after migration
```

---

## 12. Review Items

Before freezing P2-04, confirm:

```text
1. Alembic is accepted as migration tool.
2. SQLite is V2.0 primary DB and PostgreSQL is future production target.
3. Manual schema changes are forbidden.
4. Production rollback uses backup/restore rather than relying on down migrations.
5. Migration tests are required in CI.
```
