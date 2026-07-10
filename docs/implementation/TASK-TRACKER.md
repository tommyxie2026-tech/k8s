# CPP V2.0 Task Tracker

> Status: ACTIVE
> Source: IMPLEMENTATION-PLAN-v1.0.md
> Note: GitHub Issues are disabled in this repository, so this file is the version-controlled execution tracker.

## Progress

| Milestone | Status | Progress |
|---|---|---:|
| M0 Engineering Baseline | IN PROGRESS | 0/10 |
| M1 Persistence Foundation | NOT STARTED | 0/22 |
| M2 Runtime Convergence | NOT STARTED | 0/16 |
| M3 Workflow Engine | NOT STARTED | 0/15 |
| M4 Resource Plane and API | NOT STARTED | 0/? |
| M5 Security, Audit and Events | NOT STARTED | 0/? |
| M6 Plugin SDK | NOT STARTED | 0/? |
| M7 Web Console | NOT STARTED | 0/? |
| M8 Release Validation | NOT STARTED | 0/? |

---

## M0 Engineering Baseline

### Epic E0.1 Project Quality Gates

- [ ] T0.1 Add pytest baseline and test directory structure
- [ ] T0.2 Add Ruff configuration
- [ ] T0.3 Add mypy baseline for platform-api
- [ ] T0.4 Add CI workflow for lint, unit tests and import validation
- [ ] T0.5 Add application startup smoke test
- [ ] T0.6 Add architecture dependency test preventing router -> executor imports

### Epic E0.2 Compatibility Inventory

- [ ] T0.7 Inventory all current API routes
- [ ] T0.8 Inventory all executor call sites
- [ ] T0.9 Inventory TaskInfo and JobRecord consumers
- [ ] T0.10 Define compatibility and deprecation map

### M0 Exit Criteria

- [ ] CI runs lint and tests
- [ ] Platform API imports successfully
- [ ] Health endpoint smoke test passes
- [ ] New router-to-executor dependencies fail tests
- [ ] Compatibility inventory is committed

---

## M1 Persistence Foundation

See `IMPLEMENTATION-PLAN-v1.0.md` for T1.1 through T1.22.

## M2 Runtime Convergence

See `IMPLEMENTATION-PLAN-v1.0.md` for T2.1 through T2.16.

## M3-M8

See `IMPLEMENTATION-PLAN-v1.0.md`. Detailed checklists will be expanded before each milestone starts.

---

## Change Rules

```text
1. Mark a task complete only after tests and acceptance criteria pass.
2. Every schema change includes an Alembic migration.
3. Every API change includes a contract test.
4. Every workflow state change includes transition tests.
5. Frozen design changes require design review before implementation.
```
