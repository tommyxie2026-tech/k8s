# 单节点升级为 HA 集群方案

本文档描述如何将 `cluster_mode=single` 的单节点物理机集群升级为多 master / 多 etcd 的 HA 集群。

该能力定位为高风险迁移能力，必须先完成 preflight、备份和人工确认，再进入 etcd 与 control plane 扩容。

## 目标

将现有单节点：

```text
single-01
  ├── etcd
  ├── kube-apiserver
  ├── kube-controller-manager
  ├── kube-scheduler
  ├── nginx local apiserver proxy
  ├── containerd
  ├── kubelet
  └── workloads
```

升级为：

```text
master-01
  ├── etcd
  ├── kube-apiserver
  ├── kube-controller-manager
  ├── kube-scheduler
  ├── nginx
  └── keepalived

master-02
  ├── etcd
  ├── kube-apiserver
  ├── kube-controller-manager
  ├── kube-scheduler
  ├── nginx
  └── keepalived

master-03
  ├── etcd
  ├── kube-apiserver
  ├── kube-controller-manager
  ├── kube-scheduler
  ├── nginx
  └── keepalived

worker-01...
  ├── containerd
  ├── kubelet
  └── kube-proxy
```

升级后统一入口：

```text
https://<LB_APISERVER_VIP>:8443
```

## 不变量

升级过程中必须保持不变：

```text
CA
front-proxy CA
service account signing key
encryption-config key
SERVICE_CIDR
CLUSTER_CIDR
CLUSTER_DNS_SVC_IP
CLUSTER_DOMAIN
现有 etcd 数据
现有 kube-system 资源
```

允许变化：

```text
MASTER_CERT_HOSTS
LB_APISERVER_VIP
etcd member 数量
kube_master 节点数量
compute_servers 节点数量
kubeconfig server endpoint
```

## 具体执行计划

### 阶段 0：冻结变更与前置确认

目标：确保当前单节点集群处于可迁移状态。

执行内容：

1. 暂停业务发布和控制面变更。
2. 确认当前集群是单节点模式。
3. 确认 etcd 当前只有 1 个 member。
4. 确认 apiserver、controller-manager、scheduler、kubelet 正常。
5. 确认目标 HA inventory 已准备完成。
6. 确认 3 个 master 节点网络互通。
7. 确认 VIP 未被占用。
8. 确认 `MASTER_CERT_HOSTS` 包含 VIP、所有 master IP、原单节点 IP 和 Kubernetes 内置 DNS 名称。

对应 playbook：

```text
0050-single-to-ha-preflight.yml
```

### 阶段 1：备份

目标：确保升级失败时可以恢复。

必须备份：

```text
etcd snapshot
local_cluster_config_dir
/etc/kubernetes/pki
encryption-config.yaml
所有 kubeconfig
当前 node / pod / service / endpoint 状态
```

推荐备份目录：

```text
backup/single-to-ha/<timestamp>/
```

可复用：

```text
0040-etcd-snapshot.yml
```

后续将新增专用备份 playbook。

### 阶段 2：扩容 etcd，从 1 member 到 3 member

目标：保留原 etcd 数据，将 etcd 扩容为 3 member。

原则：

```text
一次只 add 一个 member
add 后立即启动新 member
新 member healthy 后再 add 下一个
失败时必须 remove 失败 member
```

执行顺序：

1. 在 master-01 上读取当前 member list。
2. `etcdctl member add master-02 --peer-urls=https://<master-02-ip>:2380`。
3. 在 master-02 上以 `initial-cluster-state=existing` 启动 etcd。
4. 检查 2 member healthy。
5. `etcdctl member add master-03 --peer-urls=https://<master-03-ip>:2380`。
6. 在 master-03 上以 `initial-cluster-state=existing` 启动 etcd。
7. 检查 3 member healthy。

计划新增：

```text
0051-expand-etcd-members.yml
roles/etcd_member_expand
```

### 阶段 3：重新签发 apiserver 证书

目标：使 apiserver 证书支持 VIP 和所有 master IP。

只允许更新：

```text
apiserver.pem
apiserver-key.pem
```

不允许替换：

```text
ca.pem
ca-key.pem
front-proxy-ca.pem
front-proxy-ca-key.pem
sa.key
sa.pub
encryption-config.yaml
```

计划新增：

```text
0052-renew-apiserver-cert-for-ha.yml
```

### 阶段 4：扩容 control plane

目标：在 master-02 和 master-03 安装并启动控制面组件。

执行内容：

1. 安装 containerd / runc。
2. 分发 PKI。
3. 分发 kubeconfig。
4. 安装 kube-apiserver。
5. 安装 kube-controller-manager。
6. 安装 kube-scheduler。
7. 启动服务。
8. 检查每个 master 的 `/readyz`。

apiserver etcd endpoint 应切换为：

```text
https://master-01:2379,https://master-02:2379,https://master-03:2379
```

计划新增：

```text
0053-expand-control-plane.yml
```

### 阶段 5：启用 HA LB

