# Kubernetes 组件部署流程文档

## 1. 文档范围

本文按标准 Kubernetes 组件部署逻辑整理当前仓库中可对应的流程，覆盖 Kubernetes 本身及其核心运行所需的组件：

- CA 与 kubeconfig (含 Service Account 密钥对、kube-proxy 凭证与 **etcd 双向 TLS 客户端证书**)
- 外部 / 本地高可用负载均衡器 (nginx + keepalived)
- **独立专属 etcd 安全集群** (数据与控制分离架构)
- kube-apiserver (含 **API 安全审计日志** 与安全隔离配置)
- kube-controller-manager (含高可用 Leader 选举与 **可观测性指标暴露**)
- kube-scheduler (含高可用 Leader 选举与 **可观测性指标暴露**)
- kubelet
- containerd / CRI (容器运行时)
- CNI 网络插件 (网络通达与 Node Ready 的必要前提)
- kube-proxy 与 CoreDNS (核心网络与服务解析)
- 节点注册与 Ready 状态就绪校验

以下内容不纳入本文流程：

- 业务平台组件
- 虚拟化服务
- 资源注册流程
- 非 Kubernetes 网络资源
- 镜像仓库和外部存储服务
- 监控（如 Prometheus 采集端）、日志（如 EFK 收集器）、外部存储服务本身
- 非 Kubernetes 标准组件的 systemd 服务

当前仓库不是 kubeadm 部署方式。Kubernetes 控制面组件由 Ansible role 直接渲染配置并通过 systemd 管理。

### 版本基线

以下版本是本仓库在 2026-05-22 锁定并验证语法通过的部署基线，不自动跟随上游最新版本。版本统一在 `inventories/group_vars/all.yml` 中维护：

| 组件 | 当前变量 | 当前值 |
|---|---|---|
| Kubernetes | `kubernetes_version` | `1.36.1` |
| CFSSL | `cfssl_version` | `1.6.5` |
| etcd | `etcd_version` | `3.6.11` |
| containerd | `containerd_version` | `2.3.0` |
| runc | `runc_version` | `1.3.5` |
| CNI plugins | `cni_plugins_version` | `1.9.1` |
| Calico | `calico_version` | `3.32.0` |
| CoreDNS | `coredns_version` | `1.14.3` |

升级版本时必须先调整 `inventories/group_vars/all.yml`，再执行 `ansible-playbook --syntax-check` 和目标环境预检。不要在 role task 或 template 中硬编码组件版本。

## 2. 标准组件与仓库映射

| Kubernetes 标准组件 | 当前仓库入口 | 说明 |
|---|---|---|
| CA / kubeconfig / SA / etcd-client / front-proxy | `0002-common-kubeconfig.yml`, `roles/kubeconfig` | 生成 CA、SA 密钥对 (`sa.key`/`sa.pub`)、etcd 双向 TLS 证书、aggregator front-proxy 证书、admin、kube-proxy 及各组件凭证 |
| 负载均衡 (nginx + keepalived) | `0005-install-lb.yml`, `roles/lb` | 部署高可用负载均衡器，提供统一的 `LB_APISERVER_VIP` 接入入口 |
| etcd (专属节点) | `0010-create-manager-set.yml`, `roles/etcd` | 部署独立 etcd 集群，**生产环境强烈推荐解耦独立物理节点以防止 I/O 争抢** |
| kube-apiserver | `0010-create-manager-set.yml`, `roles/kube_master` | 通过 systemd 启动，配置 SA 公钥、API 安全审计策略以及 etcd-client 双向加密证书 |
| kube-controller-manager | `0010-create-manager-set.yml`, `roles/kube_master` | 通过 systemd 启动，配置 SA 私钥、高可用选举，开放 HTTPS 可观测性监控端口 |
| kube-scheduler | `0010-create-manager-set.yml`, `roles/kube_master` | 通过 systemd 启动，配置高可用选举，开放 HTTPS 可观测性监控端口 |
| containerd / CRI | `roles/kubelet` | 统一在 kubelet 角色内渲染 `/etc/containerd/config.toml` 并启动 containerd |
| kubelet | `0012-manager-set-kube.yml`, `0020-create-compute-set.yml`, `roles/kubelet` | 管理节点和工作节点均通过该 role 部署，对齐 cgroup 驱动，开放监控接口 |
| CNI 网络插件 | `0030-install-cni.yml`, `roles/cni` | 部署 CNI 二进制及配置模板（如 Calico），激活数据面网络通达 |
| CoreDNS | `0030-install-cni.yml`, `roles/cni` | 渲染 CoreDNS 清单并通过 admin kubeconfig 发布到集群，提供内部 DNS 解析 |
| kube-proxy | `0030-install-cni.yml`, `roles/cni`, `roles/kube-proxy` | 默认 `kube_proxy_deploy_mode=daemonset`，由 `roles/cni` 渲染并发布 DaemonSet；设置为 `systemd` 时才执行 `roles/kube-proxy` 部署 systemd 服务 |

