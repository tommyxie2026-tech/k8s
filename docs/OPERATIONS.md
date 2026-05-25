# 部署与运维执行规范

本文档用于约束项目的实际执行顺序、安全边界和运维检查项。

## 模式定位

### machine 模式

`node_type=machine` 用于物理机或虚拟机部署，是项目的主路径。该模式会执行内核模块、sysctl、防火墙、Swap、Chrony、Keepalived 等宿主级配置。

### container 模式

`node_type=container` 仅用于开发、CI、演示和本地验证。该模式通过 Docker API 管理 systemd 容器，不需要 SSH，不应作为生产运行形态。

容器模式可能使用 privileged 容器和宿主 cgroup 挂载，因此只能用于隔离的开发或测试环境。

## 推荐执行顺序

### 物理机 / 虚拟机

```bash
INV="-i inventories/hosts.yml"

ansible-playbook $INV 0000-preflight.yml
ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0020-create-compute-set.yml
ansible-playbook $INV 0030-install-cni.yml
```

### 容器模式

```bash
INV="-i inventories/hosts-container.yml"

ansible-playbook $INV 0000-container-infra.yml
ansible-playbook $INV 0000-preflight.yml
ansible-playbook $INV 0001-download-binaries.yml
ansible-playbook $INV 0000-common-service.yml
ansible-playbook $INV 0002-common-kubeconfig.yml
ansible-playbook $INV 0005-install-lb.yml
ansible-playbook $INV 0010-create-manager-set.yml
ansible-playbook $INV 0012-manager-set-kube.yml
ansible-playbook $INV 0020-create-compute-set.yml
ansible-playbook $INV 0030-install-cni.yml
```

## 部署前必须确认

- inventory 中的 IP、VIP、网卡名、CIDR 与真实环境一致。
- `MASTER_CERT_HOSTS` 覆盖所有 master IP、VIP、kubernetes service IP 和内置 DNS 名称。
- 目标节点没有旧的 kube-apiserver、etcd、kubelet、containerd 进程或端口冲突。
- 生产环境不要提交真实 inventory、证书、私钥、kubeconfig、二进制缓存。
- 生产环境应将 CA 私钥保留在离线控制机或专用证书管理节点，不应分发到 master。

## 基础验收命令

部署完成后至少执行：

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get componentstatuses || true
kubectl -n kube-system get ds,deploy,svc
```

建议再执行一个最小业务验证：

```bash
kubectl create deployment smoke-nginx --image=nginx:alpine
kubectl expose deployment smoke-nginx --port=80 --target-port=80
kubectl run smoke-client --rm -it --image=curlimages/curl --restart=Never -- curl -s http://smoke-nginx.default.svc.cluster.local
kubectl delete svc smoke-nginx
kubectl delete deployment smoke-nginx
```

## 运维改造优先级

1. 安全基线：移除弱默认配置、保护私钥、忽略生成物。
2. 稳定性：preflight、幂等化、reset/cleanup。
3. 可验证：语法检查、容器模式 smoke test、CI。
4. 生产化：证书轮换、etcd 备份恢复、Secret 静态加密、HA 故障演练。
