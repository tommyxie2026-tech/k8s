# Platform API 设计（L15）

## 1. 目标

Platform API 是本项目从 Ansible Playbook 集合升级为企业级平台控制面的关键层。

目标：

```text
统一入口
统一权限
统一任务模型
统一审计
统一资源抽象
```

它不替代现有 Playbook，而是把现有能力封装成稳定 API。

---

## 2. API 覆盖范围

L15 API 第一阶段覆盖：

```text
Cluster
NodePool
StoragePool
KubeVirt VM
Backup & Recovery
Observability
Governance
Task
```

---

## 3. 总体架构

```text
Client / WebUI / CLI / GitOps
          │
          ▼
┌──────────────────────┐
│ Platform API          │
│ FastAPI / REST        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Task Executor         │
│ ansible-playbook      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Existing Playbooks    │
│ 0000 ~ 0096           │
└──────────────────────┘
```

---

## 4. 设计原则

```text
1. API 默认只读
2. 破坏性操作必须显式确认
3. 所有异步任务必须返回 task_id
4. 不直接暴露 shell 命令给调用方
5. 不在 API 层保存敏感凭据明文
6. API 层只编排，不隐藏底层 playbook
7. 所有操作可审计、可追踪、可回放
```

---

## 5. 资源模型

### 5.1 Cluster

```text
GET /api/v1/clusters
GET /api/v1/clusters/{cluster}/health
GET /api/v1/clusters/{cluster}/capacity
```

### 5.2 NodePool

```text
GET  /api/v1/nodepools
POST /api/v1/nodepools/apply
GET  /api/v1/nodepools/health
```

### 5.3 StoragePool

```text
GET /api/v1/storagepools
GET /api/v1/storagepools/health
GET /api/v1/storageclasses/governance
```

### 5.4 VM

```text
GET  /api/v1/vms
POST /api/v1/vms/{namespace}/{name}/start
POST /api/v1/vms/{namespace}/{name}/stop
POST /api/v1/vms/{namespace}/{name}/restart
```

### 5.5 Backup

```text
POST /api/v1/backups/etcd
POST /api/v1/backups/vm
GET  /api/v1/backups/preflight/velero
GET  /api/v1/backups/snapshots/check
```

### 5.6 Restore

```text
POST /api/v1/restores/etcd/preflight
POST /api/v1/restores/vm
```

### 5.7 Observability

```text
GET /api/v1/observability/preflight
```

### 5.8 Task

```text
GET /api/v1/tasks
GET /api/v1/tasks/{task_id}
GET /api/v1/tasks/{task_id}/logs
```

---

## 6. Task 模型

所有会执行 playbook 的 API 都返回：

```json
{
  "task_id": "uuid",
  "status": "pending",
  "playbook": "0095-kubevirt-vm-backup.yml"
}
```

任务状态：

```text
pending
running
success
failed
cancelled
```

---

## 7. 安全模型

### 7.1 只读接口

默认不需要危险确认。

### 7.2 写操作

必须显式参数：

```json
{
  "confirm": true
}
```

### 7.3 破坏性操作

必须二次确认：

```json
{
  "confirm": true,
  "confirm_phrase": "RESTORE_VM"
}
```

etcd restore 类操作必须使用：

```text
RESTORE_ETCD
```

---

## 8. 与 Ansible 的关系

Platform API 调用现有 Makefile/Playbook，不重复实现底层逻辑。

例如：

```text
POST /api/v1/backups/vm
↓
0095-kubevirt-vm-backup.yml
```

```text
POST /api/v1/restores/vm
↓
0096-kubevirt-vm-restore.yml
```

---

## 9. 第一阶段交付物

```text
platform-api/
├── app/
│   ├── main.py
│   ├── core/config.py
│   ├── core/task_store.py
│   ├── core/executor.py
│   ├── schemas/common.py
│   └── routers/
│       ├── health.py
│       ├── tasks.py
│       ├── cluster.py
│       ├── nodepool.py
│       ├── storagepool.py
│       ├── vm.py
│       ├── backup.py
│       ├── restore.py
│       └── observability.py
├── requirements.txt
└── README.md
```

---

## 10. 后续阶段

```text
L16 CLI
L17 Web UI
L18 GitOps Controller
L19 Terraform Provider
```
