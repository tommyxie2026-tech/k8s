# 默认二进制缓存

项目支持将默认版本的 Kubernetes、etcd、containerd、runc、CNI、cfssl、kubectl、Calico manifest 等二进制和清单下载到 `files/<arch>/` 目录，并通过 Git LFS 跟踪。

为避免主分支持续膨胀，默认二进制缓存推荐提交到独立分支：

```text
binary-cache/<arch>
```

例如：

```text
binary-cache/amd64
binary-cache/arm64
```

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

inventories/group_vars/
  download-checksums-amd64.yml
```

后续可增加：

```text
files/arm64/
inventories/group_vars/download-checksums-arm64.yml
```

## 验证与发布的独立入口

此前 `Build default binaries` 和 `Cache default binaries` 内包含自动回写逻辑。A09 变更后：

| 入口 | 操作 | 权限 |
| --- | --- | --- |
| `Build default binaries` | 从源码 Tag 编译、校验、上传 14 天 Artifacts | `contents: read`，无发布 PAT |
| `Cache default binaries` | 下载上游 Release、校验、上传 14 天 Artifacts | `contents: read`，无发布 PAT |
| `Publish default binary cache` | 手动确认 + 受保护发布 Job，写入 `binary-cache/<arch>` | 仅发布 Job 可访问专用 PAT |

发布前先设置 `binary-cache-publish` GitHub Environment 的必需审查人，使用该环境范围的 `BINARY_CACHE_TOKEN`，并审查缓存分支保护规则。**只创建 Environment 名称并不会自动启用人工审批。**

多阶段源码构建按 Stage 1→2→3→4 顺序发布，后续阶段在只读 Build Job 中使用 `git lfs pull` 恢复前序制品并校验 SHA256SUMS。下载与构建过程共用制品完整性规范，不允许未经授权在验证 Job 中提交缓存。

更多内容见 [A09-BUILD-PUBLISH.md](A09-BUILD-PUBLISH.md)。

## 从缓存分支同步到部署工作区

在部署机上先安装 Git LFS，然后执行：

```bash
git lfs install
ARCH=amd64 CACHE_BRANCH=binary-cache/amd64 bash scripts/sync-binary-cache-branch.sh
```

该脚本会：

1. fetch `binary-cache/<arch>` 分支。
2. 在临时 Git worktree 中执行 `git lfs pull`，恢复真实二进制文件而非 LFS 指针。
3. 校验临时缓存的 SHA256SUMS，然后同步到当前工作区的 `files/<arch>/`。
4. 如果存在 `SHA256SUMS`，自动执行 `sha256sum -c SHA256SUMS`。

如果缓存分支包含 `inventories/group_vars/download-checksums-<arch>.yml`，也建议同步该文件到当前工作区，以便在线下载或离线校验时启用强校验。

## 生成 Ansible checksum 变量

如果本地已有：

```text
files/<arch>/SHA256SUMS
```

可以生成 Ansible 变量文件：

```bash
python scripts/generate-download-checksums.py --arch amd64
```

输出：

```text
inventories/group_vars/download-checksums-amd64.yml
```

格式示例：

```yaml
---
download_checksums:
  cfssl: sha256:<digest>
  cfssljson: sha256:<digest>
  kubectl: sha256:<digest>
  etcd: sha256:<digest>
  kubernetes_server: sha256:<digest>
  kubernetes_node: sha256:<digest>
  containerd: sha256:<digest>
  runc: sha256:<digest>
  containerd_service: sha256:<digest>
  cni_plugins: sha256:<digest>
  calico_manifest: sha256:<digest>
```

`0001-download-binaries.yml` 会自动检查并加载：

```text
inventories/group_vars/download-checksums-{{ target_arch }}.yml
```

存在时，联网下载模式也会启用 `checksum:` 强校验。

## 离线部署模式

当 `files/<arch>/` 已经准备完整，可以启用严格离线模式：

```bash
ansible-playbook -i inventories/hosts-single.yml 0001-download-binaries.yml -e offline_binary_cache_only=true
```

或直接使用 Makefile：

```bash
make deploy-single-offline
make deploy-container-offline
```

`offline_binary_cache_only=true` 时：

- 不访问公网。
- 不执行任何 `get_url` 下载。
- 只检查 `download_expected_files` 是否全部存在。
- 如果存在 `SHA256SUMS`，执行 `sha256sum -c SHA256SUMS`。
- 如果存在 `download-checksums-<arch>.yml`，也会被自动加载。
- 缺失任何必要文件都会立即失败。

## 本地下载

也可以在本地运行：

```bash
ARCH=amd64 bash scripts/download-default-binaries.sh
python scripts/generate-download-checksums.py --arch amd64
```

可覆盖默认版本：

```bash
ARCH=amd64 \
KUBERNETES_VERSION=1.36.5 \
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

`roles/download` 默认会下载缺失文件到 `files/<arch>/`。当工作区中已经同步了默认二进制缓存时，部署流程可以直接复用这些文件，适合离线部署或受限网络环境。

可选变量：

```yaml
download_dir: "{{ playbook_dir }}/files"
download_arch_dir: "{{ download_dir }}/{{ target_arch }}"
offline_binary_cache_only: false
```

设为 `true` 后，download role 会进入严格离线校验模式。

## 校验

下载脚本和源码构建脚本都会生成：

```text
files/<arch>/SHA256SUMS
```

用于记录当前缓存文件的 sha256 摘要。离线模式会自动校验该文件。
