# 存算分离与多存储多计算架构共存设计（V1）

## 1. 目标

本文档设计一套适用于本项目的存算分离架构，使同一套 Kubernetes 平台能够同时支持：

```text
多种计算资源池
多种存储资源池
容器 workload
虚拟机 workload
StatefulSet
边缘节点
企业 SAN
云原生分布式存储
```

最终目标：

```text
计算资源可弹性扩展
存储资源可独立演进
不同业务按需绑定不同计算池和存储池
```

---

## 2. 设计原则

核心原则：

```text
存储与计算解耦
计算池可分层
存储池可分级
调度策略显式化
StorageClass 显式选择
NodePool 显式选择
KubeVirt VM 与容器共享统一资源模型
```

禁止：

```text
把所有节点混成一个无差别资源池
把所有业务都绑定到 default StorageClass
让生产 VM 随机落到不具备 /dev/kvm 的节点
让数据库随机使用低性能 NFS
```

---

## 3. 总体架构

推荐架构：

```text
                   ┌──────────────────────────┐
                   │ Kubernetes Control Plane │
                   └─────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
      ┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
      │ Compute Pool  │  │ VM Pool       │  │ Storage Pool   │
      │ container     │  │ kubevirt/kvm  │  │ ceph/iscsi/nfs │
      └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                          ┌──────▼──────┐
                          │ CSI / CNI   │
                          └─────────────┘
```

抽象成三层：

```text
控制面：etcd / kube-apiserver / scheduler / controller
计算面：container pool / vm pool / gpu pool / edge pool
存储面：local-lvm / nfs / iscsi-san / rook-ceph
```

---

## 4. 计算资源池设计

### 4.1 control-plane pool

用途：

```text
etcd
kube-apiserver
kube-controller-manager
kube-scheduler
VIP / keepalived / nginx
```

标签建议：

```yaml
node-role.kubernetes.io/control-plane: ""
k8s.io/node-pool: control-plane
```

原则：

```text
不承载普通业务
不承载 KubeVirt VM
不承载 Ceph OSD，除非是小规模测试环境
```

---

### 4.2 container compute pool

用途：

```text
普通容器业务
无状态服务
轻量 StatefulSet
Ingress
中间件
```

标签建议：

```yaml
k8s.io/node-pool: compute
k8s.io/workload-type: container
```

污点建议：

```yaml
dedicated=compute:NoSchedule
```

适合绑定：

```text
nfs-csi
cephfs
ceph-rbd
iscsi-san
```

---

### 4.3 vm compute pool

用途：

```text
KubeVirt VM
传统应用迁移
数据库虚拟机
Windows/Linux VM
```

节点要求：

```text
/dev/kvm
CPU virtualization flags: vmx/svm
足够内存
稳定网络
可访问 VM StorageClass
```

标签建议：

```yaml
k8s.io/node-pool: vm
kubevirt.io/kvm: "true"
k8s.io/workload-type: vm
```

污点建议：

```yaml
dedicated=vm:NoSchedule
```

适合绑定：

```text
ceph-rbd
iscsi-san
local-lvm（仅单节点/边缘）
```

不建议：

```text
高 IO VM 使用 NFS
生产 VM 使用无 HA 的 local-lvm
```

---

### 4.4 storage pool

用途：

```text
Rook Ceph OSD
NFS Server
iSCSI target gateway
存储网关
```

标签建议：

```yaml
k8s.io/node-pool: storage
k8s.io/workload-type: storage
```

污点建议：

```yaml
dedicated=storage:NoSchedule
```

原则：

```text
存储节点优先承载存储组件
不建议混跑普通业务
生产 Ceph OSD 必须使用独立数据盘
```

---

### 4.5 gpu / ai compute pool

用途：

```text
AI 推理
训练任务
GPU VM
高性能计算
```

标签建议：

```yaml
k8s.io/node-pool: gpu
accelerator: nvidia
k8s.io/workload-type: ai
```

适合绑定：

```text
cephfs
ceph-rbd
高速对象存储
```

后续可扩展：

```text
GPU passthrough
SR-IOV
RDMA
```

---

### 4.6 edge pool

用途：

```text
边缘节点
单节点业务
本地数据采集
轻量 VM
```

标签建议：

```yaml
k8s.io/node-pool: edge
k8s.io/workload-type: edge
```

适合绑定：

```text
local-lvm
nfs
```

说明：

```text
edge pool 可以接受较弱 HA，但必须明确故障域和数据风险
```

---

## 5. 存储资源池设计

### 5.1 local-lvm pool

定位：

```text
单节点高性能本地盘
边缘场景
开发测试
```

StorageClass：

