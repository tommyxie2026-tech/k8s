# P2-04 Migration Design v0.9

> Status: Design Review
> Version: v0.9
> Depends on:
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P2-02-ER-MODEL-v1.0
> - FROZEN-P2-03-TABLE-SCHEMA-AND-INDEX-DESIGN-v1.0
> Scope: CPP schema evolution, data migration, compatibility, rollback and SQLite-to-PostgreSQL transition

---

## 1. Purpose

This document defines how CPP evolves its persistent data safely across releases.

It covers:

```text
Schema migration
Data migration
Backward compatibility
Upgrade ordering
Rollback rules
Validation
SQLite to PostgreSQL transition
Disaster recovery for migration failure
```

---

## 2. Migration Principles

CPP freezes the following migration principles as candidates:

```text
1. All schema changes are versioned.
2. Manual production schema changes are forbidden.
3. Migration scripts must be repeatable in test and idempotent where practical.
4. Destructive migration requires explicit operator confirmation.
5. Application compatibility must be evaluated before schema activation.
6. Backup and validation are mandatory before high-risk migration.
7. Rollback must be designed before upgrade is released.
```

---

## 3. Migration Tooling

CPP V2.0 uses Alembic as the schema migration framework.

Suggested layout:

```text
platform-api/
  alembic.ini
  migrations/
    env.py
    script.py.mako
    versions/
      0001_initial_schema.py
      0002_add_resource_events.py
      0003_add_task_sequence.py
```

Rules:

```text
1. Every schema change must have an Alembic revision.
2. Revision identifiers are immutable after release.
3. Released migrations must never be edited in place.
4. Fixes require a new revision.
5. Migration code must support SQLite and PostgreSQL where the release claims both.
```

---

## 4. Schema Version Tracking

The authoritative schema version is Alembic's revision state.

CPP must also expose a read-only platform status view:

```yaml
database:
  engine: sqlite | postgresql
  current_revision: string
  expected_revision: string
  migration_required: boolean
  migration_state: idle | running | succeeded | failed
```

The API must refuse normal write operations if the database revision is incompatible with the running application.

---

## 5. Migration Categories

### 5.1 Additive Migration

Examples:

```text
Add nullable column
Add table
Add non-unique index
Add optional JSON field
```

Default risk: low.

### 5.2 Transformative Migration

Examples:

```text
Backfill shadow columns
Rename semantic field through copy-and-switch
Convert serialized payload format
Split one table into multiple tables
```

Default risk: medium.

### 5.3 Destructive Migration

Examples:

```text
Drop column
Drop table
Change incompatible type
Remove enum value
Delete or rewrite historical records
```

Default risk: high.

Destructive migrations require:

```text
Preflight
Backup
Explicit confirmation
Maintenance window
Post-migration validation
Documented recovery path
```

---

## 6. Expand / Migrate / Contract Pattern

Incompatible changes must use three phases.

### Phase A: Expand

```text
Add new columns/tables.
Keep old fields available.
Application writes both old and new formats where required.
```

### Phase B: Migrate

```text
Backfill existing data.
Validate record counts and semantic equality.
Switch reads to the new representation.
```

### Phase C: Contract

```text
Stop writing old representation.
Keep compatibility for at least one supported release boundary.
Drop old fields only in a later explicitly destructive migration.
```

Direct rename/drop in one release is forbidden for externally visible or critical fields.

---

## 7. Application and Database Compatibility

CPP uses a compatibility window.

Each application release declares:

```yaml
schema_compatibility:
  minimum_revision: string
  maximum_revision: string
  target_revision: string
```

Startup behavior:

```text
Current < minimum -> refuse startup except migration command
Current > maximum -> refuse startup
Current within range but below target -> start read-only or require migration according to release policy
Current == target -> normal operation
```

---

## 8. Upgrade Order

Recommended production upgrade sequence:

```text
1. Enter maintenance or write-restricted mode.
2. Verify application and database compatibility.
3. Run migration preflight.
4. Create database backup.
5. Run schema expansion migrations.
6. Run data transformation/backfill.
7. Validate migrated data.
8. Deploy new application version.
9. Run smoke tests.
10. Exit maintenance mode.
11. Run contract migrations only in a later release.
```

For strictly additive migrations, application deployment and migration ordering may use backward-compatible rolling upgrade rules.

---

## 9. Migration Preflight

Preflight must verify:

```text
Database connectivity
Current revision
Target revision
Free disk space
Backup destination
No previous failed migration lock
Required extensions/capabilities
Record counts for affected tables
Expected indexes and constraints
Application maintenance state
```

Preflight is read-only.

---

## 10. Migration Lock

Only one migration may run at a time.

SQLite:

```text
Use process/file lock plus migration state record.
```

PostgreSQL:

```text
Use PostgreSQL advisory lock plus migration state record.
```

A stale lock must not be automatically broken without operator review and explicit force confirmation.

---

## 11. Migration State Record

CPP should maintain a migration operation record separate from Alembic revision metadata.

```yaml
MigrationRun:
  id: UUIDv7
  from_revision: string
  to_revision: string
  application_version: string
  database_engine: string
  phase: pending | running | succeeded | failed | rolled_back
  started_at: datetime
  finished_at: datetime|null
  actor: string
  backup_location: string|null
  error_message: string|null
  validation_result: object|null
```

MigrationRun is retained for audit and diagnosis.

---

## 12. Backup Requirements

Before medium/high-risk migrations:

SQLite:

```text
Checkpoint WAL if enabled.
Create a consistent database copy or SQLite backup API snapshot.
Record checksum and file size.
```

PostgreSQL:

