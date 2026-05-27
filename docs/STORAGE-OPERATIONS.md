# 企业级 Kubernetes 存储运维手册（V1）

# 1. 目标

本文档定义企业级 CSI 存储的日常运维、故障处理、扩容、快照、恢复和迁移检查方法。

覆盖后端：

```text
local-lvm
nfs
iscsi-san
rook-ceph
```

目标：

```text
可观测
可诊断
可恢复
可扩容
可审计
```

---

# 2. 日常检查

每日检查：

```bash
kubectl get sc
kubectl get pvc -A
kubectl get pv
kubectl get volumeattachment
kubectl get pods -A | grep -i csi
```

必须关注：

```text
PVC Pending
PV Released
VolumeAttachment 残留
CSI Pod CrashLoopBackOff
节点磁盘压力
```

---

# 3. PVC Pending

常见原因：

```text
StorageClass 不存在
CSI controller 异常
volumeBindingMode=WaitForFirstConsumer 但没有 Pod 调度
后端存储容量不足
拓扑约束不满足
```

排查：

```bash
kubectl describe pvc -n <ns> <pvc>
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl get pods -A | grep -i csi
```

---

# 4. VolumeAttachment 残留

常见表现：

```text
Pod 无法挂载卷
Multi-Attach error
节点已下线但卷仍 attached
```

排查：

```bash
kubectl get volumeattachment
kubectl describe volumeattachment <name>
```

处理原则：

```text
先确认后端卷已 detach
再处理 Kubernetes VolumeAttachment
禁止盲删生产 VolumeAttachment
```

---

# 5. iSCSI 运维

检查 session：

```bash
iscsiadm -m session
```

检查 multipath：

```bash
multipath -ll
systemctl status multipathd
```

常见问题：

```text
portal 不通
CHAP 认证失败
multipath 丢路径
LUN 未授权给节点 IQN
```

恢复建议：

```text
先恢复网络和 SAN path
再恢复 iscsi session
最后重建 workload
```

---

# 6. Ceph 运维

检查：

```bash
kubectl -n rook-ceph get pods
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph health detail
```

必须关注：

```text
HEALTH_WARN
OSD down
PG degraded
MON quorum lost
CSI Pod 异常
```

生产要求：

```text
ceph health == HEALTH_OK
```

---

# 7. NFS 运维

检查：

```bash
showmount -e <nfs-server>
mount -t nfs <nfs-server>:<path> /mnt
```

常见问题：

```text
NFS server 不可达
目录权限错误
root_squash
网络抖动
```

---

# 8. local-lvm 运维

检查：

```bash
lvs
vgs
pvs
lsblk
```

风险：

```text
节点故障即数据风险
不可跨节点漂移
```

生产建议：

```text
local-lvm 不作为核心生产默认存储
```

---

# 9. 扩容

PVC 扩容前检查：

```bash
kubectl get sc <sc> -o yaml | grep allowVolumeExpansion
```

扩容：

```bash
kubectl patch pvc <pvc> -n <ns> -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

必须确认：

```text
后端支持扩容
文件系统支持在线扩容
CSI driver 支持 expansion
```

---

# 10. 快照

检查：

```bash
kubectl get volumesnapshotclass
kubectl get volumesnapshot -A
```

迁移/升级前建议：

```text
关键 PVC 必须先 snapshot
```

---

# 11. 回滚

回滚原则：

```text
保留旧 PVC
保留旧 PV
保留 snapshot
禁止迁移后立即删除旧数据
```

推荐：

```text
先回切 workload
再验证数据
最后清理新资源
```

---

# 12. 告警建议

必须监控：

```text
PVC Pending 数量
PV Released 数量
VolumeAttachment 异常
CSI Pod 重启次数
Ceph HEALTH_WARN
iSCSI session 数量
multipath path 数量
节点磁盘使用率
```

---

# 13. 后续自动化

后续 playbook：

```text
0061-storage-health-check.yml
0062-storage-migration-check.yml
```

将自动输出：

```text
存储健康报告
迁移风险报告
是否允许继续
```
