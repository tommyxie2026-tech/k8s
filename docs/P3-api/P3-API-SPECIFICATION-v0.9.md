# P3 API Specification v0.9

> Status: Design Review
> Depends on FROZEN-P0-02, FROZEN-P1-01, FROZEN-P2-01, FROZEN-P2-02 and P2-03

## 1. API Principles

```text
API First
Resource-oriented
Versioned under /api/v1
Asynchronous for infrastructure mutation
Safe by default
Idempotent where possible
Optimistic concurrency through resource_version
```

API routers must not call executors or infrastructure tools directly.

## 2. Standard Resource Envelope

```json
{
  "api_version": "cpp.io/v1",
  "kind": "VM",
  "metadata": {
    "id": "uuidv7",
    "name": "vm01",
    "labels": {},
    "annotations": {},
    "generation": 1,
    "resource_version": "...",
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null
  },
  "spec": {},
  "status": {"phase": "running"}
}
```

## 3. Collection Conventions

```text
GET    /api/v1/{resources}
POST   /api/v1/{resources}
GET    /api/v1/{resources}/{id}
PATCH  /api/v1/{resources}/{id}
DELETE /api/v1/{resources}/{id}
```

Collections support:

```text
limit
cursor
sort
label_selector
field_selector
include_deleted
```

Offset pagination is not used for large collections. Cursor pagination is based on `(created_at,id)`.

## 4. Core Resource Paths

```text
/api/v1/clusters
/api/v1/nodes
/api/v1/storage-pools
/api/v1/storage-classes
/api/v1/vms
/api/v1/backups
/api/v1/workflows
/api/v1/tasks
/api/v1/plugins
/api/v1/users
/api/v1/audit-events
/api/v1/resource-events
```

## 5. Action Endpoints

Complex mutations create Workflows:

```text
POST /api/v1/vms/{id}/actions/start
POST /api/v1/vms/{id}/actions/stop
POST /api/v1/vms/{id}/actions/migrate
POST /api/v1/vms/{id}/actions/backup
POST /api/v1/backups/{id}/actions/restore
POST /api/v1/clusters/{id}/actions/validate
POST /api/v1/storage-pools/{id}/actions/health-check
```

Successful action response:

```json
{
  "workflow_id": "...",
  "status": "pending",
  "location": "/api/v1/workflows/..."
}
```

HTTP 202 is used for accepted asynchronous actions.

## 6. Workflow API

```text
POST /api/v1/workflows
GET  /api/v1/workflows
GET  /api/v1/workflows/{id}
POST /api/v1/workflows/{id}/actions/cancel
POST /api/v1/workflows/{id}/actions/retry
POST /api/v1/workflows/{id}/actions/resume
```

Workflow creation uses a named template or validated workflow definition. V2.0 does not accept arbitrary shell commands from API clients.

## 7. Concurrency

PATCH/DELETE require `If-Match: <resource_version>` or equivalent request field. Version mismatch returns HTTP 409.

## 8. Idempotency

Mutation endpoints accept `Idempotency-Key`. Repeated requests with the same key and equivalent body return the original result.

## 9. Error Envelope

```json
{
  "error": {
    "code": "RESOURCE_VERSION_CONFLICT",
    "message": "resource was modified",
    "request_id": "...",
    "details": {}
  }
}
```

Standard status use:

```text
400 validation error
401 unauthenticated
403 unauthorized or destructive confirmation missing
404 resource not found
409 conflict
422 semantic validation error
429 rate limited
500 internal error
503 dependency unavailable
```

## 10. Destructive Confirmation

Destructive actions require:

```text
confirm=true
confirmation_phrase matching the action
optional approval_id in enterprise edition
```

The confirmation value is recorded in AuditEvent but secrets are redacted.

## 11. Authentication and Authorization Boundary

Community V2.0 may support local authentication. Enterprise extensions may add OIDC/LDAP. Authorization is evaluated before resource service or workflow creation.

## 12. Events and Streaming

```text
GET /api/v1/events/stream
GET /api/v1/workflows/{id}/events
GET /api/v1/tasks/{id}/logs
```

WebSocket or Server-Sent Events may be used. Event order is based on event sequence/resource version, not client receive time.

## 13. Compatibility

Breaking changes require `/api/v2` or a new API version. Additive fields are allowed. Clients must ignore unknown fields.

## 14. Existing API Migration

Existing direct playbook routers remain temporarily supported through a compatibility layer. They must create Task or Workflow resources and may not bypass the frozen architecture.

## 15. Review Items

1. Accept resource-oriented REST plus explicit `/actions` endpoints.
2. Accept HTTP 202 and Workflow references for infrastructure changes.
3. Accept cursor pagination and optimistic concurrency.
4. Accept generic workflow endpoint plus typed action endpoints.
5. Accept a compatibility layer for existing L15 APIs during V2.0 migration.
