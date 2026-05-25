# 安全加固待办清单

本文档记录当前项目需要继续推进的安全加固项。GitHub Issues 未开启时，先以仓库文档方式跟踪。

## P0：CA 私钥离线化

### 背景

生产环境中，根 CA 私钥和 front-proxy CA 私钥只应保留在离线控制机或专用证书管理节点，不应分发到 Master 节点。

### 风险

如果 Master 节点持有根 CA 私钥，一旦 Master 被入侵，攻击者可以签发任意 Kubernetes 客户端或服务端证书，绕过集群身份边界。

### 改造目标

- Master 节点只保留运行控制面所需证书和私钥。
- CA 私钥只用于本地签发阶段。
- 后续组件证书签发、续期、轮换都通过控制机或专用证书管理流程执行。

### 建议保留到 Master 的文件

```text
ca.pem
sa.key
sa.pub
admin.pem
admin-key.pem
etcd-client.pem
etcd-client-key.pem
front-proxy-ca.pem
front-proxy-client.pem
front-proxy-client-key.pem
apiserver.pem
apiserver-key.pem
```

### 禁止分发到 Master 的文件

```text
ca-key.pem
front-proxy-ca-key.pem
```

### 验收标准

- Master 节点 `/etc/kubernetes/ssl` 不包含 `ca-key.pem` 和 `front-proxy-ca-key.pem`。
- kube-apiserver、kube-controller-manager、kube-scheduler 正常启动。
- 后续证书签发仍可在控制机完成。
- 文档明确说明 CA 私钥边界。

## P1：apiserver 安全参数增强

建议逐步补充：

```text
--anonymous-auth=false
--profiling=false
--enable-aggregator-routing=true
--event-ttl=1h
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml
--kubelet-client-certificate=/etc/kubernetes/ssl/apiserver-kubelet-client.pem
--kubelet-client-key=/etc/kubernetes/ssl/apiserver-kubelet-client-key.pem
--kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP
```

## P1：Secret 静态加密

- 新增 encryption config 模板。
- 生成并保护 encryption provider key。
- apiserver 挂载并启用 `--encryption-provider-config`。
- 增加 Secret 重写流程，确保历史 Secret 也被加密。

## P1：证书续期与轮换

- 拆分 CA 有效期和组件证书有效期。
- 增加 `0400-renew-certs.yml`。
- 增加 `0410-rotate-sa-key.yml`。
- 增加 kubelet client/server 证书轮换策略。

## P2：运行时暴露面收敛

- 收敛 kubelet healthz 监听地址。
- 收敛 kube-proxy metrics 监听地址。
- 根据环境决定是否暴露 controller-manager / scheduler metrics。
- 审计策略按 Metadata / RequestResponse 分级。

## P2：供应链安全

- 为下载的二进制包增加 checksum。
- 对镜像版本做明确锁定。
- 增加下载失败重试、超时和离线校验。