## 3. 标准部署顺序

标准 Kubernetes 组件的依赖顺序如下：

```text
节点基础环境
  -> CA / kubeconfig 与 SA 密钥生成 (含 kube-proxy 凭证与 etcd-client 专属证书)
  -> 负载均衡集群就绪 (nginx + keepalived 绑定 VIP)
  -> etcd 独立集群就绪 (启用 mTLS 双向认证)
  -> kube-apiserver 启动 (监听物理 IP，配置审计策略与 etcd 专属证书)
  -> kube-controller-manager 启动 (开启 Leader Election 与安全指标监控，连接 VIP)
  -> kube-scheduler 启动 (开启 Leader Election 与安全指标监控，连接 VIP)
  -> containerd 容器运行时就绪 (Cgroup 驱动对齐 systemd)
  -> kubelet 服务启动与节点注册 (连接 VIP，此时节点状态为 NotReady)
  -> CNI 网络插件部署 (激活网络平面，Kubelet 自动感知配置)
  -> CoreDNS 部署
  -> kube-proxy 部署 (默认 DaemonSet，可选 systemd)
  -> Node 状态变为 Ready
```

对应到当前仓库的优化执行链路：

```text
0000-common-service.yml (环境初始化)
  -> 0001-download-binaries.yml (预下载并缓存 cfssl / kubectl / Kubernetes / containerd / CNI / Calico 二进制与清单)
  -> 0002-common-kubeconfig.yml (证书、Kubeconfig 与 etcd-client / front-proxy 证书预生成)
  -> 0005-install-lb.yml (部署 nginx + keepalived 负载均衡集群，绑定 VIP)
  -> 0010-create-manager-set.yml (部署专属 etcd 与 Master 控制面组件)
  -> 0012-manager-set-kube.yml (部署 Master 节点的 kubelet/CRI)
  -> 0020-create-compute-set.yml (部署 Worker 节点的 kubelet/CRI)
  -> 0030-install-cni.yml (部署 CNI 网络插件与核心系统组件，激活集群)
```

说明：

- **LB 先行原则**：`0005-install-lb.yml` 必须在控制面（kube-apiserver）和组件启动前完成部署，以保证 `kube-controller-manager`、`kube-scheduler` 启动时能够通过已配置的 `kubeconfig` 成功连接负载均衡的 VIP，避免启动报错。
- `0001-download-binaries.yml` 是当前实现链路中的前置缓存预热步骤。若直接执行 `0002-common-kubeconfig.yml`、`0010-create-manager-set.yml`、`0012-manager-set-kube.yml`、`0020-create-compute-set.yml` 或 `0030-install-cni.yml`，必须确保 `files/<arch>/` 已存在对应二进制和清单。
- 依赖本地缓存或生成物的入口 playbook 已内置 preflight 检查；缓存、证书或 kubeconfig 缺失时会在执行具体 role 前终止，并提示先运行对应前置 playbook。
- `0010-create-manager-set.yml` 中还包含非 Kubernetes 标准 role。本文只讨论其中的 `etcd` 与 `kube_master`。
- `0012-manager-set-kube.yml` 和 `0020-create-compute-set.yml` 中包含的 `kubelet` 角色会在节点完成注册。只有在 CNI 网络组件部署后，节点才会真正转为 `Ready` 状态。

## 4. Inventory 与节点角色

标准 Kubernetes 视角下需要关注以下分组与关键变量：

| 分组 | 标准 Kubernetes 角色 | 当前仓库说明 |
|---|---|---|
| `kube_master` | control-plane 节点 | 部署负载均衡、Kubernetes 控制面。高可用场景下建议配置 3 节点 |
| `etcd` | etcd 专属节点 | **生产环境强烈推荐使用 3 台搭载 SSD 存储的独立节点，实现计算与数据解耦。中小型规模可复用控制面节点，但须做好 I/O 隔离** |
| `compute_servers` | worker 节点 | 部署 kubelet 与 containerd，注册为 Kubernetes Node |
| `kube_node` | 全部 Kubernetes 节点 | 包含控制面节点和工作节点 |

