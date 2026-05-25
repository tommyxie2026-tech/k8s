# 高可用 Kubernetes 二进制部署

基于 Ansible 的 Kubernetes 高可用集群二进制部署方案，支持 HA 物理机/虚拟机、单节点物理机，以及用于开发、CI、演示的 Docker 容器模式。

> 当前项目正在按 `docs/ROADMAP.md` 逐步生产化。容器模式仅用于开发、CI 和演示，不作为生产运行形态；单节点物理机模式不提供高可用能力。

## 部署模式

| 模式 | `node_type` | 定位 | Inventory |
|------|-------------|------|-----------|
| 物理机 / 虚拟机 HA | `machine` | 主部署路径，执行完整宿主级系统配置，支持多 master / 多 etcd | `inventories/hosts.yml` |
| 单节点物理机 | `machine` + `cluster_mode=single` | PoC、边缘、小型离线单机，不提供 HA | `inventories/hosts-single.yml` |
| 容器 | `container` | 开发 / CI / 演示环境 | `inventories/hosts-container.yml` |

容器模式下，每个节点是一个运行 systemd 的 Docker 容器，Ansible 通过 Docker API 管理，无需 SSH。单节点物理机模式下，同一台机器同时承担 etcd、control plane 与 worker 角色。

## 架构概览

- HA 入口：Nginx 4 层 stream 代理 + Keepalived VIP 漂移
- 单节点入口：Nginx 本地代理，跳过 Keepalived
- etcd：HA 模式独立多节点，单节点模式本机单 member
- PKI：cfssl 签发，含 front-proxy CA 支持 API 聚合层
- 网络：Calico + kube-proxy DaemonSet
- 运行时：containerd + runc
- 安全增强：apiserver 默认关闭匿名访问和 profiling，支持 Secret 静态加密配置

## 前置要求

### 物理机 / 虚拟机模式

- 控制机：macOS / Linux，Ansible >= 2.9
- 目标节点：Ubuntu 20.04+ / CentOS 7+，SSH 免密可登录
- 网络互通：控制机可 SSH 到所有节点，节点之间互通
- 生产环境需提前确认 IP、VIP、网卡、CIDR、DNS、时间同步和端口占用

### 容器模式

- 控制机：Docker + Ansible >= 2.9
- 安装 collection：`ansible-galaxy collection install -r requirements.yml`
- 不需要 SSH，不需要目标节点预装软件

## 常用命令

项目提供 `Makefile` 作为常用入口：

```bash
make syntax-check
make syntax-check-single
make preflight-container
make deploy-container
make deploy-single
make smoke-test
make cleanup-container
```

也可以直接使用 playbook。

## 推荐部署流程

### 物理机 / 虚拟机 HA 部署

```bash
INV="-i inventories/hosts.yml"

ansible-playbook $INV 0000-preflight.yml
ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0003-encryption-config.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0020-create-compute-set.yml
ansible-playbook $INV 0030-install-cni.yml
```

### 单节点物理机部署

```bash
make deploy-single
```

或手动执行：

```bash
INV="-i inventories/hosts-single.yml"

ansible-playbook $INV 0000-preflight.yml
ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0003-encryption-config.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0030-install-cni.yml
ansible-playbook $INV 0031-single-node-post.yml
```

### 容器模式部署

```bash
INV="-i inventories/hosts-container.yml"

ansible-playbook $INV 0000-container-infra.yml
ansible-playbook $INV 0000-preflight.yml
ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0003-encryption-config.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0020-create-compute-set.yml
ansible-playbook $INV 0030-install-cni.yml
```

部署完成后可执行：

```bash
KUBECONFIG_PATH=/root/.kube/config make smoke-test
```

## 运维 Playbooks

| Playbook | 作用 | 风险级别 |
|----------|------|----------|
| `0000-preflight.yml` | 部署前检查控制机、节点、端口、网络变量 | 低 |
| `0003-encryption-config.yml` | 生成并分发 kube-apiserver Secret 静态加密配置 | 中 |
| `0031-single-node-post.yml` | 单节点部署后处理，移除控制面 taint 并等待 Ready | 中，仅单节点 |
| `0040-etcd-snapshot.yml` | 生成 etcd snapshot 并校验状态 | 中 |
| `0400-cert-expiry-check.yml` | 检查本地组件证书有效期，不修改文件 | 低 |
| `0401-renew-component-certs.yml` | 归档并重新生成本地组件证书与 kubeconfig，需显式确认 | 高 |
| `0090-stop-services.yml` | 停止 Kubernetes / etcd / LB 服务，不删除数据 | 中 |
| `0091-reset-node-runtime.yml` | 清理 kubelet / CNI / containerd 运行态，需显式确认 | 高 |
| `0099-container-cleanup.yml` | 删除容器实验节点和 Docker 网络 | 高，仅容器模式 |

`0091-reset-node-runtime.yml` 默认拒绝执行，必须显式传入：

```bash
ansible-playbook -i inventories/hosts.yml 0091-reset-node-runtime.yml -e confirm_reset_node_runtime=true
```

`0401-renew-component-certs.yml` 默认拒绝执行，必须显式传入：

```bash
ansible-playbook -i inventories/hosts.yml 0401-renew-component-certs.yml -e confirm_renew_component_certs=true
```

