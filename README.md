# 高可用 Kubernetes 二进制部署

基于 Ansible 的生产级 Kubernetes 高可用集群二进制部署方案。同时支持**物理机、虚拟机、容器**三种部署目标。

## 部署模式

| 模式 | `node_type` | 说明 | Inventory |
|------|-------------|------|-----------|
| 物理机 / 虚拟机 | `machine` (默认) | 标准生产部署，完整内核/网络控制 | `hosts.yml` |
| 容器 | `container` | Docker 容器节点，用于开发/CI | `hosts-container.yml` |

容器模式下，每个"节点"是一个运行 systemd 的 Docker 容器，Ansible 通过 Docker API 连接管理。同一套 playbooks 和 roles 自动适配。

## 架构概览

### 物理机 / 虚拟机模式

```
                    ┌──────────────┐
                    │   VIP        │
                    │ 192.168.1.100│
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
     ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
     │ master-01 │   │ master-02 │   │ master-03 │
     │   Nginx   │   │   Nginx   │   │   Nginx   │
     │ Keepalived│   │ Keepalived│   │ Keepalived│
     │  APIServer│   │  APIServer│   │  APIServer│
     │    KCM    │   │    KCM    │   │    KCM    │
     │ Scheduler │   │ Scheduler │   │ Scheduler │
     │  Kubelet  │   │  Kubelet  │   │  Kubelet  │
     └───────────┘   └───────────┘   └───────────┘
           ┌───────────────┼───────────────┐
     ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
     │  etcd-01  │   │  etcd-02  │   │  etcd-03  │
     └───────────┘   └───────────┘   └───────────┘
           ┌───────────────┐
     ┌─────┴─────┐   ┌─────┴─────┐
     │ worker-01 │   │ worker-02 │
     │ Containerd│   │ Containerd│
     │  Kubelet  │   │  Kubelet  │
     └───────────┘   └───────────┘
```

- **HA 入口**：Nginx 4 层 stream 代理 + Keepalived VIP 漂移
- **etcd**：独立 3 节点集群，mTLS 双向认证
- **PKI**：cfssl 签发，含 front-proxy CA 支持 API 聚合层
- **网络**：Calico BGP 模式 + kube-proxy DaemonSet

### 容器模式

```
  Docker Network: k8s-net (172.20.0.0/24)
  ┌─────────────────────────────────────────────┐
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
  │  │master-01 │ │master-02 │ │master-03 │    │
  │  │  Nginx   │ │  Nginx   │ │  Nginx   │    │
  │  │ APIServer│ │ APIServer│ │ APIServer│    │
  │  └──────────┘ └──────────┘ └──────────┘    │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
  │  │ etcd-01  │ │ etcd-02  │ │ etcd-03  │    │
  │  └──────────┘ └──────────┘ └──────────┘    │
  │  ┌──────────┐ ┌──────────┐                  │
  │  │worker-01 │ │worker-02 │                  │
  │  └──────────┘ └──────────┘                  │
  └─────────────────────────────────────────────┘
```

- **HA 入口**：Nginx 本地代理 (无 VIP，容器模式不需要 Keepalived)
- **连接方式**：`ansible_connection: docker` 直接通过 Docker API 管理
- **跳过**：内核模块、sysctl、防火墙、Swap、chrony（容器共享宿主内核）

## 前置要求

### 物理机 / 虚拟机模式

- 控制机：macOS / Linux，已安装 Ansible ≥ 2.9
- 目标节点：Ubuntu 20.04+ / CentOS 7+，SSH 免密可登录
- 网络互通：控制机可 SSH 到所有节点，节点间网络互通

### 容器模式

- 控制机：已安装 Docker + Ansible ≥ 2.9
- 需要 `community.docker` collection：`ansible-galaxy collection install community.docker`
- 无需 SSH，无需目标节点预装任何软件

## 目录结构

```
.
├── Dockerfile                       # 容器节点基础镜像
├── inventories/
│   ├── hosts.yml                    # 物理机/虚拟机 主机清单
│   ├── hosts-container.yml          # 容器模式 主机清单
│   └── group_vars/all.yml           # 组件版本号 + 部署模式变量
├── files/
│   └── amd64/                       # 二进制缓存 (download role 下载至此)
├── roles/
│   ├── download/                    # 统一下载所有二进制包
│   ├── container-infra/             # 容器基础设施 (构建镜像+创建容器)
│   ├── common/                      # 节点系统初始化 (适配 machine/container)
│   ├── kubeconfig/                  # CA/证书/Kubeconfig 生成
│   ├── lb/                          # Nginx + Keepalived HA (容器模式跳过 Keepalived)
│   ├── etcd/                        # etcd 集群部署
│   ├── kube_master/                 # 控制面三件套
│   ├── kubelet/                     # Containerd + Kubelet
│   ├── kube-proxy/                  # kube-proxy (systemd 模式)
│   └── cni/                         # Calico + CoreDNS + kube-proxy DaemonSet
├── 0000-container-infra.yml         # 容器模式: 构建镜像+拉起容器
├── 0001-download-binaries.yml
├── 0000-common-service.yml
├── 0002-common-kubeconfig.yml
├── 0005-install-lb.yml
├── 0010-create-manager-set.yml
├── 0012-manager-set-kube.yml
├── 0020-create-compute-set.yml
└── 0030-install-cni.yml
```

