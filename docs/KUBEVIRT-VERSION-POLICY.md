# KubeVirt 版本策略（V1）

## 1. 目标

KubeVirt 属于可选虚拟化扩展能力，涉及：

```text
Kubernetes API
CRD
virt-operator
virt-api
virt-controller
virt-handler
CDI
CSI
CNI
KVM
```

因此版本必须显式管理，不能使用隐式 latest。

---

## 2. 当前默认版本

当前项目默认 pinned 版本：

```yaml
kubevirt_version: v1.8.2
kubevirt_version_policy: pinned
kubevirt_allow_prerelease: false
```

说明：

```text
v1.8.2 是当前项目的默认验证基线。
生产环境仍必须结合 Kubernetes / CSI / CNI / OS / 内核版本完成兼容性验证后再启用。
```

---

## 3. 版本选择原则

必须遵循：

```text
1. 禁止使用 latest
2. 禁止默认使用 alpha / beta / rc
3. 必须使用明确的 pinned 版本
4. KubeVirt 与 CDI 版本必须组合验证
5. KubeVirt 与 Kubernetes 版本必须组合验证
6. KubeVirt 与 CSI / CNI 必须组合验证
```

---

## 4. 预发布版本策略

默认：

```yaml
kubevirt_allow_prerelease: false
```

禁止默认使用：

```text
alpha
beta
rc
pre-release
```

如果实验环境需要验证预发布版本，必须显式设置：

```yaml
kubevirt_allow_prerelease: true
```

并且不得作为生产默认值提交。

---

## 5. 推荐升级流程

升级 KubeVirt 版本时，必须按以下顺序执行：

```text
1. 修改 kubevirt_version
2. 修改 kubevirt_operator_url / kubevirt_cr_url 或离线 manifest
3. 执行 syntax-check
4. 执行 kubevirt-preflight
5. 执行 install-kubevirt
6. 执行 kubevirt-health-check
7. 执行 kubevirt-smoke-test
8. 如果启用 CDI，执行 install-kubevirt-cdi
9. 如果启用 PVC-backed VM，执行 kubevirt-datavolume-smoke-test
10. 记录验证结果
```

---

## 6. 与 CDI 的关系

CDI 版本独立配置：

```yaml
kubevirt_cdi_version: v1.60.0
```

CDI 不应盲目跟随 KubeVirt 自动升级。

原因：

```text
DataVolume
image import
PVC clone
uploadproxy
storage profile
```

都依赖 CDI 自身 CRD 与 controller 行为。

---

## 7. 与存储的关系

KubeVirt 生产 VM 推荐使用：

```text
rook-ceph RBD
iscsi-san
```

测试/边缘场景可以使用：

```text
local-lvm
nfs
```

但需要明确风险：

```text
local-lvm 不支持跨节点漂移
NFS 不适合高 IO VM
```

---

## 8. 与 single-to-HA 的关系

建议顺序：

```text
1. 完成 Kubernetes 基础部署
2. 完成 single-to-HA 或 HA 部署
3. 完成 CSI 存储部署
4. 完成 KubeVirt 部署
5. 完成 CDI / DataVolume 验证
```

不建议在 control-plane 迁移过程中升级或安装 KubeVirt。

---

## 9. 回滚原则

升级失败时：

```text
1. 不删除业务 VM PVC
2. 不删除 DataVolume 产生的 PVC
3. 先保留 KubeVirt CRD 状态
4. 先导出 VM / VMI / PVC / DataVolume 状态
5. 再执行回滚或版本修复
```

---

## 10. 后续规划

后续可以增加：

```text
KubeVirt compatibility matrix
KubeVirt upgrade playbook
KubeVirt rollback playbook
KubeVirt release validation CI
```
