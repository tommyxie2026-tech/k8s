# P1-00 Resource-Centric Domain Model 总纲

> 状态：Design Review v0.9  
> 阶段：P1 Domain Model  
> 前置：P0 Architecture Freeze v1.0  
> 原则：Everything Is A Resource

---

## 1. 目标

P1 的目标是为 CPP 定义统一领域模型。

该模型将成为后续所有设计的基础：

```text
P1 Domain Model
    ↓
P2 Database Schema
    ↓
P3 API Specification
    ↓
P4 Workflow Specification
    ↓
P5 Plugin SDK
    ↓
Implementation
```

P1 不直接定义数据库表，也不直接定义 REST API，而是定义平台真正认识的资源、状态、生命周期、事件和边界。

---

## 2. 设计原则

P1 采用 Resource-Centric Domain Model，而不是传统实体优先的 DDD。

原因：

```text
CPP 是 Cloud Control Plane
Control Plane 的第一公民是 Resource
Resource 统一驱动 API / DB / Workflow / RBAC / Audit / Plugin
```

核心原则：

```text
Everything Is A Resource
Every Resource Has Lifecycle
Every Resource Has Status
Every Resource Emits Events
Every Operation Maps To Workflow Or Action
Every Mutation Must Be Auditable
```

---

## 3. 领域划分

P1 将 CPP 划分为以下 Domain：

```text
Cluster Domain
Node Domain
Storage Domain
Network Domain
Virtualization Domain
Workflow Domain
Backup Domain
Identity Domain
Observability Domain
Plugin Domain
```

这些是业务领域，不是代码目录。

---

## 4. Resource 统一结构

所有 Resource 都应具备以下通用字段：

```yaml
apiVersion: cpp.io/v1
kind: ResourceKind
metadata:
  id: ""
  name: ""
  namespace: ""
  labels: {}
  annotations: {}
  createdAt: ""
  updatedAt: ""
spec: {}
status:
  phase: ""
  conditions: []
  reason: ""
  message: ""
```

其中：

```text
metadata 描述资源身份
spec 描述期望状态
status 描述实际状态
conditions 描述细粒度健康和进展
```

---

## 5. 通用生命周期

推荐所有 Resource 尽量复用以下生命周期：

```text
Pending
Creating
Ready
Updating
Deleting
Failed
Unknown
```

对于特殊资源可扩展，但不得破坏统一状态模型。

---

## 6. 通用 Condition 模型

所有 Resource 的 status.conditions 使用统一结构：

```yaml
conditions:
  - type: Ready
    status: "True"
    reason: "Ready"
    message: "Resource is ready"
    lastTransitionTime: ""
```

推荐 condition 类型：

```text
Ready
Healthy
Scheduled
Provisioned
Validated
BackedUp
Restored
Synced
```

---

## 7. 通用事件模型

所有资源变化都应产生事件：

```text
resource.created
resource.updated
resource.deleted
resource.failed
workflow.created
workflow.succeeded
workflow.failed
backup.created
restore.succeeded
```

事件用于：

```text
Audit
Observability
Workflow Trigger
Notification
```

---

## 8. Domain 文档模板

每个 Domain 文档必须包含：

```text
1. Domain 目标
2. Resource 列表
3. Resource 关系
4. Resource 生命周期
5. 状态机
6. 事件
7. Workflow 入口
8. API 映射建议
9. RBAC 边界
10. Plugin 扩展点
11. Out of Scope
```

---

## 9. P1 文档计划

```text
P1-00 Resource-Centric Domain Model 总纲
P1-01 Cluster Domain
P1-02 Node Domain
P1-03 Storage Domain
P1-04 Network Domain
P1-05 Virtualization Domain
P1-06 Workflow Domain
P1-07 Backup Domain
P1-08 Identity Domain
P1-09 Observability Domain
P1-10 Plugin Domain
```

---

## 10. 冻结候选内容

P1-00 建议冻结：

```text
Resource-Centric Domain Model
统一 Resource 结构
统一生命周期
统一 Condition 模型
统一事件模型
Domain 文档模板
P1 文档计划
```

暂不冻结：

```text
具体数据库字段
具体 REST API 路径
具体插件接口
具体前端页面
```

这些分别进入 P2/P3/P5/P6。