```text
Use logical dump for smaller installations or platform backup procedure for production.
Record backup identifier and recovery instructions.
```

Backup success must be verified before migration proceeds.

---

## 13. Data Validation

Validation must be both structural and semantic.

Structural checks:

```text
Target revision reached
Required tables exist
Required columns exist
Required indexes exist
Constraints valid
```

Semantic checks:

```text
Record counts preserved where expected
No unexpected null values
All resource IDs valid
spec/status JSON parse successfully
Shadow phase matches status.phase
Foreign references resolve where required
No duplicate active uniqueness keys
Workflow/Task history preserved
Audit/Event row counts preserved
```

Validation results must be persisted in MigrationRun.

---

## 14. Rollback Strategy

Rollback has two meanings.

### 14.1 Application Rollback

Application rollback is allowed only while the previous application version supports the current schema revision.

### 14.2 Database Rollback

Database downgrade migrations are allowed only for explicitly reversible changes.

For destructive or large transformative migrations, the supported recovery path is:

```text
Stop application
Restore verified backup
Deploy compatible application version
Validate recovery
```

A misleading automatic downgrade must not be provided when data loss is possible.

---

## 15. Failed Migration Handling

On migration failure:

```text
1. Stop subsequent revisions.
2. Mark MigrationRun failed.
3. Preserve logs and error details.
4. Keep application in maintenance/write-restricted mode.
5. Determine whether revision transaction rolled back cleanly.
6. Run read-only diagnosis.
7. Resume only through explicit retry or restore workflow.
```

The system must not silently mark a partially applied migration as successful.

---

## 16. Large Data Migration

Large backfills must use bounded batches.

Required controls:

```text
Batch size
Checkpoint cursor
Progress counters
Rate limit
Retry policy
Cancellation boundary
Validation per batch
```

Large migrations should be resumable and should avoid one long database transaction.

---

## 17. SQLite Migration Rules

SQLite-specific rules:

```text
1. Avoid relying on unsupported ALTER TABLE behavior.
2. Complex changes use create-copy-validate-swap pattern.
3. Foreign key enforcement must be explicitly enabled and validated.
4. WAL mode and checkpoint state must be considered before backup.
5. Repository-level uniqueness checks remain mandatory for active soft-deleted resources.
```

Create-copy-validate-swap:

```text
Create new table
Copy transformed rows
Validate counts and checksums
Replace old table transactionally where supported
Recreate indexes
Run final validation
```

---

## 18. PostgreSQL Migration Rules

PostgreSQL-specific rules:

```text
1. Use transactional DDL where supported.
2. Create large indexes concurrently where operationally required.
3. Avoid long table locks.
4. Use partial unique indexes for deleted_at IS NULL.
5. Validate JSONB conversion before removing legacy text representation.
6. Advisory lock protects migration exclusivity.
```

---

## 19. SQLite to PostgreSQL Transition

The transition is a controlled data migration, not a direct file conversion.

Recommended flow:

```text
1. Upgrade SQLite schema to the export-compatible revision.
2. Enter maintenance mode.
3. Create and verify SQLite backup.
4. Export resources through repository/export service.
5. Initialize PostgreSQL at the same logical schema revision.
6. Import in dependency order.
7. Validate counts, IDs, references and JSON payloads.
8. Switch database configuration.
9. Run API and workflow smoke tests.
10. Keep SQLite backup read-only for the defined rollback window.
```

Import dependency order:

```text
users
plugins
clusters
nodes
storage_pools
storage_classes
vms
workflows
tasks
backups
resource_events
audit_events
migration_runs
```

---

## 20. Engine-Neutral Data Rules

To preserve SQLite/PostgreSQL portability:

```text
Use UUID strings at service boundaries.
Use UTC timestamps.
Use repository abstractions.
Avoid database-specific SQL in services.
Treat booleans and JSON through ORM/repository types.
Do not depend on implicit row ordering.
Use explicit pagination order with id tie-breaker.
```

---

## 21. Migration Commands

Candidate operator commands:

```text
cpp db status
cpp db preflight
cpp db backup
cpp db upgrade
cpp db validate
cpp db history
cpp db restore-plan
cpp db export
cpp db import
```

Destructive or restore actions require explicit confirmation and must emit audit events.

---

## 22. CI Requirements

Every pull request changing schema or models must run:

```text
Alembic upgrade from empty database
Upgrade from previous supported release snapshot
Schema validation
Repository integration tests
SQLite tests
PostgreSQL tests when supported
Migration downgrade test for reversible revisions
Export/import round-trip test
```

Released migration fixtures must be retained for compatibility testing.

---

## 23. Observability

Migration execution must expose:

```text
Current revision
Target revision
Current migration step
Processed row count
Failed row count
Elapsed time
Migration phase
Validation result
```

Migration logs and audit records must include the MigrationRun ID.

---

## 24. Review Items

Before freezing P2-04, confirm:

```text
1. Alembic is the mandatory schema migration framework.
2. Expand/Migrate/Contract is required for incompatible changes.
3. MigrationRun is persisted independently for audit.
4. Preflight and verified backup are mandatory for medium/high-risk migrations.
5. Destructive rollback normally uses backup restore rather than unsafe downgrade.
6. SQLite-to-PostgreSQL uses repository-level export/import.
7. Large data migrations are resumable and batched.
8. Application refuses incompatible database revisions.
```

---

## 25. Deferred To Implementation

```text
Alembic env.py implementation
Concrete initial revision
CLI implementation
Backup adapter implementation
PostgreSQL connection configuration
Migration API endpoints
Release-specific compatibility matrix
```