标准 Kubernetes 相关核心变量：

| 变量 | 用途 | 最佳实践/安全要求 |
|---|---|---|
| `SERVICE_CIDR` | Kubernetes Service CIDR | 避免与节点物理网络冲突 |
| `MASTER_CERT_HOSTS` | 追加到 kube-apiserver 证书 SAN | 必须包含所有控制面节点 IP、VIP 及集群内部 DNS 名 |
| `KUBE_APISERVER` | kubeconfig 中的 apiserver 地址 | 指向高可用接入地址 `https://{{ LB_APISERVER_VIP }}:{{ LB_APISERVER_PORT }}` |
| `LB_APISERVER_VIP` | 多控制面场景下的负载均衡虚拟 IP | 配合 Keepalived/Nginx 集群实现虚拟 IP 自动漂移 |
| `LB_APISERVER_PORT` | Nginx 负载均衡监听端口 | 通常配置为 `8443` 或 `6443`（若 apiserver 绑定在物理 IP 端口上） |
| `CONTAINERD_CGROUP_DRIVER`| containerd 与 kubelet 的 cgroup 驱动 | 生产环境必须统一设为 `systemd`，避免节点失联与 OOM 异常 |

---

## 5. 部署流程

### 5.1 节点基础环境

入口 playbook：

- `0000-common-service.yml`

标准 Kubernetes 视角下，该阶段只承担前置准备：

1. 检查节点初始化状态。
2. 配置软件源和基础包（如 `ipvsadm`、`ipset`、`conntrack` 等内核模块依赖）。
3. 关闭 Swap 分区（Kubelet 运行的强力要求）。
4. 准备后续证书、二进制、systemd 服务所需的系统环境。
5. 配置时间同步（Chrony/NTP），避免 etcd 节点因时间漂移引发选举失败或证书校验失败。

### 5.2 生成 CA 与 kubeconfig (含 SA、Proxy 与 etcd-client 双向证书)

入口 playbook：`0002-common-kubeconfig.yml`

关键 role：`roles/kubeconfig`

主要动作：

1. 创建 `{{ local_cluster_config_dir }}/ssl` 证书存储目录。
2. 使用 `files/<arch>/cfssl`、`files/<arch>/cfssljson` 与 `files/<arch>/kubectl` 的绝对路径生成证书和 kubeconfig；不会向控制机 `/usr/local/bin` 写入工具。控制机工具按控制机 OS/架构下载，目标节点二进制仍按 `target_arch` 下载。
3. 检查 `ca.pem` 是否存在，若不存在则生成 CA 密钥对。
4. 生成 Service Account 专用非对称密钥对 `sa.key` 和 `sa.pub`（禁止与 CA 密钥对混用以确保系统安全）。
5. 生成 aggregator front-proxy CA 与 `front-proxy-client` 证书，用于 Kubernetes Aggregated API（如 Metrics API）请求头代理认证。
6. **签发 etcd 双向 TLS 客户端证书**：生成专用 `etcd-client.pem` 与 `etcd-client-key.pem` 客户端证书（**实现 APIServer 与 etcd 的 mTLS 绝对安全认证，隔离非法内网越权**）。
7. 签发 `kube-proxy` 专属证书（`kube-proxy.pem` 与 `kube-proxy-key.pem`），并生成对应的 `kube-proxy.kubeconfig`（**严禁滥用 admin 高权限凭证部署 kube-proxy，以对齐最小权限安全准则**）。
8. 使用规划好的 `LB_APISERVER_VIP` 生成 admin kubeconfig，以及 `kube-controller-manager`、`kube-scheduler` 访问控制面所需的 kubeconfig。

标准 Kubernetes 组件对应关系：

