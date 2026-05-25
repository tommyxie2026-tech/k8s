# 默认二进制缓存

项目支持将默认版本的 Kubernetes、etcd、containerd、runc、CNI、cfssl、kubectl、Calico manifest 等二进制和清单下载到仓库的 `files/<arch>/` 目录，并通过 Git LFS 跟踪。

## 目录规则

```text
files/
  amd64/
    cfssl
    cfssljson
    kubectl
    etcd-v<version>-linux-amd64.tar.gz
    kubernetes-server-linux-amd64.tar.gz
    kubernetes-node-linux-amd64.tar.gz
    containerd-<version>-linux-amd64.tar.gz
    runc
    containerd.service
    cni-plugins-linux-amd64-v<version>.tgz
    calico.yaml
    SHA256SUMS
```

后续可增加：

```text
files/arm64/
```

## 触发下载

在 GitHub Actions 中手动运行：

```text
Cache default binaries
```

输入：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `arch` | `amd64` | 目标架构，例如 `amd64` 或 `arm64` |
| `commit_changes` | `true` | 是否自动提交下载结果 |

工作流会执行：

```bash
bash scripts/download-default-binaries.sh
```

然后将 `files/<arch>/` 下的文件提交回仓库。

## 本地下载

也可以在本地运行：

```bash
ARCH=amd64 bash scripts/download-default-binaries.sh
```

可覆盖默认版本：

```bash
ARCH=amd64 \
KUBERNETES_VERSION=1.36.1 \
ETCD_VERSION=3.6.11 \
CONTAINERD_VERSION=2.3.0 \
bash scripts/download-default-binaries.sh
```

## Git LFS

`.gitattributes` 已配置：

```text
files/**/* filter=lfs diff=lfs merge=lfs -text
```

因此默认二进制缓存会通过 Git LFS 跟踪，避免大文件直接进入普通 Git 对象。

> 注意：GitHub LFS 有流量和存储配额限制。若默认二进制总量较大，建议确认仓库的 LFS 配额，或只缓存 `amd64` 的核心生产版本。

## 与 download role 的关系

`roles/download` 默认会下载缺失文件到 `files/<arch>/`。当仓库中已经缓存默认二进制时，部署流程可以直接复用这些文件，适合离线部署或受限网络环境。

可选变量：

```yaml
download_dir: "{{ playbook_dir }}/files"
download_arch_dir: "{{ download_dir }}/{{ target_arch }}"
offline_binary_cache_only: false
```

后续可以将 `offline_binary_cache_only` 设为 `true`，使部署严格依赖仓库内缓存，不允许联网下载缺失文件。

## 校验

下载脚本会生成：

```text
files/<arch>/SHA256SUMS
```

用于记录当前缓存文件的 sha256 摘要。后续可将其与 `download_checksums` 变量联动，实现更严格的供应链校验。
