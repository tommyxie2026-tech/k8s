# CPP Current Implementation Sprint

> Milestone: M0 Engineering Baseline
> Status: IN PROGRESS
> Updated: 2026-07-11

## Completed

```text
[x] Frozen P0-P8 design baseline
[x] Design-to-Code Gap Analysis v1.0
[x] Implementation Plan v1.0
[x] Repository-native implementation status board
[x] T0.8 Executor call-site inventory
[x] T0.9 TaskInfo / JobRecord consumer inventory
[x] T0.10 Compatibility and deprecation map
```

## Current Batch

```text
[ ] T0.1 Add pytest baseline and test directory structure
[ ] T0.2 Add Ruff configuration
[ ] T0.3 Add mypy or pyright baseline
[ ] T0.4 Add CI workflow for lint, unit tests and import validation
[ ] T0.5 Add application startup smoke test
[ ] T0.6 Add architecture dependency test preventing router -> executor imports
[~] T0.7 Complete current API route inventory
```

## Exit Criteria

```text
CI runs on every pull request.
Platform API imports successfully.
Application startup smoke test passes.
New router-to-executor dependencies fail CI.
Existing compatibility surface is documented.
```

## Next Milestone

```text
M1 Persistence Foundation
```

M1 may begin only after the M0 quality gates are green.