目标：在 3 个 master 上启用 Nginx + Keepalived，提供统一 VIP 入口。

执行内容：

1. 在 master 节点安装 Nginx。
2. 在 master 节点安装 Keepalived。
3. 配置 VIP。
4. 配置 Nginx upstream 到 3 个 apiserver。
5. 验证 VIP 可访问。

验证命令：

```bash
curl -k https://<LB_APISERVER_VIP>:8443/readyz
```

计划新增：

```text
0054-enable-ha-lb.yml
```

### 阶段 6：切换 kubeconfig 到 VIP

目标：所有组件和管理员 kubeconfig 统一使用 HA 入口。

切换前置条件：

```text
3 个 apiserver ready
Nginx upstream 正常
Keepalived VIP 正常
VIP /readyz 正常
```

需要更新：

```text
admin.kubeconfig
controller-manager.kubeconfig
scheduler.kubeconfig
kubelet bootstrap kubeconfig
kube-proxy kubeconfig
```

计划新增：

```text
0055-switch-kubeconfigs-to-vip.yml
```

### 阶段 7：扩容 worker

目标：将业务负载从原单节点迁移到 worker，或增加业务承载能力。

可复用：

```text
0020-create-compute-set.yml
```

计划新增包装入口：

```text
0056-expand-workers.yml
```

### 阶段 8：收尾与角色转换

目标：将原 single 节点转为 master-01，清理 single 标记，按策略处理 master 调度。

默认生产策略：master 不承载业务 Pod。

执行内容：

```text
移除 node-role.kubernetes.io/single
添加/确认 control-plane role
给 master 节点加 control-plane NoSchedule taint
检查 kube-system
检查业务 Pod
检查 endpoints kubernetes
```

计划新增：

```text
0057-finalize-ha-migration.yml
```

## 自动化落地计划

### 第一批实现

本批先实现低风险能力，不修改 etcd 数据：

```text
docs/SINGLE-TO-HA.md
inventories/hosts-ha-from-single.yml
0050-single-to-ha-preflight.yml
0050-single-to-ha.yml
Makefile migrate-single-to-ha-preflight 入口
```

### 第二批实现

实现备份和 etcd 扩容：

```text
0051-expand-etcd-members.yml
roles/etcd_member_expand
etcd existing cluster service 模板支持
失败 member remove 逻辑
```

### 第三批实现

实现控制面扩容和 VIP 切换：

```text
0052-renew-apiserver-cert-for-ha.yml
0053-expand-control-plane.yml
0054-enable-ha-lb.yml
0055-switch-kubeconfigs-to-vip.yml
```

### 第四批实现

实现 worker 扩容和最终收尾：

```text
0056-expand-workers.yml
0057-finalize-ha-migration.yml
完整 smoke test
文档化回滚流程
```

## 风险边界

### etcd 风险

etcd 扩容是最高风险阶段。必须保证：

```text
扩容前有 snapshot
每次只 add 一个 member
member add 后必须启动成功
失败时必须 member remove
不得直接用 new cluster 覆盖已有数据目录
```

### 证书风险

`MASTER_CERT_HOSTS` 不完整会导致 TLS 失败。

必须包含：

```text
LB_APISERVER_VIP
所有 master IP
原 single 节点 IP
127.0.0.1
10.96.0.1
kubernetes
kubernetes.default
kubernetes.default.svc
kubernetes.default.svc.cluster.local
```

### kubeconfig 切换风险

不得在 VIP ready 前切换 kubeconfig。

正确顺序：

```text
3 master apiserver ready
LB ready
VIP ready
VIP /readyz 通过
切换 kubeconfig
```

### 业务负载风险

如果原 single 节点已有业务负载，建议升级前先评估：

```bash
kubectl get pods -A -o wide
```

生产场景建议扩容 worker 后，再给 master 加 taint。

## 回滚原则

### preflight 阶段

只读检查，不需要回滚。

### etcd 扩容阶段

如果新 member 未健康：

```bash
etcdctl member remove <member-id>
```

保留 master-01 原数据目录，不得清空。

### control plane 扩容阶段

新 master 异常时：

```bash
systemctl stop kube-apiserver kube-controller-manager kube-scheduler
```

不影响原 single/master-01。

### LB 阶段

VIP 异常时：

```bash
systemctl stop keepalived nginx
```

暂不切 kubeconfig。

### kubeconfig 切换阶段

如 VIP 异常，回切 server：

```text
https://<master-01-ip>:8443
```

## 验收标准

升级完成后必须通过：

```bash
etcdctl endpoint health --cluster
etcdctl member list
kubectl get nodes -o wide
kubectl get pods -A
kubectl get endpoints kubernetes
curl -k https://<LB_APISERVER_VIP>:8443/readyz
```

期望：

```text
etcd 3 member healthy
3 个 kube-apiserver ready
controller-manager leader 正常
scheduler leader 正常
VIP 可访问
kube-system 全部 Running
worker 可调度
原有业务 Pod 正常
```