## 目录结构

```text
.
├── ansible.cfg
├── requirements.yml
├── Makefile
├── Dockerfile
├── inventories/
│   ├── hosts.yml
│   ├── hosts-single.yml
│   ├── hosts-container.yml
│   └── group_vars/all.yml
├── roles/
│   ├── download/
│   ├── container-infra/
│   ├── common/
│   ├── encryption-config/
│   ├── kubeconfig/
│   ├── lb/
│   ├── etcd/
│   ├── kube_master/
│   ├── kubelet/
│   ├── kube-proxy/
│   └── cni/
├── scripts/
│   ├── syntax-check.sh
│   ├── smoke-test.sh
│   ├── download-default-binaries.sh
│   └── sync-binary-cache-branch.sh
├── docs/
│   ├── ROADMAP.md
│   ├── OPERATIONS.md
│   ├── SECURITY-HARDENING.md
│   ├── VERSION-MATRIX.md
│   ├── SINGLE-NODE.md
│   ├── BINARY-CACHE.md
│   ├── MACHINE-RESET.md
│   └── ETCD-BACKUP-RESTORE.md
├── 0000-container-infra.yml
├── 0000-preflight.yml
├── 0001-download-binaries.yml
├── 0000-common-service.yml
├── 0002-common-kubeconfig.yml
├── 0003-encryption-config.yml
├── 0005-install-lb.yml
├── 0010-create-manager-set.yml
├── 0012-manager-set-kube.yml
├── 0020-create-compute-set.yml
├── 0030-install-cni.yml
├── 0031-single-node-post.yml
├── 0040-etcd-snapshot.yml
├── 0400-cert-expiry-check.yml
├── 0401-renew-component-certs.yml
├── 0090-stop-services.yml
├── 0091-reset-node-runtime.yml
└── 0099-container-cleanup.yml
```

## 组件版本

版本以 `inventories/group_vars/all.yml` 为单一事实来源，详见 `docs/VERSION-MATRIX.md`。

| 组件 | 当前默认版本 |
|------|--------------|
| Kubernetes | 1.36.1 |
| etcd | 3.6.11 |
| Containerd | 2.3.0 |
| runc | 1.3.5 |
| CNI Plugins | 1.9.1 |
| Calico | 3.32.0 |
| CoreDNS | 1.14.3 |
| cfssl | 1.6.5 |

## 安全边界

- 容器模式不内置 SSH，也不允许 root 免密 SSH。
- 单节点物理机模式不提供 HA，也不提供 etcd quorum 容错。
- 生成的证书、私钥、kubeconfig、二进制缓存会被 `.gitignore` 忽略。
- CA 私钥离线化仍作为 P0 待办记录在 `docs/SECURITY-HARDENING.md`，当前不在本轮修改范围内。
- Secret 静态加密能力由 `0003-encryption-config.yml` 生成配置，并由 apiserver `--encryption-provider-config` 启用。
- 证书续期入口默认拒绝执行，必须显式确认。
- 破坏性 reset 操作默认拒绝执行，必须显式确认。

## 下载与供应链校验

下载任务支持：

- `download_timeout`
- `download_retries`
- `download_retry_delay`
- `download_checksums`

可在 inventory 或 extra-vars 中设置 checksum，例如：

```yaml
download_checksums:
  kubectl: "sha256:<digest>"
  etcd: "sha256:<digest>"
```

未设置 checksum 时仍可下载，但不会执行强校验。默认二进制缓存可通过 `docs/BINARY-CACHE.md` 中的独立缓存分支流程同步。

## 离线部署

1. 在联网环境执行 `0001-download-binaries.yml`，将二进制下载到 `files/<arch>/`。
2. 或从 `binary-cache/<arch>` 分支同步默认二进制缓存。
3. 将整个项目目录拷贝到离线环境。
4. 离线环境按推荐部署流程执行。

容器模式还需提前准备 kube-proxy、CoreDNS、Calico、pause 等镜像。

## 故障排查

- etcd 健康检查失败：确认 etcd 证书路径、2379/2380 端口和节点网络。
- APIServer 未就绪：检查 Nginx、VIP、etcd endpoint、审计策略和 encryption config。
- 节点 NotReady：检查 Calico、CNI 二进制、kube-proxy DaemonSet 和 kubelet 日志。
- 单节点无法调度业务 Pod：确认 `0031-single-node-post.yml` 已执行，并检查 control-plane / master taint。
- 证书签发失败：检查 `local_cluster_config_dir` 权限和 cfssl/kubectl 是否可执行。
- 容器模式连接失败：确认 Docker daemon 运行中且已安装 `community.docker`。

## 更多文档

- `docs/ROADMAP.md`：阶段性完善计划
- `docs/OPERATIONS.md`：部署与运维执行规范
- `docs/SECURITY-HARDENING.md`：安全加固待办
- `docs/VERSION-MATRIX.md`：组件版本矩阵
- `docs/SINGLE-NODE.md`：单节点物理机模式
- `docs/BINARY-CACHE.md`：默认二进制缓存
- `docs/MACHINE-RESET.md`：机器模式 reset 设计
- `docs/ETCD-BACKUP-RESTORE.md`：etcd 备份与恢复
