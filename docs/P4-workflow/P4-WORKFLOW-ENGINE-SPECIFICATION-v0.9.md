# P4 Workflow Engine Specification v0.9

> Status: Design Review
> Depends on frozen architecture, domain and data specifications

## 1. Purpose

Defines Workflow as the only orchestration mechanism for multi-step or destructive infrastructure operations.

## 2. Core Model

```text
Workflow
  ├── metadata/spec/status
  ├── target resource
  ├── ordered Tasks
  ├── retry policy
  ├── timeout policy
  ├── approval requirements
  ├── compensation plan
  └── event stream
```

## 3. State Machines

Workflow:

```text
pending -> queued -> running -> succeeded
                           -> failed
                           -> cancelled
                           -> waiting_approval
                           -> compensating -> compensated | compensation_failed
```

Task:

```text
pending -> queued -> running -> succeeded | failed | cancelled | skipped
```

Terminal states are immutable except through an explicit retry workflow.

## 4. Execution Rules

```text
Workflow Engine schedules; it never executes commands.
Runtime claims Tasks; Executor performs commands.
One Task uses exactly one Executor type.
Task result is persisted before the next dependent Task starts.
```

## 5. Workflow Definition

```yaml
name: backup.vm
version: 1
inputs: {}
destructive: false
steps:
  - id: preflight
    executor: ansible
    command_ref: 0092-velero-preflight.yml
    timeout: 300
    retry:
      max_attempts: 1
  - id: backup
    depends_on: [preflight]
    executor: ansible
    command_ref: 0095-kubevirt-vm-backup.yml
```

Definitions are versioned and validated before registration. Arbitrary untrusted commands are prohibited.

## 6. Scheduling and Claiming

Workers claim queued Tasks using an atomic lease. A lease includes worker_id, leased_at and lease_expires_at. Expired leases may be reclaimed after safety checks.

V2.0 may use database polling. V2.1 may add Redis or an external queue without changing Workflow semantics.

## 7. Idempotency

Each Task has an idempotency key derived from workflow, step and attempt. Executors should support safe re-entry. Non-idempotent operations require preflight checks and compensation.

## 8. Retry

Retry is opt-in per step. Defaults:

```text
max_attempts: 1
backoff: exponential
retryable errors: explicitly classified
```

Validation, authorization and confirmation failures are never automatically retried.

## 9. Timeout and Cancellation

Task timeout is mandatory. Cancellation is cooperative first, forced only where executor safety permits. A cancelled Workflow does not imply infrastructure rollback.

## 10. Saga Compensation

Cross-resource consistency uses Saga compensation. Compensation steps are explicit, versioned and auditable. Automatic compensation is disabled for steps where reversal could cause data loss.

## 11. Approval and Destructive Operations

Destructive workflows require confirmation. Enterprise edition may require one or more approval records. Approval state is separate from task execution state.

## 12. Persistence

Workflow, Task, attempts, events and log references are durable. Process memory is not authoritative. Engine restart must recover queued/running workflows by lease reconciliation.

## 13. Executor Contract

```python
execute(task_context) -> ExecutionResult
cancel(task_id) -> CancelResult
health() -> ExecutorHealth
```

ExecutionResult includes exit_code, stdout_ref, stderr_ref, structured_output, started_at, finished_at and error classification.

## 14. Observability

Required events:

```text
WorkflowCreated
WorkflowQueued
WorkflowStarted
WorkflowSucceeded
WorkflowFailed
WorkflowCancelled
TaskQueued
TaskStarted
TaskSucceeded
TaskFailed
TaskRetried
CompensationStarted
CompensationFinished
```

## 15. Initial Workflow Templates

```text
cluster.validate
governance.full_check
backup.etcd
restore.etcd_preflight
backup.vm
restore.vm
storage.health_check
storage.snapshot_check
observability.preflight
```

## 16. Security

Executor input is generated from validated templates. Secrets are passed by reference, never logged, and redacted from audit/output.

## 17. Review Items

1. Accept durable DB-backed scheduling for V2.0.
2. Accept explicit Saga compensation rather than implicit rollback.
3. Accept versioned templates and prohibit arbitrary shell from public APIs.
4. Accept lease-based task claiming and restart recovery.
5. Accept existing direct actions only through Task compatibility resources.
