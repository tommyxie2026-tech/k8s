# K8s Platform API

L15 Platform API 是现有 Ansible Playbook 能力之上的统一控制面入口。

## 运行

```bash
cd platform-api
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8080
```

访问：

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/docs
```

## Docker

```bash
docker build -f platform-api/Dockerfile -t k8s-platform-api:dev .
docker run --rm -p 8080:8080 k8s-platform-api:dev
```

## 当前 API

```text
GET  /health
GET  /api/v1/jobs
GET  /api/v1/jobs/{task_id}
GET  /api/v1/clusters/current
POST /api/v1/clusters/preflight
POST /api/v1/clusters/syntax-check
POST /api/v1/nodepools/health-check
POST /api/v1/nodepools/apply-labels
POST /api/v1/storagepools/health-check
POST /api/v1/storagepools/storageclass-governance
POST /api/v1/storagepools/volume-snapshot-check
POST /api/v1/governance/scheduling
POST /api/v1/governance/failure-domain
POST /api/v1/governance/capacity
POST /api/v1/governance/admission-baseline
POST /api/v1/observability/preflight
POST /api/v1/backups/etcd
POST /api/v1/backups/etcd/restore-preflight
POST /api/v1/backups/velero/preflight
POST /api/v1/backups/velero/install-plan
POST /api/v1/backups/vm
POST /api/v1/backups/vm/restore
POST /api/v1/vms/start
POST /api/v1/vms/stop
POST /api/v1/vms/status
POST /api/v1/vms/backup
POST /api/v1/vms/restore
```

## V1 边界

当前版本重点是：

```text
统一入口
任务模型
Playbook 编排
安全确认参数透传
OpenAPI 文档
```

不包含：

```text
多租户
数据库持久化
完整 RBAC
审批流
Web UI
```
