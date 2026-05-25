# 机器模式 Reset / Cleanup 设计

机器模式不同于容器模式，不能简单删除节点。Reset 必须明确区分“停止服务”“清理运行数据”“清理证书”“清理二进制”“保留备份”等级，避免误删生产数据。

## 目标

提供可控、分级、默认安全的机器模式清理流程。

## 清理级别

### level 1：停止服务

仅停止 Kubernetes 与 etcd 相关服务，不删除任何数据。

适用场景：

- 临时维护
- 准备替换配置
- 故障定位

涉及服务：

```text
kube-apiserver
kube-controller-manager
kube-scheduler
kubelet
kube-proxy
containerd
etcd
nginx
keepalived
```

### level 2：清理运行状态

停止服务后清理运行时状态，但保留证书、kubeconfig 和二进制。

候选路径：

```text
/var/lib/kubelet
/var/lib/cni
/etc/cni/net.d
/opt/cni/bin
/var/log/kubernetes
/run/containerd
```

### level 3：清理集群身份与配置

清理证书、kubeconfig、systemd unit 和 kube 相关配置。

候选路径：

```text
/etc/kubernetes
/etc/systemd/system/kube-apiserver.service
/etc/systemd/system/kube-controller-manager.service
/etc/systemd/system/kube-scheduler.service
/etc/systemd/system/kubelet.service
/etc/systemd/system/kube-proxy.service
```

该级别必须要求显式变量：

```yaml
confirm_destroy_cluster_identity: true
```

### level 4：清理 etcd 数据

清理 etcd 数据是高风险操作，必须单独开关，不应隐式包含在任何 reset 中。

候选路径：

```text
/var/lib/etcd
/etc/etcd
```

必须要求：

```yaml
confirm_destroy_etcd_data: true
```

并且执行前必须提示先完成 snapshot。

## 建议 playbook 设计

```text
0090-stop-services.yml
0091-reset-node-runtime.yml
0092-reset-cluster-identity.yml
0093-destroy-etcd-data.yml
```

## 默认安全原则

- 默认不删除 etcd 数据。
- 默认不删除 CA、组件证书和 kubeconfig。
- 默认不删除二进制文件。
- 所有破坏性操作必须显式确认变量。
- 所有删除动作尽量使用路径白名单。
- 删除前输出将要删除的路径。

## 后续实现顺序

1. 先实现 `0090-stop-services.yml`。
2. 再实现 `0091-reset-node-runtime.yml`。
3. 最后实现带强确认的 `0092` 和 `0093`。