| 产物 | 用途 | 存放路径 |
|---|---|---|
| `ca.pem` / `ca-key.pem` | Kubernetes 集群 CA 证书与私钥 | `/etc/kubernetes/ssl/` |
| `sa.pub` / `sa.key` | Service Account Token 签名与验证密钥对 | `/etc/kubernetes/ssl/` |
| `etcd-client.pem` / `etcd-client-key.pem` | APIServer 访问 etcd 的双向 TLS 客户端证书与私钥 | `/etc/kubernetes/ssl/` |
| `front-proxy-ca.pem` / `front-proxy-client.pem` / `front-proxy-client-key.pem` | Aggregated API requestheader 代理认证 | `/etc/kubernetes/ssl/` |
| `admin.kubeconfig` | 管理员访问 apiserver 的凭证 | 本地 `{{ local_cluster_config_dir }}/kubeconfig/admin.kubeconfig`，Master 节点 `/root/.kube/config` |
| `kube-controller-manager.kubeconfig` | controller-manager 访问凭证 | `/etc/kubernetes/` |
| `kube-scheduler.kubeconfig` | scheduler 访问凭证 | `/etc/kubernetes/` |
| `kube-proxy.kubeconfig` | kube-proxy 专属通信与服务转发凭证 | `/etc/kubernetes/` |

> ⚠️ **安全与运维提示**
> - 当前方案采用 Ansible **静态分发证书**，并非 TLS Bootstrap 动态签发。
> - 证书默认有效期需在模版中设为较长年限（如 10 年），并建立清晰的证书过期轮转（Renewal）运维预案。

### 5.3 部署 Nginx + Keepalived 负载均衡集群

入口 playbook：`0005-install-lb.yml`

关键 role：`roles/lb`

主要动作：

1. **安装 nginx**：部署轻量级本地或集群侧 Nginx，在 `kube_master` 节点上提供 4 层 `stream` 转发服务。
2. **配置 nginx**：渲染 `/etc/nginx/nginx.conf`，将流量均衡代理至后端的多个实际 `kube_master` 节点的 `kube-apiserver` 服务端口（如物理 IP 的 6443 端口）。
3. **安装 keepalived**：部署 keepalived 守护进程，用于在所有 `kube_master` 节点间利用 VRRP 协议虚拟出 `LB_APISERVER_VIP`。
4. **配置 keepalived 防御性健康检查**：
   - 渲染 `/etc/keepalived/keepalived.conf`。
   - 配置高可用状态机（主节点为 `MASTER`，备节点为 `BACKUP`），设置不同的 VRRP 优先级 `priority`。
   - 配置 Nginx 统一健康检查脚本（`/etc/keepalived/check_nginx.sh`）。**要求所有节点（含备节点）必须持续监控本地 Nginx 状态。若本地 Nginx 崩溃，备节点必须主动降低自身权重或宣告 FAULT，严禁在自身 nginx 挂掉的情况下盲目接管/强占 VIP。**
5. **启动并守护** `nginx` 和 `keepalived` 服务。

> ⚠️ **网络架构警告**
> Keepalived 方案强依赖二层网络多播（Multicast）或单播环境。在云厂商网络环境（如 AWS、阿里云，默认禁用 VRRP 多播）或跨三层网络（跨网段/跨物理交换机）部署场景下，极易因心跳包丢失引发“双主抢占 VIP”脑裂。
> **应对策略**：在上述受限环境下，应改用云厂商提供的四层 SLB（如监听 8443 转发各 Master 的 6443），或者在所有节点本地回环地址部署轻量级 Nginx（Local Loopback Proxy 方案，各节点连接本地 `127.0.0.1:8443` 进行自负载）。

Nginx 核心 4层 转发配置示例：

```nginx
stream {
    upstream kube-apiserver {
        server 192.168.1.11:6443 max_fails=3 fail_timeout=30s;
        server 192.168.1.12:6443 max_fails=3 fail_timeout=30s;
        server 192.168.1.13:6443 max_fails=3 fail_timeout=30s;
    }
    server {
        listen 0.0.0.0:8443;  # Nginx 代理监听端口 (即 LB_APISERVER_PORT)
        proxy_connect_timeout 2s;
        proxy_timeout 900s;
        proxy_pass kube-apiserver;
    }
}
```

校验：

```bash
# 在所有 Master 节点检查服务状态
systemctl is-active nginx
systemctl is-active keepalived

# 校验 VIP 是否成功绑定在 Master 节点上
ip addr show | grep <LB_APISERVER_VIP>

# 校验负载均衡端口连通性
nc -z -w 3 <LB_APISERVER_VIP> <LB_APISERVER_PORT>
```

### 5.4 部署 etcd 专属集群 (启用 mTLS 双向认证)

入口 playbook：`0010-create-manager-set.yml`

关键 role：`roles/etcd`

主要动作：

