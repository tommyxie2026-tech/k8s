# FROZEN-P3 API Specification v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P2-03-TABLE-SCHEMA-v1.0
> Scope: CPP V2.0 REST API conventions, resource API baseline, workflow API baseline and safety rules
> Rule: Any incompatible change to API naming, resource structure, destructive-operation semantics or workflow submission model must create a new API version or pass design review.

---

## 1. Purpose

This frozen specification defines CPP V2.0 API design rules.

The API must expose the frozen Resource Model, not implementation details.

---

## 2. API Principles

CPP API freezes the following principles:

```text
API First
Resource Model Driven
Workflow Native
Safe by Default
Backward Compatible
```

API Plane must not directly execute infrastructure commands.

Forbidden:

```text
API -> ansible-playbook
API -> kubectl
API -> virtctl
API -> shell
```

Allowed:

```text
API -> Resource Service
API -> Workflow Service
```

---

## 3. API Versioning

V2.0 base path:

```text
/api/v1
```

Rules:

```text
1. Breaking changes require a new API version.
2. Non-breaking fields may be added.
3. Removed fields must be deprecated first.
4. API response shape must remain stable within v1.
```

---

## 4. Resource Response Shape

All resource APIs return the same logical structure:

```yaml
resource:
  metadata:
    id: string
    kind: string
    name: string
    labels: object
    annotations: object
    generation: integer
    resource_version: string
    created_at: string
    updated_at: string
    deleted_at: string|null
  spec: object
  status: object
```

List responses:

```yaml
items: list[resource]
page:
  limit: integer
  cursor: string|null
  next_cursor: string|null
```

---

## 5. Error Response Shape

All errors must use a common shape:

```yaml
error:
  code: string
  message: string
  details: object|null
  request_id: string
```

Examples:

```text
RESOURCE_NOT_FOUND
VALIDATION_FAILED
CONFLICT
FORBIDDEN
DESTRUCTIVE_CONFIRMATION_REQUIRED
WORKFLOW_REJECTED
```

---

## 6. Common Query Parameters

Resource list APIs should support:

```text
limit
cursor
label_selector
field_selector
include_deleted
sort
```

`include_deleted` must default to false.

---

## 7. Core Resource APIs

Frozen baseline endpoints:

```text
GET    /api/v1/clusters
POST   /api/v1/clusters
GET    /api/v1/clusters/{id}
PATCH  /api/v1/clusters/{id}
DELETE /api/v1/clusters/{id}

GET    /api/v1/nodes
GET    /api/v1/nodes/{id}
PATCH  /api/v1/nodes/{id}

GET    /api/v1/storage-pools
POST   /api/v1/storage-pools
GET    /api/v1/storage-pools/{id}
PATCH  /api/v1/storage-pools/{id}
DELETE /api/v1/storage-pools/{id}

GET    /api/v1/storage-classes
POST   /api/v1/storage-classes
GET    /api/v1/storage-classes/{id}
PATCH  /api/v1/storage-classes/{id}
DELETE /api/v1/storage-classes/{id}

GET    /api/v1/vms
POST   /api/v1/vms
GET    /api/v1/vms/{id}
PATCH  /api/v1/vms/{id}
DELETE /api/v1/vms/{id}

GET    /api/v1/backups
GET    /api/v1/backups/{id}
DELETE /api/v1/backups/{id}

GET    /api/v1/plugins
GET    /api/v1/plugins/{id}
PATCH  /api/v1/plugins/{id}

GET    /api/v1/users
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}
```

---

## 8. Workflow APIs

All infrastructure-changing operations must be submitted as workflows.

Frozen endpoints:

```text
GET  /api/v1/workflows
POST /api/v1/workflows
GET  /api/v1/workflows/{id}
POST /api/v1/workflows/{id}/cancel
POST /api/v1/workflows/{id}/retry
```

Workflow creation request:

```yaml
name: string
target_kind: string|null
target_id: string|null
params: object
confirm: boolean
confirm_phrase: string|null
```

Workflow creation response:

```yaml
workflow_id: string
status: pending|queued|running|succeeded|failed|cancelled
```

---

## 9. Task APIs

Task APIs are read-first.

Frozen endpoints:

```text
GET /api/v1/tasks
GET /api/v1/tasks/{id}
GET /api/v1/tasks/{id}/logs
```

Direct task creation is allowed only for legacy execution compatibility and must be explicitly marked as legacy.

---

## 10. Action APIs

Action APIs may exist for usability, but they must create workflows internally.

Examples:

```text
POST /api/v1/vms/{id}/start
POST /api/v1/vms/{id}/stop
POST /api/v1/vms/{id}/restart
POST /api/v1/vms/{id}/backup
POST /api/v1/vms/{id}/restore
```

These endpoints must not directly call executors.

They must translate to:

```text
Action API -> Workflow Create -> Runtime -> Executor
```

---

## 11. Destructive Operation Rules

Destructive operations must require explicit confirmation.

Examples:

```text
cluster delete
vm restore
backup delete
storage pool delete
node drain
```

Required request fields:

```yaml
confirm: true
confirm_phrase: string
```

If missing:

```text
DESTRUCTIVE_CONFIRMATION_REQUIRED
```

---

## 12. Concurrency Rules

PATCH/DELETE should support resource_version checks.

Clients should send:

```text
If-Match: <resource_version>
```

or body field:

```yaml
resource_version: string
```

On mismatch:

```text
409 CONFLICT
```

---

## 13. Events and Audit APIs

Frozen endpoints:

```text
GET /api/v1/resource-events
GET /api/v1/audit-events
```

Filters:

```text
resource_kind
resource_id
actor_id
action
created_after
created_before
```

Audit APIs are read-only in normal operation.

---

## 14. Health and Readiness APIs

Frozen endpoints:

```text
GET /health
GET /ready
GET /api/v1/system/info
```

`/health` checks process liveness.

`/ready` checks database and runtime readiness.

---

## 15. WebSocket APIs

Future-compatible baseline:

```text
/ws/v1/events
/ws/v1/workflows/{id}
/ws/v1/tasks/{id}/logs
```

WebSocket streams consume Event and Task log sources. They must not become a separate source of truth.

---

## 16. Authentication and Authorization

V2.0 may support local development authentication.

Enterprise identity is deferred to the RBAC/Identity specification.

API design must remain compatible with:

```text
OIDC
LDAP
API Token
Service Account
```

---

## 17. Frozen Decisions

```text
1. /api/v1 is the V2.0 base path.
2. All resources expose metadata/spec/status.
3. Action APIs must create workflows internally.
4. API must not directly call executors.
5. Destructive operations require confirm and confirm_phrase.
6. Resource updates must support optimistic concurrency.
7. Audit APIs are read-only.
8. WebSocket is event/log streaming, not state storage.
```

---

## 18. Next Document

```text
FROZEN-P4-WORKFLOW-ENGINE-v1.0
```
