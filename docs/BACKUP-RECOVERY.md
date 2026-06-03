# Backup & Recovery 灾备设计（V1）

## 1. 目标

本项目已经具备 Kubernetes HA、CSI、KubeVirt、CDI、资源池治理、容量盘点和独立监控设计。下一阶段需要补齐灾备能力，使平台具备生产交付的底线能力。

灾备目标：

```text
控制面可恢复
业务资源可恢复
PVC/VM 数据可恢复
KubeVirt VM 可恢复
存储后端故障可定位
恢复流程可演练
```

---

## 2. 灾备分层

灾备分为五层：

```text
L1 etcd backup / restore
L2 Kubernetes resource backup / restore
L3 PVC / PV backup / restore
L4 KubeVirt VM backup / restore
L5 Storage backend snapshot / restore
```

对应能力：

```text
etcd snapshot
Velero
CSI snapshot
KubeVirt VMExport / Velero plugin
Ceph RBD snapshot / iSCSI SAN snapshot
```

---

## 3. 设计原则

必须遵循：

```text
1. 备份数据必须独立于被保护集群
2. 备份存储不能只放在业务集群内部
3. 恢复流程必须可演练
4. VM/PVC 恢复前必须先确认 StorageClass 可用
5. etcd 恢复必须与证书、apiserver 地址、VIP 配合
6. KubeVirt VM 恢复必须考虑 DataVolume/PVC/StorageClass
```

禁止：

```text
只做 etcd 备份，不做 PVC 数据备份
只备份 YAML，不备份持久化卷
把唯一备份放在同一个 Ceph 集群内
未演练就宣称具备生产灾备能力
```

---

## 4. 推荐备份对象

### 4.1 控制面

```text
etcd snapshot
apiserver certs
front-proxy certs
service-account keys
admin kubeconfig
encryption-config
HA LB/VIP 配置
```

### 4.2 Kubernetes 资源

```text
Namespace
Deployment
StatefulSet
DaemonSet
Service
Ingress
ConfigMap
Secret
PVC
StorageClass
CRD
```

### 4.3 KubeVirt 资源

```text
VirtualMachine
VirtualMachineInstance
DataVolume
CDI config
VM PVC
cloud-init Secret
network attachment definition
```

### 4.4 存储资源

```text
PVC/PV
VolumeSnapshot
Ceph RBD snapshot
iSCSI SAN snapshot
NFS export metadata
local-lvm LV metadata
```

---

## 5. 推荐 Playbook 规划

```text
0090-backup-preflight.yml
0091-etcd-snapshot.yml
0092-etcd-restore-preflight.yml
0093-velero-install.yml
0094-velero-backup.yml
0095-velero-restore.yml
0096-kubevirt-vm-backup.yml
0097-kubevirt-vm-restore.yml
0098-storage-snapshot.yml
0099-disaster-recovery-drill.yml
```

---

## 6. etcd 备份策略

建议：

```text
每日定时 snapshot
变更前手动 snapshot
single-to-HA 前 snapshot
证书轮换前 snapshot
KubeVirt/CDI 升级前 snapshot
```

备份内容：

```text
snapshot.db
snapshot status
etcd member list
etcd endpoint health
证书文件清单
```

备份位置：

```text
本地临时目录
外部备份服务器
对象存储
离线归档
```

---

## 7. Velero 策略

Velero 用于备份 Kubernetes API 资源与部分 PVC 数据。

推荐对象存储：

```text
S3
MinIO
Ceph RGW
企业对象存储
```

建议策略：

```text
namespace 级备份
应用级备份
KubeVirt namespace 备份
CSI VolumeSnapshot 集成
```

---

## 8. KubeVirt VM 灾备策略

VM 恢复需要同时保护：

```text
VM spec
DataVolume
PVC
Secret
NetworkAttachmentDefinition
StorageClass 映射
```

推荐恢复顺序：

```text
1. 恢复 Namespace
2. 恢复 StorageClass / SnapshotClass
3. 恢复 PVC / VolumeSnapshot
4. 恢复 DataVolume
5. 恢复 VirtualMachine
6. 启动 VM
7. 执行 VM health-check
```

---

## 9. 存储后端策略

### 9.1 Ceph RBD

推荐：

```text
RBD snapshot
RBD mirror
Ceph pool 级容量监控
定期恢复演练
```

### 9.2 iSCSI SAN

推荐：

```text
厂商快照
LUN clone
multipath 状态备份
CHAP 配置备份
```

### 9.3 NFS

推荐：

```text
rsync / restic
export 配置备份
文件级恢复演练
```

### 9.4 local-lvm

仅建议用于测试/边缘：

```text
LV snapshot
节点级备份
不可作为生产 HA 唯一备份
```

---

## 10. 恢复等级

| 等级 | 描述 | 目标 |
|---|---|---|
| R0 | 只恢复 YAML | 开发测试 |
| R1 | 恢复 Kubernetes 资源 | 无状态业务 |
| R2 | 恢复 PVC 数据 | StatefulSet |
| R3 | 恢复 VM + PVC | KubeVirt 生产 VM |
| R4 | 跨集群恢复 | 灾难恢复 |

---

## 11. DR 演练

每次演练必须记录：

```text
备份时间
恢复时间
RTO
RPO
失败点
数据一致性检查
业务验证结果
```

最低演练频率：

```text
PoC：按需
测试环境：每月
生产环境：每季度
关键系统：每月或每次重大变更前
```

---

## 12. 与独立监控的关系

灾备依赖独立监控：

```text
备份任务失败告警
备份过期告警
对象存储不可达告警
VolumeSnapshot 失败告警
VM 恢复失败告警
```

监控平面必须在业务集群之外，避免灾难发生时告警和历史记录一起丢失。

---

## 13. 最终目标

最终形成：

```text
HA + Governance + Observability + Backup/Recovery
```

平台才可以从“可部署”进入“可生产交付”。
