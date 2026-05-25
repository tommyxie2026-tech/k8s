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
| `components` | `all` | 组件列表，逗号分隔，例如 `cfssl,runc` |
| `target_branch` | `binary-cache/amd64` | 编译产物提交分支 |
| `commit_changes` | `true` | 是否提交产物 |

示例：

```text
arch=amd64
components=cfssl,runc,cni-plugins
target_branch=binary-cache/amd64-build-test
commit_changes=true
```

## 本地执行

```bash
python3 -m pip install pyyaml
ARCH=amd64 BUILD_COMPONENTS=cfssl,runc bash scripts/build-default-binaries.sh
```

全部构建：

```bash
ARCH=amd64 BUILD_COMPONENTS=all bash scripts/build-default-binaries.sh
```

输出：

```text
files/amd64/
  cfssl
  cfssljson
  runc
  ...
  SHA256SUMS
```

## 推荐落地顺序

因为 Kubernetes、containerd、etcd 编译较重，不建议第一次就 `components=all`。

建议分阶段：

### 阶段一：轻量组件验证

```text
components=cfssl,runc
```

目标：验证 manifest、CI、Git LFS、缓存分支提交链路。

### 阶段二：CNI 与 etcd

```text
components=cni-plugins,etcd
```

目标：验证 Go 多模块项目构建和归档逻辑。

### 阶段三：containerd

```text
components=containerd
```

目标：验证运行时构建依赖，例如 libseccomp。

### 阶段四：Kubernetes

```text
components=kubernetes
```

Kubernetes 编译最重，建议使用 self-hosted runner 或更大规格 runner。

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

后续可以将 `SHA256SUMS` 自动转换为 `download_checksums`，让部署过程强制校验。

## 风险与注意事项

- `repo/sources.yml` 中的版本必须与 `inventories/group_vars/all.yml` 保持一致。
- Kubernetes 构建命令可能随上游版本变化，需要随版本升级验证。
- 不同组件对 Go 版本、libseccomp、make、bash 等依赖不同。
- GitHub hosted runner 可能不适合全量 Kubernetes 编译。
- 内部 GitLab mirror 应定期同步 tag，并禁止随意改写 tag。
