# P6 Web Console Design v0.9

> Status: Design Review
> Depends on P3 API and P4 Workflow specifications

## 1. Purpose

Defines the Web Console information architecture, resource views, workflow experience, safety model and frontend integration boundaries.

## 2. Product Navigation

```text
Overview
Clusters
Nodes
Storage
  ├── Storage Pools
  └── Storage Classes
Virtual Machines
Backups
Workflows
Tasks
Plugins
Events & Audit
Administration
```

## 3. Resource Page Pattern

Every resource page follows:

```text
List -> Detail -> Spec/Status -> Related Resources -> Events -> Actions
```

The UI must preserve the metadata/spec/status separation.

## 4. List Views

Required capabilities:

```text
Cursor pagination
Search
Label and field filtering
Status filtering
Saved views
Bulk selection where safe
Soft-deleted resource view for administrators
```

## 5. Detail Views

Standard tabs:

```text
Summary
Specification
Status
Relationships
Events
Audit
YAML/JSON
```

Editable spec fields use forms and PATCH APIs with resource_version checks.

## 6. Workflow Experience

Infrastructure actions open a plan/confirmation dialog and then create a Workflow. The UI shows:

```text
Workflow status
Step graph
Current task
Duration
Logs
Events
Retry/cancel/resume availability
Compensation status
```

The UI never assumes an action completed merely because the API request returned successfully.

## 7. Destructive Safety

Destructive actions require:

```text
Impact summary
Affected resources
Typed confirmation phrase
Optional approval state
Backup/preflight recommendation
```

Dangerous operations cannot be placed as one-click actions in list rows.

## 8. Real-Time Updates

The console consumes WebSocket or SSE events. Polling is a fallback. Event reconnect uses sequence/resource version checkpoints.

## 9. Dashboard

Overview displays:

```text
Cluster health
Node readiness
VM status
Storage capacity and degradation
Backup freshness
Failed/running workflows
Recent audit/security events
```

Dashboard data comes from public aggregation APIs, not direct database access.

## 10. Permissions

Navigation and actions are permission-aware. Hidden UI controls do not replace server-side authorization.

## 11. Accessibility and Internationalization

V2.0 baseline:

```text
Keyboard navigation
Accessible labels
Color-independent status indicators
Chinese and English localization framework
UTC API time with local display
```

## 12. Frontend Architecture

Recommended boundary:

```text
Web App
  -> Typed API Client generated from OpenAPI
  -> Query/cache layer
  -> Resource components
  -> Workflow/event client
```

Framework choice is not frozen in this document. React/Vue selection may be made through a separate ADR.

## 13. Error Handling

The console renders the standard API error envelope, request_id and actionable recovery advice. Version conflicts offer refresh-and-reapply rather than silent overwrite.

## 14. Review Items

1. Accept resource-centric navigation.
2. Accept workflow-first action experience.
3. Accept typed confirmation for destructive actions.
4. Accept spec/status separation in all detail pages.
5. Defer frontend framework choice to ADR.