```text
local-lvm
```

特点：

```text
性能高
成本低
不支持跨节点漂移
强绑定节点
```

适合：

```text
单节点 VM
边缘 StatefulSet
临时高性能测试
```

不适合：

```text
生产 HA 数据库
跨节点迁移 VM
```

---

### 5.2 NFS pool

定位：

```text
低成本共享文件
轻量 RWX
日志/配置/共享目录
```

StorageClass：

```text
nfs-csi
```

适合：

```text
共享配置
低 IO 文件
轻量 workload
```

不适合：

```text
高 IO 数据库
高并发 VM 磁盘
核心生产块存储
```

---

### 5.3 iSCSI SAN pool

定位：

```text
企业已有 SAN
集中式块存储
数据库与 VM 磁盘
```

StorageClass：

```text
iscsi-san
```

要求：

```text
multipath
CHAP
双 portal
独立存储网络
厂商 CSI 优先
```

适合：

```text
数据库
KubeVirt VM root/data disk
企业 StatefulSet
```

---

### 5.4 Rook Ceph pool

定位：

```text
云原生分布式存储
多副本块存储
共享文件存储
```

StorageClass：

```text
ceph-rbd
ceph-rbd-retain
cephfs
```

适合：

```text
KubeVirt VM
数据库
StatefulSet
AI 数据集共享
```

要求：

```text
至少 3 节点
独立数据盘
10GbE+
replica=3
```

---

## 6. 多存储共存策略

同一集群内允许多个 StorageClass 共存：

```text
local-lvm
nfs-csi
iscsi-san
ceph-rbd
ceph-rbd-retain
cephfs
```

推荐：

```text
默认 StorageClass 只给通用业务
关键业务必须显式指定 StorageClass
数据库优先使用 Retain class
VM 优先使用 ceph-rbd 或 iscsi-san
共享文件使用 cephfs 或 nfs-csi
```

不建议：

```text
所有 PVC 不写 storageClassName
所有业务依赖 default StorageClass
频繁切换 default StorageClass
```

---

## 7. 多计算共存策略

同一集群中允许多个计算池共存：

```text
control-plane
compute
vm
storage
gpu
edge
```

通过以下机制隔离：

```text
node labels
taints / tolerations
nodeSelector
nodeAffinity
topologySpreadConstraints
ResourceQuota
LimitRange
PriorityClass
```

推荐规则：

```text
容器业务默认进入 compute pool
VM 业务进入 vm pool
存储组件进入 storage pool
GPU 业务进入 gpu pool
边缘业务进入 edge pool
```

---

## 8. Workload 绑定模型

### 8.1 容器业务绑定 compute pool

示例：

```yaml
nodeSelector:
  k8s.io/node-pool: compute
```

PVC：

```yaml
storageClassName: ceph-rbd
```

---

### 8.2 VM 业务绑定 vm pool

示例：

```yaml
nodeSelector:
  k8s.io/node-pool: vm
```

VM 磁盘：

```yaml
storageClassName: ceph-rbd
```

或：

```yaml
storageClassName: iscsi-san
```

---

### 8.3 存储组件绑定 storage pool

示例：

```yaml
nodeSelector:
  k8s.io/node-pool: storage
```

用于：

```text
rook-ceph-osd
nfs provisioner
iSCSI gateway
```

---

## 9. 推荐资源组合

### 9.1 最小验证组合

```text
1 control-plane / worker 合一节点
local-lvm
KubeVirt optional
```

适合：

```text
开发测试
功能验证
```

---

### 9.2 小型 HA 组合

```text
3 control-plane/worker 混合节点
NFS 或 local-lvm
可选 KubeVirt
```

适合：

```text
小型内网
PoC
非核心业务
```

---

### 9.3 企业 SAN 组合

```text
3 control-plane
N worker
企业 SAN
iSCSI CSI
KubeVirt VM pool
```

适合：

```text
已有 SAN 的企业
数据库
传统 VM 迁移
```

---

### 9.4 云原生生产组合

```text
3 control-plane
3+ compute
3+ storage
Rook Ceph
KubeVirt + CDI
```

适合：

```text
企业 Kubernetes 平台
容器 + VM 混合负载
生产 StatefulSet
```

---

## 10. 调度与隔离规范

必须引入统一标签：

```yaml
k8s.io/node-pool: control-plane|compute|vm|storage|gpu|edge
k8s.io/workload-type: container|vm|storage|ai|edge
```

建议引入统一污点：

```yaml
dedicated=vm:NoSchedule
dedicated=storage:NoSchedule
dedicated=gpu:NoSchedule
```

业务必须通过：

