# 企业级 Kubernetes 存储迁移设计（V1）

# 1. 目标

本文档定义：

```text
Kubernetes 集群中的存储迁移策略
```

覆盖：

```text
single → HA
StorageClass 迁移
PVC/PV 迁移
CSI 迁移
StatefulSet 迁移
Ceph / iSCSI / NFS / local-lvm
```

最终实现：

```text
企业级可回滚存储迁移
```

---

# 2. 核心原则

存储迁移必须满足：

```text
可回滚
最小中断
可审计
先验证后切换
禁止直接破坏 PV
```

禁止：

```text
直接删除生产 PVC
直接删除 PV
直接修改绑定中的 PV
```

---

# 3. 迁移风险

Kubernetes 存储迁移是：

```text
整个集群中风险最高的操作之一
```

主要风险：

```text
数据丢失
StatefulSet 崩溃
PV orphan
VolumeAttachment 残留
StorageClass 误删
local PV 丢失
```

因此：

```text
迁移前必须 backup
```

---

# 4. 推荐迁移顺序

single → HA 推荐：

```text
1. etcd HA
2. control-plane HA
3. VIP kubeconfig
4. storage-preflight
5. CSI install
6. StorageClass install
7. PVC validation
8. workload migration
```

禁止：

```text
control-plane 迁移期间修改存储
```

---

# 5. storage-preflight

0058-storage-preflight.yml
必须检查：

```text
StorageClass
PVC
PV
StatefulSet
VolumeSnapshot
CSI Pod
VolumeAttachment
```

还必须输出：

```text
local PV 风险
Retain/Delete 风险
是否允许继续
```

---

# 6. StorageClass 迁移

推荐策略：

```text
新增 StorageClass
而不是直接覆盖 default class
```

例如：

```text
local-lvm
→
ceph-rbd
```

推荐：

```text
新 PVC
新数据同步
再切换 workload
```

禁止：

```text
直接修改 existing PV backend
```

---

# 7. PVC/PV 迁移

推荐方式：

```text
新建 PVC
数据同步
切换 workload
```

不推荐：

```text
直接 patch PV
```

原因：

```text
Kubernetes 不保证底层数据一致性
```

---

# 8. StatefulSet 迁移

StatefulSet 是：

```text
最高风险迁移对象
```

包括：

```text
MySQL
PostgreSQL
Kafka
Redis
MongoDB
```

推荐：

```text
逐实例迁移
```

顺序：

```text
1. backup
2. freeze writes
3. sync data
4. switch PVC
5. verify
6. resume traffic
```

---

# 9. local-lvm 风险

local PV：

```text
无法跨节点漂移
```

节点故障时：

```text
数据可能永久丢失
```

因此：

```text
single → HA 时
必须优先迁移 local PV
```

推荐：

```text
local-lvm
→
Ceph / iSCSI
```

---

# 10. NFS 迁移

NFS 适合：

```text
共享目录
日志
低性能 workload
```

不推荐：

```text
高 IO 数据库
```

迁移到 Ceph 时：

```text
rsync
snapshot
停机切换
```

---

# 11. iSCSI SAN 迁移

推荐：

```text
StorageClass 级别迁移
```

例如：

```text
old SAN
→
new SAN
```

必须：

```text
multipath
CHAP
VolumeAttachment validation
```

禁止：

```text
直接修改 active LUN
```

---

# 12. Ceph 迁移

推荐：

```text
RBD Snapshot
RBD Mirror
CephFS Sync
```

推荐流程：

```text
1. 新 pool
2. 新 StorageClass
3. 新 PVC
4. 数据同步
5. workload switch
```

---

# 13. Retain / Delete 策略

生产数据库推荐：

```yaml
reclaimPolicy: Retain
```

临时 workload：

```yaml
reclaimPolicy: Delete
```

迁移期间：

```text
禁止使用 Delete 删除生产 PVC
```

---

# 14. Snapshot

企业级迁移必须支持：

```text
VolumeSnapshot
```

推荐：

```text
迁移前 snapshot
迁移后 snapshot
```

否则：

```text
不允许生产迁移
```

---

# 15. Health Check

0061-storage-health-check.yml
必须检查：

```text
PVC Bound
PV Bound
CSI Pod
VolumeAttachment
Snapshot
```

必须验证：

```text
所有 PVC 正常 attach
```

---

# 16. 回滚策略

迁移必须支持：

```text
快速回滚
```

推荐：

```text
旧 PVC 保留
旧 PV retain
snapshot rollback
```

禁止：

```text
迁移后立即删除旧数据
```

---

# 17. 企业最佳实践

推荐：

```text
先新建 StorageClass
先同步数据
先小规模验证
StatefulSet 分批迁移
保留旧 PV
```

禁止：

```text
生产环境直接 replace PV
直接 patch storage backend
直接删除 active PVC
```

---

# 18. 后续规划

未来支持：

```text
Velero
Cross Cluster Migration
Disaster Recovery
Volume Replication
Storage QoS
```

---

# 19. 最终目标

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

最终实现：

```text
企业级 Kubernetes 存储平台
```
