# 企业级 CSI / 存储体系设计（V1）

## 1. 目标

本项目当前已经具备：

```text
single-node
→
HA etcd
→
HA control plane
→
VIP + Keepalived + Nginx
→
VIP kubeconfig
```

下一阶段目标：

```text
企业级 CSI / 存储体系
```

最终形成：

```text
企业级 Kubernetes 交付平台
```

---

# 2. 设计原则

CSI 层必须满足：

```text
可插拔
可迁移
支持多后端
支持企业 SAN
支持云原生存储
支持 single → HA 演进
```

设计上不绑定某一个存储实现。

采用：

```text
Kubernetes
  ↓
CSI 抽象层
  ↓
Storage Backend
```

---

# 3. 支持的存储后端

## 3.1 local-lvm

定位：

```text
单节点
边缘节点
开发环境
PoC
```

特点：

```text
高性能
本地盘
不依赖网络
不支持跨节点漂移
```

推荐实现：

```text
topolvm
```

默认 StorageClass：

```text
local-lvm
```

---

## 3.2 NFS CSI

定位：

```text
轻量共享存储
测试环境
低成本共享目录
```

推荐实现：

```text
nfs-subdir-external-provisioner
```

默认 StorageClass：

```text
nfs-csi
```

支持：

```text
RWX
动态 provisioning
共享目录
```

---

## 3.3 iSCSI SAN

定位：

```text
企业已有 SAN
集中式块存储
企业存储阵列
```

推荐接入：

```text
NetApp
Dell EMC
Pure Storage
OceanStor
Lenovo
Inspur
```

支持模式：

### 模式 A（推荐）

厂商 CSI：

```text
NetApp Trident
Dell CSI
Huawei CSI
Pure CSI
```

### 模式 B

通用 iSCSI CSI：

```text
democratic-csi
csi-driver-iscsi
```

必须支持：

```text
multipath
CHAP
snapshot
clone
expansion
retain policy
```

默认 StorageClass：

```text
iscsi-san
```

---

## 3.4 Rook Ceph

定位：

```text
企业云原生生产环境
多副本
分布式存储
```

推荐实现：

```text
Rook Ceph
```

支持：

```text
RBD
CephFS
Snapshot
Expansion
Clone
Self-healing
```

默认生产 StorageClass：

```text
ceph-rbd
```

共享文件：

```text
cephfs
```

---

# 4. 存储架构

新增：

```text
roles/
  storage_preflight/
  storage_common/
  storageclass/
  storage_health/

  csi_local_lvm/
  csi_nfs/
  csi_iscsi_san/
  csi_rook_ceph/
```

新增 playbook：

```text
0058-storage-preflight.yml
0059-install-csi.yml
0060-install-storageclass.yml
0061-storage-health-check.yml
0062-storage-migration-check.yml
```

---

# 5. Inventory 设计

新增：

```yaml
storage_enabled: true

storage_backend: local-lvm
# local-lvm | nfs | iscsi-san | rook-ceph

storage_default_class: local-lvm

storage_snapshot_enabled: true
storage_expansion_enabled: true

storage_reclaim_policy: Delete
storage_retain_class_enabled: true

storage_enable_topology: true
```

新增 storage group：

```text
[storage]
storage-01
storage-02
storage-03
```

用于：

```text
Ceph OSD
NFS Server
iSCSI Target
```

---

# 6. StorageClass 设计

内置：

```text
local-lvm
nfs-csi
iscsi-san
ceph-rbd
ceph-rbd-retain
cephfs
```

默认生产推荐：

```yaml
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

关键业务建议：

```yaml
reclaimPolicy: Retain
```

---

# 7. single → HA 与 CSI

CSI 安装必须位于：

```text
etcd HA
control-plane HA
VIP kubeconfig
```

之后。

推荐顺序：

```text
1. etcd HA
2. control plane HA
3. VIP kubeconfig
4. storage preflight
5. CSI install
6. StorageClass install
7. PVC validation
8. workload migration
```

禁止：

```text
在 etcd/control-plane 迁移期间修改 CSI
```

---

# 8. storage-preflight

0058-storage-preflight.yml 必须检查：

```text
StorageClass
PVC
PV
StatefulSet
local PV
VolumeSnapshot CRD
磁盘状态
网络状态
multipath
iscsiadm
```

输出：

```text
风险报告
迁移建议
是否允许继续
```

---

# 9. 企业级运维能力

必须支持：

```text
VolumeSnapshot
Expansion
PVC Health Check
CSI Pod Health Check
VolumeAttachment Health Check
StorageClass Validation
```

后续规划：

```text
Velero
CSI Snapshot Backup
Ceph Backup
Disaster Recovery
```

---

# 10. 推荐默认方案

## 单节点

```yaml
storage_backend: local-lvm
```

## 小型共享

```yaml
storage_backend: nfs
```

## 企业 SAN

```yaml
storage_backend: iscsi-san
```

## 企业生产

```yaml
storage_backend: rook-ceph
```

---

# 11. 推荐开发顺序

严格建议：

```text
1. storage_preflight
2. local-lvm
3. nfs
4. iscsi-san
5. rook-ceph
6. health-check
7. migration
```

不要优先实现 Ceph。

---

# 12. 最终目标

最终形成：

```text
single node
→
HA control plane
→
企业级 CSI
→
企业级存储迁移
→
企业级备份恢复
```

最终成为：

```text
完整企业级 Kubernetes 交付平台
```
