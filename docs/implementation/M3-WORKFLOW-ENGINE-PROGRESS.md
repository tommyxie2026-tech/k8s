# M3 Workflow Engine Progress

> Status: IN PROGRESS
> Milestone: M3 Workflow Engine

## Implemented in current increment

- [x] T3.1 Persist Workflow and WorkflowStep models — model existed; durable step repository added.
- [x] T3.2 Implement workflow state machine baseline.
- [x] T3.3 Implement ordered-step and dependency validation baseline.
- [x] T3.4 Implement failure propagation baseline.

## Artifacts

```text
platform-api/app/db/models.py
platform-api/app/db/workflow_repositories.py
platform-api/app/services/workflow_service.py
platform-api/tests/test_workflow_service.py
```

## Architectural changes

```text
Before:
WorkflowService -> subprocess -> ansible-playbook -> file workflow store

After:
WorkflowService -> WorkflowRepository / WorkflowStepRepository
Runtime worker -> TaskService -> Executor
```

The new WorkflowService does not execute infrastructure commands.

## Test coverage added

```text
Workflow and ordered-step persistence
Forward/unknown dependency rejection
Workflow phase transitions
Dependency satisfaction enforcement
Successful workflow completion
Step failure propagation to workflow
Terminal workflow transition rejection
```

## Verification state

- [ ] CI lint passed
- [ ] CI type check passed
- [ ] CI pytest passed

These boxes remain open until GitHub Actions or an equivalent local test run confirms them.

## Remaining M3 tasks

- [ ] T3.5 Implement cancellation propagation to active/pending steps and tasks
- [ ] T3.6 Implement timeout handling
- [ ] T3.7 Add retry policy
- [ ] T3.8 Implement bounded retry/backoff
- [ ] T3.9 Add compensation model
- [ ] T3.10 Add resume support
- [ ] T3.11 Persist retry/compensation events
- [ ] T3.12 Centralize destructive confirmation
- [ ] T3.13 Convert hard-coded templates to versioned definitions
- [ ] T3.14 Align workflow API with frozen P3

## Next implementation increment

```text
T3.5 cancellation
T3.6 timeout
T3.7/T3.8 retry policy and bounded retry
```