1. 计算 etcd 成员列表 `ETCD_NODES`。
2. 创建证书及数据存储目录（**生产环境强烈推荐使用独立的高速 SSD 存储挂载至数据目录，避免高并发 I/O 争抢引发共识分裂**）。
3. 同步 Kubernetes CA，并为 etcd 签发专属证书（`etcd.pem` / `etcd-key.pem`）。
4. 分发 etcd 及 etcdctl 二进制文件。
5. **配置 etcd 安全参数**：在 `etcd.service` 中开启 `--client-cert-auth=true` 与 `--peer-client-cert-auth=true`，实现完全的 **mTLS 双向 TLS 校验**。
6. 渲染并启动 `etcd.service` systemd 服务。
7. 轮询健康状态，确保 etcd 集群达成共识。

校验：

```bash
# 检查服务状态
systemctl is-active etcd

# 校验集群健康度 (使用 etcd 专用 mTLS 证书进行认证)
etcdctl \
  --cacert=/opt/etcd/ssl/ca.pem \
  --cert=/opt/etcd/ssl/etcd.pem \
  --key=/opt/etcd/ssl/etcd-key.pem \
  --endpoints=https://<etcd-member-ip>:2379 \
  endpoint health
```

### 5.5 部署 kube-apiserver (含安全审计防线与 mTLS etcd 通信)

入口 playbook：`0010-create-manager-set.yml`

关键 role：`roles/kube_master/tasks/main.yml`（渲染 kube-apiserver / kube-controller-manager / kube-scheduler 三个 systemd 模板）

主要动作：

1. 签发 apiserver 服务端证书，SAN 必须覆盖 `LB_APISERVER_VIP`、所有 Master 节点 IP 以及 `kubernetes.default.svc` 等内部域名。
2. 生成 aggregator proxy 证书（用于支持 Metrics API 扩展）。
3. **下发 API 安全审计策略**：渲染并下发 `/etc/kubernetes/audit-policy.yaml` 策略文件，规范集群各类 API 操作审计级别。
4. **配置安全与审计参数**：
   - **配置 Aggregated API requestheader 参数**：
     - `--requestheader-client-ca-file=/etc/kubernetes/ssl/front-proxy-ca.pem`
     - `--requestheader-allowed-names=front-proxy-client`
     - `--requestheader-extra-headers-prefix=X-Remote-Extra-`
     - `--requestheader-group-headers=X-Remote-Group`
     - `--requestheader-username-headers=X-Remote-User`
     - `--proxy-client-cert-file=/etc/kubernetes/ssl/front-proxy-client.pem`
     - `--proxy-client-key-file=/etc/kubernetes/ssl/front-proxy-client-key.pem`
   - `--service-account-key-file=/etc/kubernetes/ssl/sa.pub` (指定 SA 校验公钥)
   - **配置 etcd mTLS 双向加密参数**：
     - `--etcd-servers` (配置前置部署的专属 etcd 集群地址)
     - `--etcd-cafile=/etc/kubernetes/ssl/ca.pem`
     - `--etcd-certfile=/etc/kubernetes/ssl/etcd-client.pem` (**指定专有的 etcd TLS 客户端证书**)
     - `--etcd-keyfile=/etc/kubernetes/ssl/etcd-client-key.pem`
   - **配置 API 安全审计参数**：
     - `--audit-policy-file=/etc/kubernetes/audit-policy.yaml`
     - `--audit-log-path=/var/log/kubernetes/audit.log`
     - `--audit-log-maxage=30`
     - `--audit-log-maxbackup=10`
     - `--audit-log-maxsize=100`
   - `--bind-address` (**绑定在各控制面节点的物理网卡 IP 上**。这能有效防止 apiserver 绕过 LB 策略抢占 VIP 网卡路由，并将物理端口 6443 与 Nginx 代理端口 8443 实现清晰的边界隔离)
   - `--secure-port=6443`
5. 启动并守护 `kube-apiserver.service` 服务。

校验：

```bash
systemctl is-active kube-apiserver
kubectl get --raw='/readyz?verbose'
```

### 5.6 部署 kube-controller-manager (含安全可观测性监控)

入口 playbook：`0010-create-manager-set.yml`

关键 role：`roles/kube_master/tasks/main.yml`

主要动作：

