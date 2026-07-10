# CPP Implementation Gap Analysis v1.0

> Status: ACTIVE
> Baseline: FROZEN-P0-01 through FROZEN-P8
> Scope: Current repository versus frozen CPP V2.0 design

## 1. Executive Summary

The repository contains strong automation assets and an initial FastAPI/workflow prototype, but it is not yet aligned with the frozen CPP product architecture.

The most important structural gaps are:

1. Two incompatible executor systems.
2. API routers can bypass Workflow and Runtime.
3. Workflow and job state use JSON files or process memory instead of repositories and database persistence.
4. Task and Job are competing concepts.
5. Resource APIs do not yet expose the frozen metadata/spec/status contract.
6. No SQLAlchemy/Alembic persistence layer exists.
7. Workflow execution is synchronous and blocks API requests.
8. Audit is file-based and not append-only through a repository abstraction.
9. Plugin SDK and Web Console are design-only.
10. Test, CI, packaging and acceptance gates are incomplete.

## 2. Current Strengths

- Existing Ansible playbooks cover cluster, governance, KubeVirt, storage and backup operations.
- FastAPI application and initial routers exist.
- Workflow templates and destructive confirmation exist.
- Workflow JSON persistence and audit logging provide a usable prototype.
- Frozen P0-P8 design baseline is complete.

## 3. Gap Matrix

| ID | Frozen requirement | Current state | Gap | Priority |
|---|---|---|---|---|
| GAP-001 | One Runtime/Executor boundary | `core.executor` and `services.executor` coexist | Duplicate lifecycle and storage models | P0 |
| GAP-002 | Workflow is mandatory for complex operations | Routers submit playbooks directly | API bypasses Workflow Plane | P0 |
| GAP-003 | Task is the execution resource | Both TaskInfo and JobRecord exist | Competing execution concepts | P0 |
| GAP-004 | Repository Pattern | JSON files and module dictionaries | No durable repository abstraction | P0 |
| GAP-005 | SQLite + Alembic | No ORM/migrations | Frozen P2 not implemented | P0 |
| GAP-006 | metadata/spec/status resource model | Router-specific response models | No universal Resource contract | P1 |
| GAP-007 | Async workflow/runtime | `subprocess.run` in request path | API blocking and no worker recovery | P0 |
| GAP-008 | Append-only audit repository | JSONL file helper | No queryable durable audit model | P1 |
| GAP-009 | Optimistic concurrency | No generation/resource_version enforcement | Concurrent updates unsafe | P1 |
| GAP-010 | UUIDv7-compatible IDs | UUIDv4 and timestamp IDs | ID strategy inconsistent | P1 |
| GAP-011 | Event propagation | Direct audit calls only | No ResourceEvent abstraction | P1 |
| GAP-012 | Executor abstraction | Ansible-specific classes | No executor protocol/registry | P1 |
| GAP-013 | Resource services/repositories | Mostly hard-coded router data | Domain layer incomplete | P1 |
| GAP-014 | Plugin SDK | Design only | No manifest, registry or lifecycle | P2 |
| GAP-015 | Web Console | Design only | No frontend implementation | P2 |
| GAP-016 | CI/release gates | Partial syntax checks | No API/unit/migration/security gates | P1 |
| GAP-017 | Compatibility migration | Existing endpoints differ from frozen API | Migration/deprecation plan required | P0 |
| GAP-018 | Secrets and credentials boundary | Executor inherits process environment | Secret handling not formalized | P1 |

## 4. P0 Architectural Blockers

### 4.1 Dual Executor

Current systems:

- `app.core.executor.PlaybookExecutor`: asynchronous `Popen`, TaskInfo/task_store.
- `app.services.executor.Executor`: synchronous `subprocess.run`, JobRecord/module dictionary.

Target:

```text
Workflow Service
  -> Runtime Service
    -> Task Repository
      -> Executor Registry
        -> AnsibleExecutor
```

One Task lifecycle must replace both TaskInfo and JobRecord.

### 4.2 Persistence

Current:

```text
Workflow -> JSON files
Job -> in-memory dictionary
Task -> current task_store implementation
Audit -> JSONL file
```

Target:

```text
Service -> Repository -> SQLite
                         -> PostgreSQL later
```

### 4.3 API Bypass

Current routers may call executor directly.

Target rules:

- Read-only resource endpoints call Resource Services.
- Simple legacy execution creates a standalone Task through Runtime Service.
- Complex or destructive execution creates a Workflow.
- No router imports an executor implementation.

### 4.4 Blocking Workflow

Current workflow calls synchronous playbooks in the API process.

Target:

- POST creates a queued Workflow and returns immediately.
- Worker claims pending Tasks.
- Worker records terminal Task state.
- Workflow reconciler advances or fails the Workflow.

## 5. Migration Constraints

1. Preserve existing playbooks and inventory variables.
2. Keep existing API endpoints temporarily as compatibility adapters.
3. Do not remove old executor modules until callers migrate.
4. Introduce repositories before replacing file persistence.
5. Migrate stored JSON workflow records where practical or document prototype incompatibility.
6. Every destructive route must retain explicit confirmation.

## 6. Definition of Architecture Alignment

The platform is architecture-aligned when:

- One Task model exists.
- One Runtime Service owns execution.
- Routers do not import executor implementations.
- Workflow state, Task state, AuditEvent and ResourceEvent are durable.
- SQLite schema is created by migrations.
- Workflow submission is asynchronous.
- Resource responses follow metadata/spec/status.
- CI validates migrations, APIs, workflows and safety rules.
