# 组件版本矩阵

本文档记录当前默认组件版本。版本的单一事实来源应以 `inventories/group_vars/all.yml` 为准，本文档用于 review 和发布说明。

| 组件 | 当前默认版本 | 变量名 | 说明 |
|------|--------------|--------|------|
| Kubernetes | 1.36.1 | `kubernetes_version` | 控制面、kubelet、kubectl、kube-proxy 镜像版本 |
| etcd | 3.6.11 | `etcd_version` | etcd 二进制版本 |
| Containerd | 2.3.0 | `containerd_version` | CRI 运行时版本 |
| runc | 1.3.5 | `runc_version` | OCI runtime 版本 |
| CNI Plugins | 1.9.1 | `cni_plugins_version` | CNI 基础插件版本 |
| Calico | 3.32.0 | `calico_version` | Calico manifest 版本 |
| CoreDNS | 1.14.3 | `coredns_version` | CoreDNS 镜像版本 |
| cfssl | 1.6.5 | `cfssl_version` | 本地证书签发工具版本 |

## 维护规则

- 修改组件版本时，优先修改 `inventories/group_vars/all.yml`。
- 同步更新本文档和 README 中的版本表。
- 版本升级必须至少通过 Ansible syntax check。
- 涉及 Kubernetes、etcd、containerd、CNI、Calico 的升级，应执行 container 模式 smoke test。
- 后续应为所有二进制下载补充 checksum，避免供应链风险。

## 待验证事项

当前版本矩阵需要在真实下载和容器模式部署中验证 URL 可用性、组件兼容性和启动行为。未完成验证前，不应宣称该版本矩阵已生产验证。
