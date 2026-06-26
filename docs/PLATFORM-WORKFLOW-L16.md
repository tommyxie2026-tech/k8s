# L16 Workflow / Control Plane 产品化设计

## 1. 目标

L16 的目标是把 L15 Platform API 从“API 调用 Ansible Playbook”升级为“工作流控制面”。

核心变化：

```text
L15: API -> executor.submit(playbook)
L16: API -> workflow -> steps -> executor -> audit/state
```

---

## 2. 为什么需要 Workflow Engine

随着能力增加，单个 API 调用已经不能代表完整平台动作。

例如 VM 备份应该包含：

```text
1. preflight
2. snapshot check
3. velero backup plan
4. backup execution
5. backup validation
6. audit log
```

单节点升级 HA 也应包含：

```text
backup
etcd preflight
etcd expansion
control-plane expansion
LB enable
kubeconfig switch
post check
```

因此 L16 需要引入 workflow。

---

## 3. 设计原则

```text
1. Workflow 默认异步
2. 每个 Workflow 由多个 Step 组成
3. 每个 Step 映射一个 playbook / shell / internal action
4. 所有 Step 有状态：pending/running/succeeded/failed/skipped
5. 破坏性 workflow 必须 confirm=true 和 confirm_phrase
6. workflow 状态必须可查询
7. V1 使用内存状态，V2 切换 SQLite/PostgreSQL
8. V1 仍复用 Ansible Playbook，不重写底层能力
```

---

## 4. 核心模型

```text
Workflow
├── workflow_id
├── name
├── status
├── destructive
├── steps[]
└── timestamps

WorkflowStep
├── name
├── action
├── playbook
├── extra_vars
├── status
├── stdout
├── stderr
└── return_code
```

---

## 5. API 变化

新增：

```text
POST /api/v1/workflows
GET  /api/v1/workflows
GET  /api/v1/workflows/{workflow_id}
```

后续业务 API 不再直接调用 executor，而是提交 workflow：

```text
POST /api/v1/backups/vm
-> workflow: kubevirt.vm.backup
```

---

## 6. V1 预置 Workflow

```text
cluster.syntax_check
cluster.preflight
nodepool.health_check
storagepool.health_check
governance.full_check
observability.preflight
backup.etcd
backup.vm
restore.vm
single_to_ha.migration
```

---

## 7. 状态存储演进

V1：

```text
InMemoryWorkflowStore
```

V2：

```text
SQLiteWorkflowStore
```

V3：

```text
PostgreSQLWorkflowStore
```

---

## 8. L16 验收标准

```text
1. platform-api 可启动
2. /api/v1/workflows 可创建 workflow
3. /api/v1/workflows/{id} 可查询 step 状态
4. governance.full_check 可串行执行 0074/0075/0076/0077/0078
5. backup.vm 可串行执行 0094/0095
6. destructive workflow 没有确认时必须拒绝
```