## 组件版本

| 组件 | 版本 | 配置位置 |
|------|------|---------|
| Kubernetes | 1.36.1 | `group_vars/all.yml` |
| etcd | 3.6.11 | `group_vars/all.yml` |
| Containerd | 2.3.0 | `group_vars/all.yml` |
| runc | 1.3.5 | `group_vars/all.yml` |
| CNI Plugins | 1.9.1 | `group_vars/all.yml` |
| Calico | 3.32.0 | `group_vars/all.yml` |
| CoreDNS | 1.14.3 | `group_vars/all.yml` |
| cfssl | 1.6.4 | `group_vars/all.yml` |

## 部署流程

### 物理机 / 虚拟机部署

使用 `inventories/hosts.yml`，按顺序执行：

#### Step 1：下载二进制包

```bash
ansible-playbook -i inventories/hosts.yml 0001-download-binaries.yml
```

- 在控制机 localhost 执行
- 下载所有二进制包到 `files/<arch>/` 目录
- **后续步骤不再联网下载**，所有 role 直接从本地缓存分发

#### Step 2：节点环境初始化

```bash
ansible-playbook -i inventories/hosts.yml 0000-common-service.yml
```

- 目标：`kube_node` + `etcd`（所有节点）
- 禁用防火墙与 Swap、加载内核模块、配置 sysctl、安装 IPVS/chrony

#### Step 3：生成证书与 Kubeconfig

```bash
ansible-playbook -i inventories/hosts.yml 0002-common-kubeconfig.yml
```

- 在控制机 localhost 执行
- 签发：根 CA、front-proxy CA、SA 密钥对、etcd-client 证书
- 签发：kube-proxy、KCM、Scheduler、admin 组件证书
- 生成所有组件的 Kubeconfig 文件

#### Step 4：部署负载均衡

```bash
ansible-playbook -i inventories/hosts.yml 0005-install-lb.yml
```

- 目标：`kube_master`
- Nginx 4 层 stream 代理 + Keepalived VIP 漂移

#### Step 5：部署 etcd + 控制面

```bash
ansible-playbook -i inventories/hosts.yml 0010-create-manager-set.yml
```

| Tag | 目标 | 内容 |
|-----|------|------|
| `etcd` | etcd 节点 | 分发证书、安装 etcd 二进制、启动服务、健康校验 |
| `kube_master` | Master 节点 | 分发证书/kubeconfig、安装 APIServer/KCM/Scheduler |

#### Step 6：部署 Master 节点 Kubelet

```bash
ansible-playbook -i inventories/hosts.yml 0012-manager-set-kube.yml
```

#### Step 7：部署 Worker 节点

```bash
ansible-playbook -i inventories/hosts.yml 0020-create-compute-set.yml
```

#### Step 8：部署网络插件与 DNS

```bash
ansible-playbook -i inventories/hosts.yml 0030-install-cni.yml
```

- CNI 基础二进制 + Calico + CoreDNS
- kube-proxy：默认以 DaemonSet 部署（`kube_proxy_deploy_mode: daemonset`）

### 容器模式部署

使用 `inventories/hosts-container.yml`，在 Step 2 之前增加基础设施准备步骤：

#### Step 0：构建镜像 + 拉起容器

```bash
ansible-playbook -i inventories/hosts-container.yml 0000-container-infra.yml
```

- 构建基于 Ubuntu 22.04 + systemd 的容器节点镜像
- 创建 Docker 网络，为每个节点拉起特权容器
- 等待容器内 systemd 就绪

#### Step 1-8：与物理机/虚拟机相同

```bash
INV="-i inventories/hosts-container.yml"

ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0020-create-compute-set.yml
ansible-playbook $INV 0030-install-cni.yml
```

容器模式下以下步骤自动跳过（由 `node_type: container` 控制）：
- 内核模块加载 / sysctl 配置
- 防火墙 / Swap 关闭
- Chrony 时间同步
- Keepalived VIP 部署

