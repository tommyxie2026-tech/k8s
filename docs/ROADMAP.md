# Kubernetes 二进制部署项目完善计划

本文档基于当前项目 review 结果，将改造分为三个阶段：先安全止血，再提升可重复部署能力，最后补齐生产化能力。

## 阶段一：安全止血与项目基线

目标：先消除高风险默认配置，让项目可以安全地作为可复用模板继续演进。

### 已完成

- 移除容器基础镜像中的 `openssh-server`、root 空密码和 SSH 登录配置。
- 增加 `.gitignore`，避免提交二进制缓存、证书、私钥、kubeconfig、本地 inventory 和临时日志。

### 待完成

- 增加 `0000-preflight.yml`，在正式部署前检查控制机、目标节点、端口、系统能力和依赖。
- 修正 README 与变量文件中的组件版本不一致问题。
- 明确声明 container 模式仅用于开发、CI 和演示，不作为生产运行形态。
- 将真实生产 inventory 与示例 inventory 分离，避免把真实 IP、VIP、网卡和证书路径提交到仓库。

## 阶段二：可重复部署与自动验证

目标：让部署过程更稳定、更幂等，并能通过 CI 或本地容器模式做基础回归。

### 待完成

- 减少 `shell` 使用，优先改为 `unarchive`、`copy`、`template`、`command` 等 Ansible 原生模块。
- 为必须使用 shell 的任务增加 `set -euo pipefail` 或明确失败条件。
- 为下载任务增加 checksum、timeout、retries。
- 增加 `reset` / `cleanup` playbook，支持销毁容器实验集群和清理节点状态。
- 增加 container 模式 smoke test：
  - `kubectl get nodes`
  - `kubectl get pods -A`
  - 创建测试 Pod / Service
  - 验证 DNS 与 Service 访问
- 增加 GitHub Actions 或本地 CI 脚本，至少验证 Ansible 语法、YAML 格式和容器模式基础流程。

## 阶段三：生产化能力补齐

目标：让项目从可演示模板升级为更接近生产交付的二进制部署方案。

### 待完成

- CA 私钥离线化：禁止将 `ca-key.pem`、`front-proxy-ca-key.pem` 分发到 Master 节点。
- 增加证书续期和轮换 playbook。
- 增加 etcd snapshot / restore playbook。
- 增加 apiserver encryption config，用于 Secret 静态加密。
- 增加 HA 故障演练文档：
  - Master 节点故障
  - VIP 漂移
  - etcd 单节点故障
  - Worker 节点恢复
- 增加安全加固项：
  - `--anonymous-auth=false`
  - `--profiling=false`
  - kubelet client certificate 独立配置
  - 审计策略分级
  - metrics / healthz 暴露面收敛

## 建议执行顺序

1. 先完成阶段一，保证项目不会继续传播高风险默认配置。
2. 再进入阶段二，保证部署流程稳定、可回归、可重复。
3. 最后进入阶段三，将证书、备份、加密、故障恢复和安全加固补齐。

## 质量门禁

每次改动至少满足以下条件之一：

- Ansible 语法检查通过。
- container 模式 smoke test 通过。
- README / ROADMAP / inventory 示例与变量保持一致。
- 对安全相关变更给出明确回滚方式。