1. 下发 `kube-controller-manager.kubeconfig`（其 server 指向 `LB_APISERVER_VIP:LB_APISERVER_PORT`）。
2. **配置安全与监控参数**：
   - `--service-account-private-key-file=/etc/kubernetes/ssl/sa.key` (指定 SA 签名私钥)
   - `--leader-elect=true` (**多控制面高可用集群必须开启，防止脑裂**)
   - `--bind-address=127.0.0.1` (或指定物理网卡 IP 监听安全可观测性指标接口)
   - `--secure-port=10257` (**启用安全监控端口暴露，供 SRE 采集可观测性指标**)
3. 启用并启动 `kube-controller-manager.service`。

校验：

```bash
systemctl is-active kube-controller-manager
# 验证 Lead 锁状态
kubectl get lease -n kube-system
```

### 5.7 部署 kube-scheduler (含安全可观测性监控)

入口 playbook：`0010-create-manager-set.yml`

关键 role：`roles/kube_master/tasks/main.yml`

主要动作：

1. 下发 `kube-scheduler.kubeconfig`（其 server 指向 `LB_APISERVER_VIP:LB_APISERVER_PORT`）。
2. **配置监控与高可用选举**：
   - `--leader-elect=true` (**多控制面高可用集群必须开启**)
   - `--bind-address=127.0.0.1` (或指定物理网卡 IP)
   - `--secure-port=10259` (**启用安全监控端口暴露，供 SRE 采集可观测性指标**)
3. 启用并启动 `kube-scheduler.service`。

校验：

```bash
systemctl is-active kube-scheduler
```

### 5.8 部署 containerd / CRI

入口 playbook：`0012-manager-set-kube.yml` (Master) 与 `0020-create-compute-set.yml` (Worker)

关键 role：`roles/kubelet`

主要动作：

1. 渲染容器运行时配置 `/etc/containerd/config.toml`。
2. 当前 `containerd_version` 为 2.x，`config.toml` 使用 `version = 3` 与 `io.containerd.cri.v1.*` 配置路径；不要回退到 containerd 1.x 的 `io.containerd.grpc.v1.cri` 配置路径。
3. **Cgroup 驱动对齐**：`SystemdCgroup` 根据 `CONTAINERD_CGROUP_DRIVER` 渲染，生产环境应保持 `systemd`。
4. **Sandbox 镜像重定向**：将默认的 `pause` 镜像地址显式配置为 `registry.k8s.io/pause:3.10.2`；受限网络环境应在私有镜像仓库同步该镜像后覆盖 `SANDBOX_IMAGE`。
5. 启用并启动 `containerd.service`。

校验：

```bash
systemctl is-active containerd
crictl info | grep -i cgroup
```

### 5.9 部署 kubelet

入口 playbook：`0012-manager-set-kube.yml` 与 `0020-create-compute-set.yml`

关键 role：`roles/kubelet/tasks/main.yml`

主要动作：

1. 静态签发该节点的 `kubelet.pem` 证书，并生成 `kubelet.kubeconfig`（其 server 同样指向 `LB_APISERVER_VIP:LB_APISERVER_PORT`）。
2. 渲染 `/opt/kubelet/config.yaml`，指定参数：
   - `cgroupDriver: {{ CONTAINERD_CGROUP_DRIVER }}` (**必须与 containerd 保持绝对一致**)
   - `containerRuntimeEndpoint: unix:///run/containerd/containerd.sock` (**Kubernetes 1.36 兼容写法，禁止继续使用已移除的 `--container-runtime` 启动参数**)
3. 启动并守护 `kubelet.service`。
4. **服务状态与注册校验**：轮询 `kubelet` systemd 状态并检查节点是否成功在控制面完成注册（此时节点因为没有部署 CNI，状态应为 `NotReady`，Ansible 任务在此处**不可死等 Ready 状态**，只需确保服务 active 且节点已注册即可）。

校验：

```bash
systemctl is-active kubelet
kubectl get node -o wide
# 此时节点应为 NotReady 状态，原因为 NetworkReady=false
```

### 5.10 部署 CNI 网络插件与系统核心组件

入口 playbook：`0030-install-cni.yml`

主要动作：

