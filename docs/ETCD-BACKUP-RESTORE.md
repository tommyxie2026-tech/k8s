# etcd 备份与恢复

本文档说明 etcd snapshot 与 restore 的设计边界。etcd 恢复属于高风险操作，必须在明确故障场景、备份文件和恢复目标后执行。

## 备份

使用：

```bash
ansible-playbook -i inventories/hosts.yml 0040-etcd-snapshot.yml
```

默认会在每个 etcd 节点生成本地快照：

```text
/var/backups/etcd/etcd-snapshot-<timestamp>.db
```

## 备份建议

- 至少保留最近 3 份成功 snapshot。
- 将 snapshot 复制到集群外部存储。
- 每次重大升级前必须执行 snapshot。
- 每次 reset / destroy etcd data 前必须执行 snapshot。
- 定期执行 snapshot status 校验。

## 恢复原则

etcd restore 不应作为普通 playbook 自动执行，原因：

- restore 会重建 member 数据目录。
- restore 可能改变 cluster token / member identity。
- 错误恢复可能导致 Kubernetes API 数据回滚或丢失。
- 多 member 恢复需要严格保证所有成员使用同一份一致 snapshot。

## 推荐恢复流程

1. 停止 kube-apiserver，避免继续写入 etcd。
2. 停止所有 etcd member。
3. 备份当前坏数据目录。
4. 在每个 etcd 节点使用同一份 snapshot 执行 restore。
5. 使用新的 data-dir 替换旧 data-dir。
6. 启动 etcd 集群。
7. 验证 etcd endpoint health。
8. 启动 kube-apiserver。
9. 验证 Kubernetes 资源一致性。

## 后续建议实现

可新增一个强确认恢复 playbook：

```text
0041-etcd-restore.yml
```

必须要求以下变量：

```yaml
confirm_restore_etcd: true
etcd_restore_snapshot_file: "/var/backups/etcd/xxx.db"
etcd_restore_new_cluster_token: "k8s-etcd-restore-<date>"
```

并且必须在执行前输出：

- 当前节点
- 将使用的 snapshot 文件
- 将替换的数据目录
- 是否已停止 kube-apiserver
- 是否已停止所有 etcd member

## 验收命令

```bash
ETCDCTL_API=3 etcdctl \
  --cacert=/etc/etcd/ssl/ca.pem \
  --cert=/etc/etcd/ssl/etcd.pem \
  --key=/etc/etcd/ssl/etcd-key.pem \
  --endpoints=https://127.0.0.1:2379 \
  endpoint health

kubectl get nodes
kubectl get pods -A
```
