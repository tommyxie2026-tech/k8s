# 从源码 Tag 编译默认二进制

本文档描述如何通过 `repo/sources.yml` 引用源码仓库和 tag，并在 CI 中编译默认二进制产物。

## 目标

- 每个默认二进制都有明确源码仓库和 tag 来源。
- 可以将源码仓库替换为内部 GitLab mirror。
- CI 可从源码构建 `files/<arch>/`。
- 产物仍通过 `binary-cache/<arch>` 分支和 Git LFS 管理。
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
```

## Source Manifest

核心文件：

```text
repo/sources.yml
```

每个组件声明：

```yaml
component: kubernetes
version: "1.36.1"
git: "https://github.com/kubernetes/kubernetes.git"
tag: "v1.36.1"
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

## CI 工作流

手动运行：

```text
Build default binaries
```

参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `arch` | `amd64` | 目标架构，例如 `amd64` 或 `arm64` |
| `stage` | `stage1-light` | 分阶段构建入口 |
| `components` | 空 | `stage=custom` 时传入组件列表 |
| `target_branch` | `binary-cache/amd64` | 编译产物提交分支 |
| `commit_changes` | `true` | 是否提交产物 |
| `strict_package` | `false` | 是否要求完整部署归档全部存在 |

## 分阶段 CI 构建顺序

为了通过 CI 逐步完成构建，建议按下面顺序手动运行同一个 workflow。所有阶段使用同一个 `target_branch`，workflow 会先从目标缓存分支恢复已有 `files/<arch>/`，再增量构建当前阶段的组件，最后重新生成 `SHA256SUMS` 和 `download-checksums-<arch>.yml`。

### 阶段一：轻量组件

```text
arch=amd64
stage=stage1-light
target_branch=binary-cache/amd64
commit_changes=true
strict_package=false
```

该阶段构建：

```text
cfssl,runc
```

目标：验证 CI、Git LFS、源码 tag checkout、构建脚本和缓存分支提交链路。

### 阶段二：CNI 与 etcd

```text
arch=amd64
stage=stage2-core
target_branch=binary-cache/amd64
commit_changes=true
strict_package=false
```

该阶段构建：

```text
cni-plugins,etcd
```

目标：补齐 CNI 归档包与 etcd release-like 包。

### 阶段三：containerd

```text
arch=amd64
stage=stage3-runtime
target_branch=binary-cache/amd64
commit_changes=true
strict_package=false
```

该阶段构建：

```text
containerd
```

目标：补齐 containerd release-like 包。

### 阶段四：Kubernetes

```text
arch=amd64
stage=stage4-kubernetes
target_branch=binary-cache/amd64
commit_changes=true
strict_package=true
```

该阶段构建：

```text
kubernetes
```

此阶段会恢复前面阶段已提交的产物，因此 `strict_package=true` 可以用于校验最终部署所需归档是否完整。

## 自定义阶段

如果需要只构建某几个组件：

```text
arch=amd64
stage=custom
components=cfssl,runc
target_branch=binary-cache/amd64-test
commit_changes=true
strict_package=false
```

如果需要一次性全部构建：

```text
stage=all
strict_package=true
```

不建议第一次就使用 `stage=all`，尤其是 GitHub hosted runner。

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
