# VM / 裸金属真实环境验证手册

本文档用于指导在真实 VM 或裸金属环境中验证当前项目的部署、single→HA、CSI 和存储验收链路。

---

## 1. 验证范围

当前建议分三类验证：

```text
1. 全新 HA 部署验证
2. single → HA 升级验证
3. CSI / Storage 验证
```

---

## 2. 前置条件

所有节点需要满足：

```text
Linux + systemd
root SSH 可登录
固定 IP
节点之间网络互通
时间同步
已确认网卡名
已确认 VIP 不冲突
```

裸金属还需要额外确认：

```text
磁盘用途
存储网卡
是否存在 RAID / HBA / multipath
不要误格式化系统盘
```

---

## 3. 全新 HA 部署验证

编辑：

```text
inventories/hosts-ha.yml
```

确认：

```text
master IP
worker IP
VIP
LB_INTERFACE
MASTER_CERT_HOSTS
SERVICE_CIDR
CLUSTER_CIDR
```

执行语法检查：

```bash
make syntax-check-ha
```

执行部署：

```bash
make deploy-ha
```

离线部署：

```bash
make deploy-ha-offline
```

部署后验证：

```bash
make smoke-test KUBECONFIG_PATH=/root/.ssl_build/kubeconfig/admin.kubeconfig
```

---

## 4. single → HA 升级验证

编辑：

```text
inventories/hosts-ha-from-single.yml
```

先执行：

```bash
make syntax-check-single-to-ha
```

按阶段执行：

```bash
make migrate-single-to-ha-preflight CONFIRM_SINGLE_TO_HA=true
make migrate-single-to-ha-backup CONFIRM_SINGLE_TO_HA=true
make migrate-single-to-ha-etcd-preflight CONFIRM_SINGLE_TO_HA=true
make migrate-single-to-ha-expand-etcd CONFIRM_SINGLE_TO_HA=true CONFIRM_EXPAND_ETCD=true
make migrate-single-to-ha-renew-apiserver-cert CONFIRM_SINGLE_TO_HA=true CONFIRM_RENEW_APISERVER_CERT=true
make migrate-single-to-ha-expand-control-plane CONFIRM_SINGLE_TO_HA=true CONFIRM_EXPAND_CONTROL_PLANE=true
make migrate-single-to-ha-enable-ha-lb CONFIRM_SINGLE_TO_HA=true CONFIRM_ENABLE_HA_LB=true
make migrate-single-to-ha-switch-kubeconfigs-to-vip CONFIRM_SINGLE_TO_HA=true CONFIRM_SWITCH_KUBECONFIGS_TO_VIP=true
```

---

## 5. CSI / Storage 验证

配置：

```text
storage_backend
storage_default_class
```

建议先验证：

```text
local-lvm 或 nfs
```

执行：

```bash
make storage-preflight INVENTORY=inventories/hosts-ha.yml
make install-csi INVENTORY=inventories/hosts-ha.yml
make storage-health-check INVENTORY=inventories/hosts-ha.yml
make storage-pvc-validate INVENTORY=inventories/hosts-ha.yml
make storage-migration-check INVENTORY=inventories/hosts-ha.yml
```

---

## 6. PVC 验证保留现场

默认会清理测试 namespace。

如需保留现场：

```bash
ansible-playbook -i inventories/hosts-ha.yml 0063-storage-pvc-validate.yml \
  -e storage_validate_cleanup=false
```

验证扩容：

```bash
ansible-playbook -i inventories/hosts-ha.yml 0063-storage-pvc-validate.yml \
  -e storage_validate_expand=true \
  -e storage_validate_expand_size=2Gi
```

---

## 7. 验收标准

基础集群：

```text
kubectl get nodes 全部 Ready
kubectl get pods -A 无异常 CrashLoopBackOff
VIP /readyz 正常
```

存储：

```text
StorageClass 存在
PVC 可以 Bound
测试 Pod 可以挂载 PVC
测试 Pod 可以写入文件
storage-health-check 无关键错误
```

---

## 8. 常见失败点

```text
LB_INTERFACE 不正确
VIP 网络不支持 gratuitous ARP
MASTER_CERT_HOSTS 缺少 VIP
节点时间不同步
CNI 未 Ready
本地 VG 不存在
NFS server/path 不可达
iSCSI portal/CHAP/multipath 未就绪
Rook Ceph OSD 磁盘未规划
```

---

## 9. 建议验证顺序

```text
1. syntax-check
2. deploy-single 或 deploy-ha
3. smoke-test
4. storage-preflight
5. install-csi
6. storage-health-check
7. storage-pvc-validate
8. storage-migration-check
```
