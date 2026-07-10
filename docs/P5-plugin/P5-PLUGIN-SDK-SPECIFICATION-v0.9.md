# P5 Plugin SDK Specification v0.9

> Status: Design Review
> Depends on frozen architecture, domain, data and API specifications

## 1. Purpose

Defines a stable extension mechanism for storage, network, identity, VM, backup and observability capabilities without modifying CPP core.

## 2. Plugin Principles

```text
Capability-driven
Versioned contracts
Out-of-process preferred
No direct database access
No private core imports
Least privilege
Explicit health and lifecycle
Backward-compatible SDK evolution
```

## 3. Plugin Manifest

```yaml
apiVersion: cpp.io/v1
kind: PluginManifest
metadata:
  name: ceph-rbd
spec:
  category: storage
  version: 1.0.0
  sdk_version: v1
  entrypoint: https://plugin.example
  capabilities:
    - storage.pool.discover
    - storage.snapshot.create
  permissions:
    resources: [StoragePool, StorageClass]
    actions: [read, update-status, create-workflow]
```

## 4. Plugin Categories

```text
storage
network
identity
vm
backup
observability
```

A plugin may declare multiple capabilities but has one primary category.

## 5. Communication Model

V2.0 supports HTTP/gRPC out-of-process plugins. In-process Python plugins are allowed only for trusted built-ins and must use the same public interfaces.

```text
Core -> Plugin Gateway -> Plugin
Plugin -> Public Resource/Workflow API
```

## 6. Mandatory Interfaces

```text
GetManifest
Health
ListCapabilities
ValidateConfig
Discover
Plan
Execute or CreateWorkflow
```

Plugins should return plans and structured results. Infrastructure execution should normally be delegated to Workflow/Runtime rather than performed inside the plugin process.

## 7. Capability Contract

Capabilities use namespaced identifiers:

```text
storage.pool.discover
storage.class.reconcile
storage.snapshot.create
backup.vm.prepare
identity.user.lookup
observability.metrics.collect
```

Unknown capabilities are ignored by older cores. Required capabilities must be explicitly negotiated.

## 8. Security

Plugins receive scoped credentials and short-lived tokens. Secrets are passed by reference. Network egress and resource permissions are declared in the manifest. Plugins cannot read arbitrary CPP resources.

## 9. Lifecycle

```text
installed -> enabled -> healthy
                    -> degraded
                    -> failed
enabled -> disabled
```

Install, enable, disable, upgrade and uninstall are Workflow operations and generate AuditEvents.

## 10. Version Compatibility

Semantic versioning applies to plugins. SDK major version mismatch blocks activation. Minor additions are backward-compatible. Plugin upgrade must support health check and rollback plan.

## 11. Failure Isolation

Plugin failure must not crash Platform API or Workflow Engine. Calls use timeout, circuit breaker and bounded retries. Plugin status reflects health without mutating unrelated resources.

## 12. Built-in Reference Plugins

V2.0 should validate the SDK with at least three storage implementations:

```text
local-lvm
nfs-csi
ceph-rbd or iscsi
```

## 13. Testing Contract

Each plugin must pass:

```text
manifest validation
capability conformance
API compatibility
failure isolation
security boundary
upgrade/rollback
integration test
```

## 14. Review Items

1. Accept out-of-process plugins as the preferred model.
2. Accept public API-only access and prohibit direct DB access.
3. Accept capability negotiation and semantic versioning.
4. Accept plugin lifecycle as Workflow operations.
5. Accept three reference storage plugins as V2.0 conformance targets.
