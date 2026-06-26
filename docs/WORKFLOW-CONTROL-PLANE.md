# L16 Workflow / Control Plane 产品化设计

## 1. 目标

L16 的目标是把 L15 Platform API 从 API Facade 升级为可产品化的控制面。

核心变化：

```text
L15: API -> Playbook
L16: API -> Workflow -> Step -> Executor -> Job Store -> Audit
```

也就是：

```text
请求不再只是触发单个 playbook
而是创建可追踪、可恢复、可审计的 workflow
```

---

## 2. L16 必须解决的问题

```text
1. Job 状态不能只存在内存中
2. 多步骤任务需要统一编排
3. 破坏性操作需要审批/确认模型
4. 执行结果需要可审计
5. 失败后需要能定位到具体 step
6. 后续可以替换为 Temporal / Argo Workflows
```

---

## 3. 架构

```text
Client / WebUI / CLI
        │
        ▼
Platform API
        │
        ▼
Workflow Service
        │
        ▼
Workflow Definition
        │
        ▼
Step Executor
        │
        ▼
Ansible / kubectl / virtctl
        │
        ▼
Job Store + Audit Log
```

---

## 4. Workflow 模型

```json
{
  "workflow_id": "wf-xxxx",
  "name": "vm-backup",
  "status": "running",
  "steps": [
    {
      "name": "volume-snapshot-check",
      "playbook": "0094-volume-snapshot-check.yml",
      "status": "succeeded"
    },
    {
      "name": "vm-backup-plan",
      "playbook": "0095-kubevirt-vm-backup.yml",
      "status": "running"
    }
  ]
}
```

状态：

```text
queued
running
succeeded
failed
cancelled
```

---

## 5. V1 内置工作流

### 5.1 Cluster Validate

```text
syntax-check
preflight
smoke-test
```

---

### 5.2 VM Backup

```text
0092-velero-preflight
0094-volume-snapshot-check
0095-kubevirt-vm-backup
```

---

### 5.3 VM Restore

```text
0092-velero-preflight
0094-volume-snapshot-check
0096-kubevirt-vm-restore
```

---

### 5.4 Governance Full Scan

```text
0074-scheduling-policy-check
0075-storageclass-governance
0076-failure-domain-check
0077-capacity-planning
0078-cluster-admission-baseline
```

---

## 6. 持久化策略

V1 使用文件型 Job Store：

```text
/tmp/k8s-platform-api/workflows/*.json
/tmp/k8s-platform-api/audit.log
```

后续升级：

```text
SQLite
PostgreSQL
Temporal
Argo Workflows
```

---

## 7. 审计策略

每次 workflow 创建、step 执行、失败、完成都写入：

```json
{
  "ts": "2026-06-26T00:00:00Z",
  "event": "workflow.step.succeeded",
  "workflow_id": "wf-xxx",
  "step": "velero-preflight"
}
```

---

## 8. V1 验收标准

```text
1. 支持 POST /api/v1/workflows/governance/full-scan
2. 支持 POST /api/v1/workflows/vm/backup
3. 支持 POST /api/v1/workflows/vm/restore
4. 支持 GET /api/v1/workflows/{workflow_id}
5. Workflow 状态写入本地 JSON
6. Audit log 写入本地文件
7. 任一步失败后 workflow 标记 failed
```