1. 分发 CNI 基础二进制文件至 `/opt/cni/bin/`。
2. 渲染并下发 CNI 网络插件（如 Calico 或 Flannel）的模板文件。
3. 执行部署并激活网络数据平面。
4. **无需重启 kubelet 提示**：Kubelet 启动后利用内核 inotify 机制自动感知 `/etc/cni/net.d` 目录下的 CNI 配置文件，**在 CNI 下发部署后，无需执行任何 kubelet 服务重启操作**，节点网络将平滑通达。
5. 部署 `CoreDNS` (提供内部域名解析)，所有 `kubectl apply` 必须显式使用 `{{ local_cluster_config_dir }}/kubeconfig/admin.kubeconfig`，禁止依赖控制机默认 kubeconfig。
6. 部署 `kube-proxy`：默认以 DaemonSet 方式发布；如设置 `kube_proxy_deploy_mode=systemd`，则使用 5.2 节生成的专属 `kube-proxy.kubeconfig` 在各节点部署 systemd 服务。
7. **轮询 Ready 状态**：等待 CNI、CoreDNS 与 kube-proxy 完成部署，网络平面通达，轮询所有 Node 的 Ready condition 均为 `True`，禁止把 `Unknown` 或其他非 Ready 状态误判为成功。

校验：

```bash
# 轮询直至节点就绪
kubectl get node
# 预期输出所有节点状态为 Ready

# 验证系统 Pod 状态
kubectl get pods -n kube-system
```

---

## 6. 控制面启动方式

当前仓库通过 systemd 独立管理控制面组件，相比静态 Pod 模式更加直观：

| 组件 | systemd 服务 | 日志定位方式 |
|---|---|---|
| nginx | `nginx.service` | `journalctl -u nginx` |
| keepalived | `keepalived.service` | `journalctl -u keepalived` |
| etcd | `etcd.service` | `journalctl -u etcd` |
| kube-apiserver | `kube-apiserver.service` | `/opt/kube-apiserver/logs/` |
| kube-controller-manager | `kube-controller-manager.service` | `/opt/kube-controller-manager/logs/` |
| kube-scheduler | `kube-scheduler.service` | `/opt/kube-scheduler/logs/` |
| containerd | `containerd.service` | `journalctl -u containerd` |
| kubelet | `kubelet.service` | `journalctl -u kubelet` |

---

## 7. 最小手工执行示例

首次部署、版本变更或缓存缺失时先执行一次本地缓存预热：

```bash
ansible-playbook -i inventories/hosts.yml 0001-download-binaries.yml
```

生成全局凭证与密钥（含 etcd-client 专属 TLS 证书）：

```bash
ansible-playbook -i inventories/hosts.yml 0002-common-kubeconfig.yml
```

部署高可用负载均衡集群（nginx + keepalived）：

```bash
ansible-playbook -i inventories/hosts.yml 0005-install-lb.yml
```

部署 etcd 专属集群与 Master 控制面：

```bash
ansible-playbook -i inventories/hosts.yml 0010-create-manager-set.yml --tags etcd
ansible-playbook -i inventories/hosts.yml 0010-create-manager-set.yml --tags kube_master
```

部署控制面节点的 kubelet 与运行时：

```bash
ansible-playbook -i inventories/hosts.yml 0012-manager-set-kube.yml --tags kubelet
```

部署工作节点的 kubelet 与运行时：

```bash
ansible-playbook -i inventories/hosts.yml 0020-create-compute-set.yml --tags kubelet
```

部署 CNI 网络插件与 kube-proxy/CoreDNS（激活集群）：

```bash
ansible-playbook -i inventories/hosts.yml 0030-install-cni.yml
```

---

## 8. 部署后验收清单

### 8.1 负载均衡高可用状态

```bash
# 在所有 Master 节点上确认 Nginx 端口 8443 是否正常监听
ss -lntp | grep 8443

# 检查当前持有 VIP 的主机
ip addr show | grep <LB_APISERVER_VIP>

# 测试关闭 Master1 节点的 nginx，观察 VIP 是否向 Master2 漂移
systemctl stop nginx
# 在 Master2 检查
ip addr show | grep <LB_APISERVER_VIP>
```

### 8.2 控制面与计算节点服务状态及可观测性接口

```bash
# 在所有 Master 节点执行基础服务检查
for service in nginx keepalived etcd kube-apiserver kube-controller-manager kube-scheduler containerd kubelet; do
  systemctl is-active --quiet $service && echo "$service: Active" || echo "$service: Failed"
done

# 验证可观测性指标监控端口监听状态 (SRE 核心指标防线)
ss -lntp | grep -E "10257|10259"
```

### 8.3 核心组件安全审计与 TLS 数据面校验

