# 企业级 Rook Ceph / CSI 设计（V1）

# 1. 目标

本文档定义：

```text
Kubernetes 企业级云原生存储方案
```

采用：

```text
Rook Ceph
```

实现：

```text
高可用
多副本
动态存储
块存储
文件存储
快照
扩容
自愈
```

最终形成：

```text
企业级云原生存储平台
```

---

# 2. 为什么选择 Rook Ceph

Rook Ceph 的定位：

```text
Kubernetes 原生分布式存储
```

相比：

```text
NFS
local-lvm
iSCSI static PV
```

优势：

```text
多副本
高可用
动态 provisioning
自愈
Snapshot
Clone
Expansion
RBD
CephFS
对象存储
```

适合：

```text
企业生产
数据库
中间件
AI 平台
大规模 StatefulSet
```

---

# 3. 架构

推荐：

```text
Kubernetes
  ↓
Rook Operator
  ↓
Ceph Cluster
  ↓
OSD / MON / MGR
```

CSI：

```text
RBD CSI
CephFS CSI
```

---

# 4. 组件说明

## 4.1 MON

作用：

```text
Ceph 元数据与 quorum
```

生产建议：

```text
MON=3
```

禁止：

```text
单 MON 生产
```

---

## 4.2 MGR

作用：

```text
管理与 metrics
```

建议：

```text
MGR=2
```

---

## 4.3 OSD

作用：

```text
真实数据存储
```

建议：

```text
每节点至少 1 块独立数据盘
```

推荐：

```text
NVMe SSD
```

禁止：

```text
OSD 与系统盘混用
```

---

## 4.4 RBD

定位：

```text
块存储
```

适合：

```text
MySQL
PostgreSQL
Kafka
Redis
MongoDB
```

默认生产推荐：

```text
ceph-rbd
```

---

## 4.5 CephFS

定位：

```text
共享文件存储
```

适合：

```text
共享目录
日志
模型文件
AI 数据集
```

默认：

```text
cephfs
```

---

# 5. 节点规划

推荐：

```text
control-plane 与 storage 分离
```

新增：

```text
[storage]
storage-01
storage-02
storage-03
```

用于：

```text
OSD
MON
MGR
```

---

# 6. 磁盘规划

推荐：

```text
系统盘
OSD 数据盘
日志盘
```

示例：

```text
/dev/sda -> OS
/dev/sdb -> OSD
/dev/nvme0n1 -> DB WAL
```

禁止：

```text
自动格式化系统盘
```

---

# 7. Inventory 设计

新增：

```yaml
storage_backend: rook-ceph

ceph_replica_size: 3

ceph_enable_rbd: true
ceph_enable_cephfs: true

ceph_auto_discover_devices: false

ceph_osd_devices:
  - /dev/sdb
  - /dev/sdc
```

可选：

```yaml
ceph_auto_discover_devices: true
```

生产不推荐自动发现。

---

# 8. 推荐 StorageClass

## 8.1 RBD

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: rook-ceph.rbd.csi.ceph.com
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

---

## 8.2 Retain

关键数据库：

```yaml
reclaimPolicy: Retain
```

推荐：

```text
ceph-rbd-retain
```

---

## 8.3 CephFS

```yaml
provisioner: rook-ceph.cephfs.csi.ceph.com
```

支持：

```text
RWX
```

---

# 9. 必须支持的能力

企业级 Ceph CSI 必须支持：

```text
Snapshot
Clone
Expansion
Retain
Topology
Self-healing
```

否则：

```text
不允许进入生产
```

---

# 10. storage-preflight

0058-storage-preflight.yml
必须检查：

```text
OSD 磁盘
磁盘是否为空
MON 数量
网络 MTU
磁盘类型
CPU / 内存
```

禁止：

```text
直接格式化未知磁盘
```

---

# 11. 网络设计

推荐：

```text
storage network
cluster network
```

生产建议：

```text
25G/40G 网络
jumbo frame
```

至少：

```text
10G
```

---

# 12. Health Check

0061-storage-health-check.yml
必须检查：

```text
ceph health
MON quorum
OSD up/in
PG status
CSI Pod
```

必须验证：

```text
ceph health == HEALTH_OK
```

---

# 13. 企业最佳实践

推荐：

```text
MON=3
MGR=2
OSD>=3
replica=3
独立数据盘
SSD/NVMe
```

数据库建议：

```text
RBD + Retain
```

AI 平台建议：

```text
CephFS
```

---

# 14. single → HA 与 Ceph

推荐顺序：

```text
1. etcd HA
2. control-plane HA
3. VIP kubeconfig
4. Ceph deploy
5. StorageClass
6. PVC validation
7. workload migration
```

禁止：

```text
control-plane 迁移期间部署 Ceph
```

---

# 15. Backup / DR

后续规划：

```text
Velero
Ceph Snapshot
RBD Mirror
Disaster Recovery
Cross Cluster Replication
```

---

# 16. 未来规划

未来支持：

```text
RGW
S3
对象存储
Ceph Dashboard
Ceph Observability
```

---

# 17. 最终目标

最终形成：

```text
Kubernetes
  ↓
Rook Ceph
  ↓
企业级云原生存储
```

形成：

```text
完整企业级分布式存储平台
```
