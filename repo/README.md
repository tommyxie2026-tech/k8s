# Source Repository Manifest

`repo/` 目录用于声明默认二进制对应的源码仓库、tag 与构建方式。

目标：

- 不再只依赖上游 release 下载。
- CI 可以按版本 tag 拉取源码并编译默认二进制。
- 编译产物统一进入 `files/<arch>/`。
- 编译缓存仍通过 `binary-cache/<arch>` 分支或 Git LFS 管理。

## 文件说明

```text
repo/
  sources.yml
```

`sources.yml` 是单一来源，描述每个组件：

- component：组件名
- version：默认版本
- git：源码仓库地址，可使用 GitHub 或 GitLab 镜像
- tag：源码 tag
- build：构建方式
- outputs：构建产物映射到 `files/<arch>/`

## 推荐工作流

```text
repo/sources.yml
        ↓
scripts/build-default-binaries.sh
        ↓
files/<arch>/
        ↓
.github/workflows/build-default-binaries.yml
        ↓
binary-cache/<arch>
```

## GitLab 镜像

如果你希望所有源码来自 GitLab，可将 `git` 字段替换为内部 GitLab 镜像地址，例如：

```yaml
git: "https://gitlab.example.com/mirror/kubernetes/kubernetes.git"
```

CI 不关心仓库来源，只要求 tag 与源码构建方式一致。
