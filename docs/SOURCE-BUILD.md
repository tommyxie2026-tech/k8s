# 从源码 Tag 编译默认二进制

本文档描述如何通过 `repo/sources.yml` 引用源码仓库和 tag，并在 CI 中编译默认二进制产物。

## 目标

- 每个默认二进制都有明确源码仓库和 tag 来源。
- 可以将源码仓库替换为内部 GitLab mirror。
- CI 可从源码构建 `files/<arch>/`。
- 正式发布的产物由经过批准的工作流进入 `binary-cache/<arch>` 分支与 Git LFS；普通构建仅产生短期 Actions Artifacts。
- release 下载与源码构建并存：前者快，后者可审计、可复现。

## 目录结构

```text
repo/
  README.md
  sources.yml

scripts/
  build-default-binaries.sh
  package-built-binaries.sh
  generate-download-checksums.py

.github/workflows/
  build-default-binaries.yml
  cache-default-binaries.yml
  publish-default-binaries.yml
```

## Source Manifest

核心文件：

```text
repo/sources.yml
```

每个组件声明：

```yaml
component: kubernetes
version: "1.36.5"
git: "https://github.com/kubernetes/kubernetes.git"
tag: "v1.36.5"
build:
  type: make
  command: "make ..."
  env:
    KUBE_BUILD_PLATFORMS: "linux/{{ arch }}"
outputs:
  - src: "_output/bin/kubectl"
    dest: "kubectl"
```

如果使用内部 GitLab mirror，把 `git` 替换成：

```yaml
git: "https://gitlab.example.com/mirror/kubernetes/kubernetes.git"
```

## CI 工作流：验证与发布隔离（A09）

从本次改造起，`Build default binaries` 不再承担 Git LFS 回写，所有验证 Job 使用 `contents: read`，不能访问发布凭据。

- **只读源码构建验证**：手动运行 `.github/workflows/build-default-binaries.yml`，选择 `arch`、`stage`（`stage1-light`、`stage2-core`、`stage3-runtime`、`stage4-kubernetes`、`custom`、`all`）、`components`、`restore_cache` 与 `strict_package`。成功后从 Actions Artifacts 下载暂存制品。
- **只读缓存验证**：手动运行 `.github/workflows/cache-default-binaries.yml`，从上游 Release 下载并校验制品，仅上传 Actions Artifacts。
- **受控缓存发布**：手动运行 `.github/workflows/publish-default-binaries.yml`，根据 `source_mode` 选择源码或上游 Release，输入 `PUBLISH` 后由专用 `binary-cache-publish` 环境执行发布 Job。必须先由仓库管理员配置环境必需审批人与环境专属 `BINARY_CACHE_TOKEN`。
- 所有构建逻辑统一于 `.github/actions/prepare-binaries/action.yml`，工作流之间不复制构建步骤。
- **读与写分离**：`restore_cache` 只控制读取旧缓存，写入仅存在于独立发布 Job；前序分阶段构建结果通过 `binary-cache/<arch>` 被复用。

分阶段执行顺序保持不变：`stage1-light` → `stage2-core` → `stage3-runtime` → `stage4-kubernetes`。对应每阶段依次独立授权和发布；Stage 2–4 从**已发布且通过校验**的缓存恢复前阶段产物，Stage 4 启用严格完整性验证。仅在干净工作区构建 Stage 4 并设置 `strict_package=true` 将因依赖归档缺失而失败，这是预期行为。`stage=all` 则可用于一次性完整构建验证。

详细权限边界、配置和回滚参阅 [A09-BUILD-PUBLISH.md](A09-BUILD-PUBLISH.md)。

## 本地执行

```bash
python3 -m pip install pyyaml
ARCH=amd64 BUILD_COMPONENTS=cfssl,runc bash scripts/build-default-binaries.sh
```

完整构建并严格检查部署归档：

```bash
ARCH=amd64 BUILD_COMPONENTS=all STRICT_PACKAGE=true bash scripts/build-default-binaries.sh
```

输出：

```text
files/amd64/
  cfssl
  cfssljson
  runc
  kubernetes-server-linux-amd64.tar.gz
  kubernetes-node-linux-amd64.tar.gz
  etcd-v3.6.11-linux-amd64.tar.gz
  containerd-2.3.0-linux-amd64.tar.gz
  cni-plugins-linux-amd64-v1.9.1.tgz
  SHA256SUMS

inventories/group_vars/download-checksums-amd64.yml
```

## CI 构建后的离线部署

阶段四完成后，在部署机同步缓存分支：

```bash
git lfs install
ARCH=amd64 CACHE_BRANCH=binary-cache/amd64 bash scripts/sync-binary-cache-branch.sh
```

然后执行：

```bash
make deploy-single-offline
```

## Runner 建议

GitHub hosted runner 可用于轻量组件和小规模验证。

Kubernetes 全量构建建议：

```text
self-hosted runner
8 vCPU+
16 GB RAM+
50 GB+ 可用磁盘
稳定网络访问 GitHub/GitLab mirror
Go build cache 持久化
```

## GitLab Mirror 设计

推荐在 GitLab 中维护 mirror：

```text
gitlab.example.com/mirror/kubernetes/kubernetes
gitlab.example.com/mirror/etcd-io/etcd
gitlab.example.com/mirror/containerd/containerd
gitlab.example.com/mirror/opencontainers/runc
gitlab.example.com/mirror/containernetworking/plugins
gitlab.example.com/mirror/cloudflare/cfssl
```

然后修改 `repo/sources.yml` 的 `git` 字段即可。

## 与 release 下载的关系

现有：

```text
scripts/download-default-binaries.sh
.github/workflows/cache-default-binaries.yml
```

用于从 upstream release 下载。

新增：

```text
scripts/build-default-binaries.sh
.github/workflows/build-default-binaries.yml
```

用于从源码 tag 编译。

两套路径可以并存：

| 路径 | 优点 | 缺点 |
|------|------|------|
| Release 下载 | 快、简单、稳定 | 对供应链可控性弱 |
| Source build | 可审计、可复现、适合内网 GitLab | 慢、依赖多、runner 要求高 |

## 产物规范

产物进入：

```text
files/<arch>/
```

并生成：

```text
files/<arch>/SHA256SUMS
```

随后生成：

```text
inventories/group_vars/download-checksums-<arch>.yml
```

## 风险与注意事项

- `repo/sources.yml` 中的版本必须与 `inventories/group_vars/all.yml` 保持一致。
- Kubernetes 构建命令可能随上游版本变化，需要随版本升级验证。
- 不同组件对 Go 版本、libseccomp、make、bash 等依赖不同。
- GitHub hosted runner 可能不适合全量 Kubernetes 编译。
- 内部 GitLab mirror 应定期同步 tag，并禁止随意改写 tag。