```bash
# 验证 API 审计日志输出
tail -f /var/log/kubernetes/audit.log

# 验证 API 核心服务通达
kubectl get --raw='/readyz?verbose'

# 检查节点 Ready 状态
kubectl get node -o wide

# 验证 CoreDNS 解析
kubectl run dns-test --rm -i --tty --image=busybox:1.37.0 --restart=Never -- nslookup kubernetes.default
```

---

## 9. 故障定位

### 9.1 负载均衡高可用异常
1. **VIP 未正常绑定**：检查 `/var/log/messages` 或 `journalctl -u keepalived`。确信 VRRP 网卡接口名与配置文件完全匹配，且 `virtual_router_id` 在同一二层网络下没有被其他物理集群占用。
2. **Nginx 转发失败（502/连接拒绝）**：检查 Nginx upstream 配置中的 kube-apiserver 物理 IP 与 6443 端口是否填写正确。校验 `kube-apiserver` 服务自身是否处于 running 状态并正确绑定在物理 IP 接口。
3. **双主抢占 VIP（脑裂）**：通常由于底层交换机或云厂商限制了 VRRP 多播（vrrp traffic blocked）。此时应改为在本地回环部署 Local Loopback Nginx 代理，或使用云厂商提供的四层 SLB。

### 9.2 kube-apiserver 无法启动与 TLS 认证失败
1. 检查 etcd 是否正常存活（`systemctl status etcd`）。
2. 查看日志 `/opt/kube-apiserver/logs/kube-apiserver.log`。
3. 检查 apiserver 服务端证书 SAN 列表中是否漏配了 Master 节点 IP 或 VIP。
4. **双向 TLS 认证错误 (mTLS Handshake Fail)**：若出现类似 `remote error: tls: bad certificate` 或 `x509: certificate signed by unknown authority` 报错，立即校验 `/etc/kubernetes/ssl/etcd-client.pem` 及其私钥是否由同一 etcd CA 证书合法签发。
5. **审计策略异常**：校验 `/etc/kubernetes/audit-policy.yaml` 缩进与 YAML 规范。

### 9.3 kubelet 启动正常但 Node 持续 NotReady
1. 检查是否由于未部署 CNI 网络插件导致（`kubectl describe node <name>` 查看 `NetworkReady` 指标）。
2. 检查 `containerd` 与 `kubelet` 的 **Cgroup 驱动是否完全一致**（若一端为 `systemd` 另一端为 `cgroupfs`，将引发周期性失联与无法就绪）。
3. 检查 `dmesg` 或 `journalctl -u kubelet` 确认是否存在 Swap 未关闭导致的强制退出。

---

## 10. 关键文件索引

| 文件 | 说明 |
|---|---|
| `0002-common-kubeconfig.yml` | CA、SA 密钥、etcd mTLS 专属凭证与各种 kubeconfig 生成入口 |
| `0001-download-binaries.yml` | 本地缓存预热入口，统一下载 cfssl / kubectl / Kubernetes / containerd / CNI / Calico 等资源 |
| `0005-install-lb.yml` | nginx + keepalived 负载均衡集群部署入口 |
| `0010-create-manager-set.yml` | etcd 专属安全集群与 Kubernetes 控制面部署入口 |
| `0012-manager-set-kube.yml` | 控制面节点 kubelet/containerd 部署入口 |
| `0020-create-compute-set.yml` | 工作节点 kubelet/containerd 部署入口 |
| `0030-install-cni.yml` | CNI 网络插件、kube-proxy 与 CoreDNS 部署入口 |
| `roles/kubeconfig` | CA、SA、front-proxy、kube-proxy、etcd-client 证书及各 kubeconfig 渲染与分发 |
| `roles/lb` | Nginx 4层代理与 Keepalived 双向健康监控配置 |
| `roles/etcd` | etcd 二进制部署、集群组建与安全 mTLS 参数配置 |
| `roles/kube_master` | APIServer (安全审计+etcd TLS)、Controller-Manager、Scheduler 部署与 HA 配置 |
| `roles/kubelet` | Kubelet 部署与 Containerd 对齐配置 |
| `roles/cni` | CNI 网络基础二进制与模板（如 Calico）下发 |
| `roles/download` | 按 `inventories/group_vars/all.yml` 版本下载本地二进制与清单缓存到 `files/<arch>/` |
| `roles/preflight_cache` | 在依赖缓存的入口 playbook 执行前检查必需文件是否存在 |
