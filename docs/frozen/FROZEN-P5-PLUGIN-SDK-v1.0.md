# FROZEN-P5 Plugin SDK Specification v1.0

> Status: FROZEN
> Version: v1.0
> Depends on:
> - FROZEN-P0-02-SYSTEM-ARCHITECTURE-v1.0
> - FROZEN-P1-01-DOMAIN-MODEL-v1.0
> - FROZEN-P2-01-DATA-ARCHITECTURE-v1.0
> - FROZEN-P3-API-SPECIFICATION-v1.0
> - FROZEN-P4-WORKFLOW-ENGINE-v1.0
> Scope: CPP V2.0 plugin model, extension boundary, capability declaration and SDK baseline
> Rule: Any incompatible change to plugin boundary, capability model, installation lifecycle or security model must create a new design version and pass review again.

---

## 1. Purpose

This specification freezes the CPP V2.0 Plugin SDK design.

Plugin is the primary extension mechanism for storage, network, identity, VM, backup and observability capabilities.

---

## 2. Core Principle

Plugin extends the platform but must not bypass the platform.

Forbidden:

```text
Plugin -> Database directly
Plugin -> Private internal service implementation
Plugin -> Executor directly without Workflow/Runtime policy
Plugin -> Kubernetes credentials outside approved boundary
```

Allowed:

```text
Plugin -> Resource API
Plugin -> Workflow API
Plugin -> Declared extension interface
Plugin -> Approved capability adapter
```

---

## 3. Plugin Resource

Plugin is a Resource.

```yaml
Plugin:
  metadata:
    id: string
    kind: Plugin
    name: string
    labels: map[string]string
    annotations: map[string]string
    generation: integer
    resource_version: string
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime|null
  spec:
    category: storage | network | identity | vm | backup | observability
    version: string
    provider: string
    entrypoint: string
    capabilities: list[string]
    config_schema: object
  status:
    phase: installed | enabled | disabled | failed
    reason: string|null
    last_checked_at: datetime|null
```

---

## 4. Plugin Categories

V2.0 freezes these categories:

```text
storage
network
identity
vm
backup
observability
```

V2.0 implementation priority:

```text
1. storage
2. backup
3. observability
4. vm
5. identity
6. network
```

Network is recognized but may remain minimal in V2.0.

---

## 5. Capability Model

Plugins must declare capabilities.

Examples:

```text
storage.provision
storage.snapshot
storage.expand
backup.create
backup.restore
observability.metrics.export
identity.oidc
vm.image.import
```

Rules:

```text
1. Capabilities must be explicit.
2. API and Workflow may check capabilities before creating operations.
3. Capabilities are part of Plugin status and audit context.
4. Unsupported capabilities must fail safely.
```

---

## 6. Plugin Lifecycle

Lifecycle:

```text
registered -> installed -> enabled -> disabled
registered -> installed -> failed
```

Rules:

```text
1. Install must validate manifest and config schema.
2. Enable must verify required capabilities.
3. Disable must not delete resources by default.
4. Failed plugin state must preserve diagnostic reason.
5. Every lifecycle transition must emit ResourceEvent and AuditEvent.
```

---

## 7. Plugin Manifest

Every plugin must provide a manifest.

```yaml
apiVersion: cpp.io/v1
kind: PluginManifest
metadata:
  name: example-storage-plugin
spec:
  category: storage
  version: 1.0.0
  provider: example
  entrypoint: example.storage.Plugin
  capabilities:
    - storage.provision
    - storage.snapshot
  configSchema:
    type: object
```

---

## 8. SDK Interface Baseline

V2.0 SDK interface baseline:

```text
load(manifest)
validate_config(config)
health_check()
list_capabilities()
execute(operation, context)
```

The exact language-level interface may be implemented in Python first.

---

## 9. Operation Context

Plugin operations receive a controlled context.

```yaml
PluginContext:
  request_id: string
  workflow_id: string|null
  task_id: string|null
  actor: string
  cluster_id: string|null
  target_kind: string|null
  target_id: string|null
  params: object
```

Context must not expose raw database handles.

---

## 10. Security Boundary

Rules:

```text
1. Plugin must run with least privilege.
2. Plugin credentials must be stored through approved secret mechanism.
3. Plugin must not access unrelated cluster credentials.
4. Plugin operations must be auditable.
5. Dangerous plugin operations must be Workflow-based.
```

V2.0 may run plugins in-process for simplicity, but the API contract must allow future out-of-process isolation.

---

## 11. Plugin and Workflow

Complex plugin actions must be exposed as Workflow templates.

Examples:

```text
storage.create_pool
storage.validate_pool
backup.create_vm_backup
backup.restore_vm
observability.install_stack
```

Plugin should contribute capabilities and operation handlers, not bypass workflow orchestration.

---

## 12. Plugin and Resource Model

Plugin-created objects must map to frozen Resource kinds or approved extension resources.

Rules:

```text
1. Storage plugins should produce StoragePool and StorageClass resources.
2. Backup plugins should produce Backup resources.
3. Observability plugins should produce Plugin status and events.
4. New resource kinds require design review.
```

---

## 13. Version Compatibility

Each plugin declares:

```text
plugin version
supported CPP API version
supported capability version
```

V2.0 must reject incompatible plugins safely.

---

## 14. Deferred

The following are deferred:

```text
Plugin marketplace
Remote plugin sandbox
WebAssembly plugin runtime
Multi-language SDKs
Plugin signing and attestation
Enterprise plugin licensing
```

---

## 15. Frozen Decisions

```text
1. Plugin is a Resource.
2. Plugin must not access database directly.
3. Plugin capability declaration is mandatory.
4. Plugin lifecycle is auditable.
5. Plugin operations must use Resource/Workflow APIs or stable extension interfaces.
6. In-process Python plugins are acceptable for V2.0, but the contract must allow out-of-process isolation later.
```
