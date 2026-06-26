# L16 Workflow Engine 设计

## 1. 目标

L16 的目标是把 L15 Platform API 从“同步 API 调用 Ansible Playbook”升级为“平台级工作流控制面”。

核心目标：

```text
1. 所有操作进入统一 Workflow
2. 所有 Workflow 由多个 Step 组成
3. 每个 Step 可审计、可追踪、可重试
4. 破坏性操作需要策略确认
5. API 返回 workflow_id，而不是直接同步等待
6. 后续可替换为 Temporal / Argo Workflows / Celery
```

---

## 2. 架构

```text
Client / WebUI / CLI
        │
        ▼
Platform API
        │
        ▼
Workflow Engine
        │
        ├── Workflow Store
        ├── Step Runner
        ├── Policy Guard
        ├── Audit Log
        └── Executor Adapter
                │
                ▼
          Ansible / kubectl / virtctl
```

---

## 3. Workflow 模型

```json
{
  "workflow_id": "wf-20260611-001",
  "name": "kubevirt.vm.backup",
  "status": "running",
  "steps": [
    {
      "name": "preflight",
      "type": "playbook",
      "target": "0092-velero-preflight.yml",
      "status": "succeeded"
    },
    {
      "name": "vm-backup-plan",
      "type": "playbook",
      "target": "0095-kubevirt-vm-backup.yml",
      "status": "running"
    }
  ]
}
```

---

## 4. 状态机

```text
queued
running
succeeded
failed
cancelled
blocked
```

其中：

```text
blocked = 被策略阻断，比如缺少 confirm 或 confirm_phrase
```

---

## 5. Workflow 类型

V1 支持：

```text
cluster.preflight
cluster.syntax_check
nodepool.health_check
storagepool.health_check
governance.full_check
observability.preflight
backup.etcd
backup.vm
restore.vm
```

---

## 6. Policy Guard

破坏性或高风险操作必须带确认：

```text
etcd backup: backup_apply_confirm=true
etcd restore: confirm_phrase=RESTORE_ETCD
vm restore: confirm_phrase=RESTORE_VM
node label apply: confirm=true
velero install: confirm=true
```

---

## 7. V1 实现边界

V1 使用内存 Workflow Store，适合开发和单进程 PoC。

后续升级：

```text
SQLite / PostgreSQL Job Store
Celery / RQ 异步队列
Temporal / Argo Workflows 工作流引擎
OIDC + RBAC
```

---

## 8. 验收标准

```text
1. 可以创建 workflow
2. workflow 可以包含多个 step
3. step 可以调用现有 executor
4. 可以查询 workflow 状态
5. 可以列出 workflow
6. confirm 缺失时可以被策略阻断
```
