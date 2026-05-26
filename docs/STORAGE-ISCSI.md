# 企业级 iSCSI SAN / CSI 设计（V1）

# 1. 目标

本文档定义：

```text
Kubernetes 集群
如何接入企业 SAN / iSCSI 存储
```

目标：

```text
企业级块存储
高性能数据库
企业存储阵列
统一 CSI 管理
```

支持：

```text
Dell EMC
NetApp
Pure Storage
Huawei OceanStor
Lenovo
Inspur
通用 SAN
```

---

# 2. iSCSI 在 Kubernetes 中的定位

iSCSI：

```text
是一种块设备接入协议
不是完整存储平台
```

Kubernetes 中：

```text
CSI
  ↓
iSCSI
  ↓
SAN / Storage Array
```

因此：

```text
iSCSI 必须结合 CSI
才能形成企业级动态存储
```

---

# 3. 为什么企业仍然使用 iSCSI

原因：

```text
已有 SAN 投资
成熟存储阵列
数据库性能要求
企业运维体系
备份体系
```

典型场景：

```text
Oracle
MySQL
PostgreSQL
MongoDB
Kafka
Redis
```

---

# 4. Kubernetes 中的推荐架构

推荐：

```text
Kubernetes
  ↓
Vendor CSI
  ↓
iSCSI
  ↓
Enterprise SAN
```

不推荐：

```text
直接 static PV + iscsi
```

因为：

```text
不可维护
无法动态 provisioning
不支持快照
不支持自动扩容
```

---

# 5. 推荐实现方式

## 5.1 模式 A（推荐）

厂商 CSI：

```text
NetApp Trident
Dell CSI
Pure CSI
Huawei CSI
```

优点：

```text
动态 LUN
快照
克隆
扩容
一致性
企业支持
```

这是：

```text
生产推荐方案
```

---

## 5.2 模式 B（通用）

通用 iSCSI CSI：

```text
democratic-csi
csi-driver-iscsi
```

适合：

```text
实验环境
通用 SAN
小规模企业
```

限制：

```text
高级能力有限
厂商特性不完整
```

---

# 6. Kubernetes Node 侧组件

所有节点必须安装：

```text
open-iscsi
iscsiadm
multipath-tools
dm-multipath
```

systemd 服务：

```text
iscsid
multipathd
```

必须自动化：

```text
自动安装
自动 enable
自动 health-check
```

---

# 7. Multipath（必须）

企业 SAN：

```text
必须启用 multipath
```

原因：

```text
多路径冗余
链路故障切换
稳定性
```

推荐：

```text
至少双 portal
```

示例：

```yaml
iscsi_target_portals:
  - 10.0.0.101
  - 10.0.0.102
```

---

# 8. CHAP 认证

必须支持：

```text
CHAP
Mutual CHAP
```

inventory：

```yaml
iscsi_chap_enabled: true
iscsi_chap_username: admin
iscsi_chap_password: secret
```

禁止：

```text
生产环境关闭认证
```

---

# 9. Inventory 设计

新增：

```yaml
storage_backend: iscsi-san

iscsi_target_portals:
  - 10.0.0.101
  - 10.0.0.102

iscsi_iqn: iqn.2026-01.com.example:k8s

iscsi_chap_enabled: true
iscsi_chap_username: admin
iscsi_chap_password: secret

iscsi_multipath_enabled: true

iscsi_fs_type: xfs

storage_default_class: iscsi-san
```

---

# 10. 推荐 StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: iscsi-san
provisioner: csi.example.com
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

关键业务推荐：

```yaml
reclaimPolicy: Retain
```

---

# 11. 必须支持的能力

企业级 iSCSI CSI 必须支持：

```text
Dynamic Provisioning
Snapshot
Clone
Expansion
Retain Policy
VolumeAttachment
Multipath
Topology
```

否则：

```text
不允许进入生产
```

---

# 12. storage-preflight

0058-storage-preflight.yml
必须检查：

```text
iscsiadm
multipathd
portal reachable
IQN auth
CHAP
CSI Pod
VolumeAttachment
```

并输出：

```text
风险报告
```

---

# 13. CSI Health Check

0061-storage-health-check.yml
必须检查：

```text
CSI Controller
CSI Node Plugin
VolumeAttachment
multipath
iscsi session
```

推荐：

```text
自动修复 session
自动 reconnect
```

---

# 14. 迁移策略

single → HA 时：

```text
禁止先迁移存储
```

推荐顺序：

```text
1. etcd HA
2. control plane HA
3. VIP kubeconfig
4. CSI install
5. StorageClass
6. PVC validation
7. StatefulSet migration
```

---

# 15. 企业最佳实践

推荐：

```text
数据库使用 Retain
日志使用 Delete
多 portal
multipath
独立 storage VLAN
```

不推荐：

```text
单 portal
无 multipath
无 CHAP
static iscsi PV
```

---

# 16. 后续规划

未来扩展：

```text
Velero
CSI Snapshot Backup
Disaster Recovery
Cross Cluster Replication
Storage QoS
```

---

# 17. 最终目标

最终形成：

```text
企业 Kubernetes
  ↓
CSI
  ↓
企业 SAN
```

形成：

```text
完整企业级块存储体系
```