### 一键全量部署

```bash
# 物理机 / 虚拟机
ansible-playbook -i inventories/hosts.yml \
  0001-download-binaries.yml \
  0000-common-service.yml \
  0002-common-kubeconfig.yml \
  0005-install-lb.yml \
  0010-create-manager-set.yml \
  0012-manager-set-kube.yml \
  0020-create-compute-set.yml \
  0030-install-cni.yml

# 容器模式
ansible-playbook -i inventories/hosts-container.yml \
  0000-container-infra.yml \
  0001-download-binaries.yml \
  0000-common-service.yml \
  0002-common-kubeconfig.yml \
  0005-install-lb.yml \
  0010-create-manager-set.yml \
  0012-manager-set-kube.yml \
  0020-create-compute-set.yml \
  0030-install-cni.yml
```

## 关键变量

### 部署模式变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `node_type` | `machine` | 部署目标：`machine`(VM/物理机) / `container`(Docker) |
| `kube_proxy_deploy_mode` | `daemonset` | kube-proxy 部署方式：`daemonset` / `systemd` |
| `kube_proxy_proxy_mode` | `ipvs` | kube-proxy 代理模式：`ipvs` / `iptables` |

### 网络变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `target_arch` | `amd64` | 目标节点架构 |
| `LB_APISERVER_VIP` | `192.168.1.100` | Keepalived VIP (机器模式) / master-01 IP (容器模式) |
| `LB_APISERVER_PORT` | `8443` | Nginx 代理端口 |
| `SERVICE_CIDR` | `10.96.0.0/16` | Service 网段 |
| `CLUSTER_CIDR` | `10.244.0.0/16` | Pod 网段 |
| `CLUSTER_DNS_SVC_IP` | `10.96.0.10` | CoreDNS Service IP |

### 路径变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `download_dir` | `{{ playbook_dir }}/files` | 二进制缓存根目录 |
| `download_arch_dir` | `{{ download_dir }}/{{ target_arch }}` | 按架构隔离的缓存目录 |
| `local_cluster_config_dir` | 项目根目录下 `ssl_build/` | 证书/kubeconfig 产出目录 |

## 两种模式行为差异

| 行为 | `machine` | `container` |
|------|-----------|-------------|
| 连接方式 | SSH | Docker API |
| 内核模块加载 | 执行 | 跳过 (共享宿主内核) |
| sysctl 配置 | 执行 | 跳过 (共享宿主内核) |
| 防火墙 / Swap | 关闭 | 跳过 (容器无此概念) |
| Chrony 时间同步 | 安装启动 | 跳过 (宿主控制时钟) |
| Keepalived VIP | 安装启动 | 跳过 (无 VIP 需求) |
| Nginx 代理 | 安装启动 | 安装启动 (仅本地代理) |
| kube-proxy | DaemonSet (默认) | DaemonSet (默认) |

## 离线部署

项目天然支持离线部署：

1. 在联网环境执行 `0001-download-binaries.yml`，所有二进制定位到 `files/<arch>/`
2. 将整个项目目录打包拷贝到离线环境
3. 在离线环境按部署流程执行即可，无需任何网络访问

容器模式还需提前准备好 kube-proxy、CoreDNS、Calico、pause 等容器镜像：

```bash
# 预拉取镜像并导出
docker pull registry.k8s.io/kube-proxy:v1.36.1
docker pull coredns/coredns:1.14.3
docker pull registry.k8s.io/pause:3.10.2
docker save -o k8s-images.tar \
  registry.k8s.io/kube-proxy:v1.36.1 \
  coredns/coredns:1.14.3 \
  registry.k8s.io/pause:3.10.2

# 离线环境导入
docker load -i k8s-images.tar
```

## 故障排查

- **etcd 健康检查失败**：确认 etcd 证书与 `etcd_ssl_dir` 路径一致，检查 2379 端口连通性
- **APIServer 未就绪**：检查 VIP 是否漂移到 Master (机器模式)、Nginx 是否代理正常、审计策略文件是否存在
- **节点 NotReady**：检查 Calico Pod 是否 Running、kube-proxy DaemonSet 是否正常、CNI 二进制是否安装
- **证书签发失败**：确认 `local_cluster_config_dir` 下 `ssl/` 目录权限正确，cfssl 已安装到本地
- **容器模式连接失败**：确认 Docker daemon 运行中、`community.docker` collection 已安装
- **容器内 systemd 未就绪**：确认容器以 `--privileged` 启动、`/sys/fs/cgroup` 已挂载
