# KubeVirt 可选虚拟化扩展设计（V1）

## 1. 目标

在当前 Kubernetes 裸机/HA 交付体系之上，提供可选的 KubeVirt 虚拟机管理能力。

目标能力：

```text
Kubernetes 集群
  ↓
可选 KubeVirt 扩展
  ↓
VirtualMachine / VirtualMachineInstance
  ↓
虚拟机生命周期管理
```

该能力默认关闭，不影响基础 Kubernetes、CSI、single→HA 迁移链路。

---

## 2. 设计原则

KubeVirt 必须作为可选扩展，不进入基础安装默认路径。

原则：

```text
默认不安装
显式开启
先 preflight
依赖 CSI
依赖硬件虚拟化
可独立卸载
```

不做的事情：

```text
不自研虚拟化引擎
不替代 KubeVirt
不直接管理 libvirt
不在 container CI 模式中强制验证硬件虚拟化
```

---

## 3. 与现有项目关系

当前项目已经具备：

```text
HA Kubernetes
CSI 存储框架
storage-preflight
single→HA 迁移
```

KubeVirt 位于更上层：

```text
基础 Kubernetes
  ↓
CNI
  ↓
CSI
  ↓
KubeVirt
  ↓
VM workload
```

安装顺序建议：

```text
1. Kubernetes control plane
2. CNI
3. CSI
4. StorageClass
5. storage health-check
6. KubeVirt preflight
7. KubeVirt install
8. VM smoke test
```

---

## 4. 适用场景

适合：

```text
虚拟机托管
传统应用迁移
轻量私有云
HCI 场景
开发测试 VM
边缘虚拟化
```

不适合：

```text
纯容器场景
无硬件虚拟化节点
没有可靠持久化存储的生产 VM
```

---

## 5. 节点要求

物理机/虚拟机节点必须满足：

```text
CPU 支持 Intel VT-x 或 AMD-V
/dev/kvm 存在
kvm 模块加载
节点可调度
容器运行时正常
```

检查命令：

```bash
ls -l /dev/kvm
lsmod | grep kvm
```

如果运行在嵌套虚拟化中，需要宿主机开启 nested virtualization。

---

## 6. 存储要求

KubeVirt VM 强依赖持久化存储。

推荐后端：

```text
rook-ceph / ceph-rbd
iscsi-san
local-lvm
```

轻量测试可使用：

```text
nfs-csi
```

生产建议：

```text
ceph-rbd-retain
iscsi-san-retain
```

原因：

```text
VM 磁盘应默认 Retain
避免误删 VM 后磁盘立即丢失
```

---

## 7. 网络要求

基础 KubeVirt 可复用 Kubernetes Pod 网络。

高级网络后续扩展：

```text
Multus
Bridge
SR-IOV
VLAN
静态 IP
```

V1 先支持默认 Pod 网络。

---

## 8. Inventory 设计

新增变量：

```yaml
kubevirt_enabled: false
kubevirt_version: v1.3.1
kubevirt_namespace: kubevirt
kubevirt_operator_url: ""
kubevirt_cr_url: ""

kubevirt_require_kvm: true
kubevirt_validate_storage: true
kubevirt_default_storage_class: ""
kubevirt_enable_cdi: true
kubevirt_cdi_version: v1.60.0
kubevirt_enable_vm_smoke_test: false
```

默认：

```yaml
kubevirt_enabled: false
```

---

## 9. Playbook 设计

新增：

```text
0063-kubevirt-preflight.yml
0064-install-kubevirt.yml
0065-kubevirt-health-check.yml
0066-kubevirt-smoke-test.yml
```

其中：

```text
0063 只检查，不修改
0064 安装 KubeVirt/CDI
0065 健康检查
0066 可选创建测试 VM
```

---

## 10. Role 设计

新增：

```text
roles/kubevirt_preflight
roles/kubevirt
roles/kubevirt_health
```

职责：

```text
kubevirt_preflight:
  - 检查 /dev/kvm
  - 检查 kvm 模块
  - 检查 StorageClass
  - 检查节点可调度

kubevirt:
  - 安装 KubeVirt operator
  - 安装 KubeVirt CR
  - 可选安装 CDI

kubevirt_health:
  - 检查 kubevirt namespace
  - 检查 virt-operator
  - 检查 virt-api
  - 检查 virt-controller
  - 检查 virt-handler
  - 检查 kubevirt CR 状态
```

---

## 11. CDI

CDI 用于 VM 镜像导入、上传和 DataVolume。

默认建议开启：

```yaml
kubevirt_enable_cdi: true
```

支持后续：

```text
HTTP image import
PVC clone
upload proxy
DataVolume
```

---

## 12. 安装边界

KubeVirt 安装必须显式执行：

```bash
make kubevirt-install KUBEVIRT_ENABLED=true
```

不进入：

```text
deploy-single
deploy-container
deploy HA
single-to-ha
```

---

## 13. 健康检查

必须检查：

```bash
kubectl get kubevirt -n kubevirt
kubectl get pods -n kubevirt
kubectl get apiservices | grep kubevirt
kubectl get crd | grep kubevirt
```

预期：

```text
virt-api Running
virt-controller Running
virt-handler Running on VM-capable nodes
KubeVirt Available
```

---

## 14. VM Smoke Test

V1 smoke test 可选关闭。

后续可创建：

```text
VirtualMachine
DataVolume
PVC-backed disk
cloud-init disk
```

默认不创建测试 VM，避免在生产集群中产生资源。

---

## 15. 企业级后续规划

后续增强：

```text
Multus 网络
VM 模板
Windows VM
Cloud-init
Live Migration
VM Snapshot
VM Backup
镜像仓库
VNC/Console
RBAC 多租户
```

---

## 16. 最终目标

形成：

```text
Kubernetes + CSI + KubeVirt
```

最终能力：

```text
容器 + 虚拟机统一调度
企业级轻量 HCI
传统应用平滑迁移
```
