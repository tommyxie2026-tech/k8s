# 单节点物理机模式

单节点物理机模式用于在一台物理机或虚拟机上同时运行 etcd、Kubernetes 控制面、containerd、kubelet、CNI、CoreDNS 和 kube-proxy。

该模式定位为：

```text
PoC
边缘节点
小型离线环境
开发验证
非高可用小规模交付
```

不适合：

```text
生产高可用控制面
etcd quorum 容错
Master 节点故障容忍
多节点业务承载
```

## 拓扑

```text
single-01
  ├── etcd
  ├── kube-apiserver
  ├── kube-controller-manager
  ├── kube-scheduler
  ├── nginx local apiserver proxy
  ├── containerd
  ├── kubelet
  ├── kube-proxy
  ├── Calico
  └── CoreDNS
```

单节点模式保留 Nginx 本地代理，统一组件访问入口：

```text
https://<single-node-ip>:8443
```

但会跳过 Keepalived，因为没有 VIP 漂移需求。

## Inventory

默认示例：

```text
inventories/hosts-single.yml
```

部署前需要修改：

```yaml
ansible_host: 192.168.1.10
LB_APISERVER_VIP: 192.168.1.10
LB_INTERFACE: eth0
MASTER_CERT_HOSTS:
  - 192.168.1.10
```

其中 `ansible_host`、`LB_APISERVER_VIP`、`MASTER_CERT_HOSTS` 必须覆盖实际单节点 IP。

## 部署

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

`0031-single-node-post.yml` 会：

- 移除 control-plane taint。
- 移除 master taint。
- 给节点增加 `node-role.kubernetes.io/single` 标签。
- 等待节点 Ready。

## 验证

```bash
kubectl get nodes -o wide
kubectl get pods -A
KUBECONFIG_PATH=/root/.kube/config make smoke-test
```

## 风险边界

- 单节点 etcd 没有 quorum 容错。
- 单节点宕机后控制面和业务都会不可用。
- etcd snapshot 更重要，建议定期执行：

```bash
ansible-playbook -i inventories/hosts-single.yml 0040-etcd-snapshot.yml
```

- 不建议将该模式标记为 HA 生产模式。
