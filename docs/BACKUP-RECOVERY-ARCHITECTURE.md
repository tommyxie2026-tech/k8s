# Backup & Recovery 架构设计（V1）

## 1. 目标

本文档定义本项目的企业级备份与恢复体系，覆盖：

```text
etcd
Kubernetes 资源
CSI/PVC/PV
KubeVirt VM
CDI/DataVolume
Rook Ceph
iSCSI SAN
NFS
配置与证书
```

核心目标：

```text
可备份
可恢复
可演练
可审计
可跨集群迁移
```

---

## 2. 设计原则

必须遵循：

```text
1. 备份平面与业务平面解耦
2. 备份数据不能只保存在被备份集群内部
3. etcd 备份、资源备份、数据备份必须分层
4. VM 恢复必须同时恢复 VM spec 与磁盘数据
5. PVC 恢复必须保留 StorageClass 与 ReclaimPolicy 语义
6. 恢复流程必须先演练，再生产启用
```

不允许：

```text
只备份 YAML 不备份数据
只备份 PVC 不备份 CRD
只备份 VM spec 不备份磁盘
只在本集群保存备份
未验证 restore 就宣称可备份
```

---

## 3. 总体架构

推荐：

```text
          ┌───────────────────────────┐
          │ External Backup Repository│
          │ S3 / MinIO / NAS / Object │
          └──────────────┬────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼───────┐ ┌──────▼───────┐ ┌──────▼───────┐
│ etcd snapshot │ │ Velero backup│ │ Storage Snap │
└───────┬───────┘ └──────┬───────┘ └──────┬───────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                  ┌──────▼──────┐
                  │ Restore Run │
                  └─────────────┘
```

分层：

```text
L1 etcd snapshot
L2 Kubernetes resources backup
L3 PVC/Volume backup
L4 VM backup
L5 Storage backend snapshot
L6 Cross-cluster restore
```

---

## 4. 备份对象分层

### 4.1 etcd

备份内容：

```text
Kubernetes control-plane state
CRD objects
KubeVirt CR
CDI CR
PVC/PV metadata
```

用途：

```text
集群级灾难恢复
控制面恢复
```

限制：

```text
etcd 备份不等于数据盘备份
不能只靠 etcd 恢复 VM 数据
```

---

### 4.2 Kubernetes Resources

工具建议：

```text
Velero
GitOps export
kubectl get -A -o yaml
```

备份对象：

```text
Namespace
Deployment
StatefulSet
DaemonSet
Service
Ingress
ConfigMap
Secret
CRD
KubeVirt VM
CDI DataVolume
StorageClass
```

---

### 4.3 PVC / PV 数据

根据后端不同选择：

```text
CSI Snapshot
Velero restic / node-agent
Ceph RBD snapshot
SAN snapshot
NFS rsync/snapshot
```

---

### 4.4 KubeVirt VM

VM 备份必须包含：

```text
VirtualMachine spec
DataVolume/PVC spec
PVC data
cloud-init Secret/ConfigMap
Network attachment
Service/Ingress
```

VM 恢复顺序：

```text
1. Namespace
2. Secrets / ConfigMaps
3. PVC / DataVolume
4. VM spec
5. Service / Network
6. Start VM
7. Health check
```

---

## 5. 存储后端策略

### 5.1 Rook Ceph

推荐：

```text
RBD snapshot
CephFS snapshot
Velero CSI snapshot
对象存储备份 metadata
```

恢复重点：

```text
Pool 存在
StorageClass 存在
CephCluster healthy
SnapshotClass 匹配
```

---

### 5.2 iSCSI SAN

推荐：

```text
厂商快照
LUN clone
CSI snapshot
multipath 校验
```

恢复重点：

```text
LUN 映射
CHAP
Portal
Multipath
PV reclaim policy
```

---

### 5.3 NFS

推荐：

```text
后端 NAS snapshot
rsync
restic
```

注意：

```text
NFS 适合文件型备份
不建议用于高 IO VM 生产盘
```

---

### 5.4 local-lvm

适合：

```text
单节点/边缘
测试
```

推荐：

```text
LVM snapshot
rsync/restic
业务停机备份
```

限制：

```text
节点故障可能导致本地数据不可恢复
不建议作为生产 HA 主存储
```

---

## 6. 恢复等级

### R0：配置恢复

恢复：

```text
YAML
ConfigMap
Secret
CRD
```

不恢复业务数据。

---

### R1：命名空间恢复

恢复：

```text
Namespace 下资源
PVC metadata
部分数据卷
```

---

### R2：应用恢复

恢复：

```text
StatefulSet + PVC data
Deployment + Config
Service
Ingress
```

---

### R3：VM 恢复

恢复：

```text
VM spec
DataVolume/PVC
VM root disk
VM data disk
Network
```

---

### R4：集群恢复

恢复：

```text
etcd
control-plane
CRD
CSI
KubeVirt
业务资源
数据卷
```

---

## 7. 推荐 Playbook 规划

```text
0090-etcd-backup.yml
0091-etcd-restore-preflight.yml
0092-etcd-restore.yml

0093-velero-preflight.yml
0094-install-velero.yml
0095-velero-backup.yml
0096-velero-restore.yml

0097-kubevirt-vm-backup-plan.yml
0098-kubevirt-vm-restore-plan.yml

0099-storage-snapshot-check.yml
```

说明：

```text
restore 必须拆 preflight 与 execute
恢复动作必须显式确认
默认只做计划与检查
```

---

## 8. 安全边界

默认必须只读：

```text
backup plan
restore preflight
snapshot check
```

破坏性动作必须显式确认：

```yaml
confirm_restore: true
confirm_etcd_restore: true
confirm_vm_restore: true
```

禁止默认执行：

```text
etcd restore
PVC overwrite
VM delete/recreate
namespace delete
```

---

## 9. 恢复演练要求

生产启用前必须完成：

```text
1. etcd snapshot restore 演练
2. Namespace restore 演练
3. StatefulSet + PVC restore 演练
4. KubeVirt VM restore 演练
5. Ceph/iSCSI/NFS 后端恢复演练
6. RTO/RPO 记录
```

---

## 10. RTO / RPO 建议

| 场景 | RPO | RTO |
|---|---:|---:|
| 配置恢复 | 1h | 30m |
| Namespace 恢复 | 1h-4h | 1h |
| StatefulSet 恢复 | 15m-1h | 1h-4h |
| VM 恢复 | 15m-1h | 1h-4h |
| 整集群恢复 | 1h-24h | 4h-24h |

---

## 11. 最终结论

生产级平台必须同时具备：

```text
备份
恢复
演练
审计
外部保存
跨集群迁移
```

本项目下一阶段应优先落地：

```text
0090-etcd-backup.yml
0091-etcd-restore-preflight.yml
0093-velero-preflight.yml
0097-kubevirt-vm-backup-plan.yml
```

先做只读与计划，再做真正执行。