```text
nodeSelector
nodeAffinity
tolerations
```

显式进入目标资源池。

---

## 11. 故障域设计

必须考虑：

```text
节点故障域
机架故障域
存储故障域
网络故障域
可用区故障域
```

建议标签：

```yaml
topology.kubernetes.io/zone: zone-a
topology.kubernetes.io/rack: rack-01
storage.k8s.io/failure-domain: fd-01
```

Ceph / VM / StatefulSet 应避免集中在单一故障域。

---

## 12. 网络分离设计

建议网络分层：

```text
管理网络
业务网络
存储网络
VM 网络
迁移网络
```

最低要求：

```text
管理网络与存储网络逻辑隔离
```

生产建议：

```text
存储网络独立 VLAN
VM 网络独立 VLAN
Ceph 使用 10/25GbE
VM LiveMigration 预留独立网络
```

---

## 13. 与 KubeVirt 的关系

KubeVirt 在存算分离中属于：

```text
计算层扩展
```

VM 数据盘属于：

```text
存储层资源
```

推荐绑定：

```text
VM compute pool + ceph-rbd
VM compute pool + iscsi-san
```

不推荐：

```text
VM 随机调度到 compute pool
VM 使用 default StorageClass
VM 数据盘使用低性能 NFS
```

---

## 14. 与 CDI / DataVolume 的关系

CDI 用于：

```text
镜像导入
DataVolume
PVC-backed VM
```

CDI 强依赖：

```text
可动态 provision 的 StorageClass
足够网络带宽
足够临时空间
```

建议：

```text
镜像导入使用独立 StorageClass
大镜像导入使用 ceph-rbd 或 iscsi-san
```

---

## 15. 与 single-to-HA 的关系

推荐演进顺序：

```text
single Kubernetes
→ HA control-plane
→ CSI 存储池
→ 计算池标签化
→ KubeVirt VM pool
→ CDI / DataVolume
→ 多池调度策略
```

不建议：

```text
在 control-plane 迁移期间同时调整存储池与 VM 池
```

---

## 16. Inventory 设计建议

后续建议新增：

```text
inventories/group_vars/node_pools.yml
```

示例：

```yaml
node_pools_enabled: true

node_pools:
  control-plane:
    selector: "k8s.io/node-pool=control-plane"
  compute:
    selector: "k8s.io/node-pool=compute"
  vm:
    selector: "k8s.io/node-pool=vm"
    require_kvm: true
  storage:
    selector: "k8s.io/node-pool=storage"
  gpu:
    selector: "k8s.io/node-pool=gpu"
  edge:
    selector: "k8s.io/node-pool=edge"
```

存储池建议：

```yaml
storage_pools:
  local:
    storage_class: local-lvm
    type: local
  nfs:
    storage_class: nfs-csi
    type: file
  san:
    storage_class: iscsi-san
    type: block
  ceph-rbd:
    storage_class: ceph-rbd
    type: block
  cephfs:
    storage_class: cephfs
    type: file
```

---

## 17. Playbook 设计建议

后续建议新增：

```text
0071-node-pool-labels.yml
0072-node-pool-health-check.yml
0073-storage-pool-health-check.yml
0074-scheduling-policy-check.yml
```

职责：

```text
节点池标签初始化
节点池 taint 初始化
计算池健康检查
存储池健康检查
调度策略检查
```

---

## 18. 推荐落地顺序

建议按以下顺序落地：

```text
1. 文档设计
2. node_pools inventory
3. node pool label/taint playbook
4. storage pool inventory
5. scheduling policy check
6. KubeVirt VM pool 绑定
7. Ceph / iSCSI StorageClass 绑定
8. 多池健康检查
```

不要一开始就自动修改所有节点标签和污点。

---

## 19. 风险与边界

主要风险：

```text
错误 taint 导致业务无法调度
错误 default StorageClass 导致数据落错存储
VM 调度到无 KVM 节点
Ceph OSD 与业务争抢 IO
NFS 承载高 IO VM 导致性能抖动
```

必须避免：

```text
无标签资源池
无显式 StorageClass
无故障域规划
无存储健康检查
无调度策略检查
```

---

## 20. 最终目标

最终形成：

```text
多计算池：control-plane / compute / vm / storage / gpu / edge
多存储池：local-lvm / nfs / iscsi-san / ceph-rbd / cephfs
统一调度：nodeSelector / taints / affinity
统一验证：health-check / smoke-test / migration-check
统一运维：VM ops / CSI ops / storage ops
```

最终平台能力：

```text
容器 + 虚拟机 + StatefulSet + 多存储后端
在同一 Kubernetes 平台内安全共存
```
