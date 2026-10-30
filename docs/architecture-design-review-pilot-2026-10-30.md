# Architecture Design Review Skill — Kubernetes 试点报告

> 试点日期：2026-10-30（北京时间）  
> 范围：`tommyxie2026-tech/k8s` 的架构、资源操作及二进制交付边界；**仅基于仓库证据进行静态审查**。  
> 审查基线：`master`（审查时基线提交 `e34dfe391c0588b6e551002f68f3d1e415ec5bb7`）；A09 参考方案为开放的 [PR #1](https://github.com/tommyxie2026-tech/k8s/pull/1)（审查时提案提交 `c464ba4d5a0ca59e8e619cdcbb05f588bea67635`）。  
> 适用方法：私有 `skills` 仓库中的 `architecture-design-review` Skill；借鉴 KubeBlocks 的**分层资源抽象**，结合 DDD 的限界上下文、六边形架构的适配器/端口及显式操作状态机。Skill 源码**不复制到本公共仓库**。

## 1. 结论和适用边界

**建议保留统一的资源目录、身份、操作记录和审计入口，但不接受将 Kubernetes 集群、KubeVirt VM、PVC/存储、etcd 恢复和 CI 产物一律映射到通用 `create/update/delete/restart` 生命周期。**共享的是接口框架、操作信封及可观测结构；真实不变量、能力集、权限和故障恢复由对应领域定义。

本仓库既包含 Ansible 二进制部署与运维自动化，也已有 CPP V2.0 的**冻结领域模型、API/Workflow 规格和部分持久化 Runtime 代码**。已有规格接受“Everything Is A Resource”的公共 metadata/spec/status 信封；这不等于冻结了所有资源共享一种生命周期。现有 SQLAlchemy 持久化与 RuntimeService 是实现基础，但异步 WorkflowOrchestrator 和遗留执行路径迁移仍有明确缺口。因此，下述新聚合和操作端口建议须与冻结规格对齐，涉及不兼容变更应走新版本/设计评审，不能把候选设计当成现行能力。

同时，**构建/验证和发布应是不同权限域**。当前 `master` 的构建和缓存工作流仍含仓库写入权限、发布凭据及回写分支流程；A09 PR 提出了隔离方案，但它尚未合并，所需环境保护也尚未在本次试点中验收。

## 2. 证据登记表

以下“证据状态”表示仓库中可观察事实的成熟度，不代表某项能力已通过真实环境验收。

| ID | 状态 | 可核验事实或待核实事项 | 证据 / 判读 |
| --- | --- | --- | --- |
| E01 | CURRENT | 主路径为 Ansible 部署，区分 HA 机器、单节点机器、容器演示模式；容器模式不是生产 HA。 | [README 部署模式及推荐流程](../README.md)；单节点不具备 etcd quorum 容错。 |
| E02 | CURRENT | `Makefile` 已区分 KubeVirt、节点池、存储、恢复、迁移等命令；若干破坏性操作设有显式确认变量。 | [Makefile](../Makefile)；对操作存在不等价语义的直接证据。 |
| E03 | CURRENT | `master` 上 `build-default-binaries.yml` 与 `cache-default-binaries.yml` 均声明 `contents: write`、向 job 暴露 `BINARY_CACHE_TOKEN`、默认 `commit_changes=true` 并具有缓存分支回写路径。 | [构建工作流](../.github/workflows/build-default-binaries.yml)、[缓存工作流](../.github/workflows/cache-default-binaries.yml)；这是配置权限暴露面，**不等同于已观察到未授权发布事件**。 |
| E04 | PROPOSED | A09 PR 设计只读 Build/Cache 验证与单独的受保护 Publish；发布需 `PUBLISH` 确认、环境审核、独立凭据。 | [PR #1](https://github.com/tommyxie2026-tech/k8s/pull/1) 及[方案运行手册](https://github.com/tommyxie2026-tech/k8s/blob/fix/a09-build-publish-isolation/docs/A09-BUILD-PUBLISH.md)；**未作为现行能力入账**。 |
| E05 | CURRENT | 存在按阶段推进的生产化待办；文档中的“已完成/待完成”表述须与源文件、运行结果分别核验。 | [ROADMAP](ROADMAP.md)；文档陈述不等于环境实际通过。 |
| E06 | CLAIM / UNKNOWN | 此前用户确认“已部署或测试，尚未完成验收”；本次未访问目标集群、权限设置、运行日志或物理故障演练证据。 | 需由环境/交付负责人提供验收证据；不从 `README` 或 CI 状态推导生产就绪。 |
| E07 | UNKNOWN | A09 的 GitHub Environment 必需审核人、密钥存放边界、缓存分支保护、LFS 实际发布及离线全链路交付是否已按预期配置/执行。 | PR 文档明确要求仓库管理员配置；须通过管理员读数与独立验收确认。 |
| E08 | CURRENT（设计基线） | CPP V2.0 冻结了通用 Resource 信封、Cluster/Node/StoragePool/StorageClass/VM/Backup/Workflow/Task 等类型以及独立限界上下文。 | [FROZEN-P1 领域模型](frozen/FROZEN-P1-01-DOMAIN-MODEL-v1.0.md)；仅证明设计冻结，不证明全部类型完整落地。 |
| E09 | CURRENT（设计基线） | 冻结 API 要求操作 API 经 Workflow，禁止 API 直接执行命令，要求破坏性确认与乐观并发；Workflow 规格拆分编排与 Task 执行。 | [FROZEN-P3 API](frozen/FROZEN-P3-API-SPECIFICATION-v1.0.md)、[FROZEN-P4 Workflow](frozen/FROZEN-P4-WORKFLOW-ENGINE-v1.0.md)。 |
| E10 | CURRENT（代码及核验文档） | `platform-api` 已有持久化 Task/RuntimeService；部分 VM 路由仍直接使用 legacy executor，异步 WorkflowOrchestrator 尚未实现完整收敛。 | [RuntimeService](../platform-api/app/runtime/service.py)、[VM router](../platform-api/app/routers/vm.py)、[实现状态基线](implementation/VERIFIED-IMPLEMENTATION-STATUS-v1.0.md)。 |
| E11 | CURRENT（设计约束） | 备份恢复架构明确 VM 规格与磁盘数据须共同恢复，且要求先做恢复演练。 | [备份恢复架构](BACKUP-RECOVERY-ARCHITECTURE.md)；操作成功率及 RTO/RPO 仍需实测。 |

## 3. 限界上下文与权威状态归属

| 限界上下文（候选） | 负责的语义 / 不变量 | 权威证据 / 现状 | 不应承担的职责 |
| --- | --- | --- | --- |
| 版本与源码清单 | 上游组件版本、源码标签、平台兼容约束 | `repo/sources.yml`、`inventories/group_vars/all.yml` 及版本校验脚本；需验证二者一致性 | 不批准发布，不表示部署成功 |
| 构建验证 | 源码构建、包完整性、校验和、临时构建证据 | Actions run、测试结果、构建产物摘要 | 不拥有长期缓存分支写权限 |
| 产物发布 | 审批后将已核验产物写入明确的 `binary-cache/<arch>` | 目标分支和 LFS 远端；A09 的隔离机制尚是提案 | 不应重新解释构建通过，也不应跳过人工审批 |
| 部署自动化 | Inventory、Ansible playbook、操作前置条件、执行记录 | Git 中的配置/代码 + 操作现场日志；实际运行状态不在 Git 中 | 不应把静态部署意图当成实时集群状态 |
| Kubernetes 运行时 | 节点、工作负载、Control Plane/etcd 的实际状态 | Kubernetes API、etcd 状态及宿主观测（本次未读取） | 不批准 GitHub 缓存发布 |
| KubeVirt / 存储 / 备份 | VM、DataVolume、PVC、快照、恢复依赖和数据完整性 | KubeVirt/Kubernetes 对象和备份系统状态（本次未读取） | 不从一条通用重试规则推断可恢复性 |
| 安全与变更治理 | 责任人、审批、授权时效、破坏性操作确认、验收 | GitHub 环境保护、变更审批和操作审计；负责人待确认 | 不以“workflow green”替代生产验收 |

**与现有冻结规格的关系**：`FROZEN-P1-01` 认可 Resource 共同字段；`FROZEN-P3` 已限定 Action API 经 Workflow；`FROZEN-P4` 把 Workflow 编排、Task 执行及 Executor 命令分开。建议的操作信封是对现有契约的审查视角，不是要求另造 `Operation` 表。当前 `platform-api/app/runtime/service.py` 已实现持久化 submit/execute 分离，而 `platform-api/app/routers/vm.py` 仍有直接 legacy executor 路径；因此应优先验证并收敛**现有** Workflow→Runtime 边界，再评估新增适配层。冻结规格变更应独立版本化与审批。

边界原则：**期望状态、观测状态和执行事实分开保存**。例如部署 Playbook 退出码为零只是一次执行结果，不自动证明节点 Ready、etcd quorum 正常或 VM 数据可恢复。若未来引入统一 API，可用 `ResourceRef(kind, name, namespace, owner)` + `Operation(id, actor, target, command, status, evidence)` 作为跨上下文信封，但实际命令由类型化适配器验证。

## 4. 资源模型和关键不变量

| 资源 / 聚合候选 | 类型化操作 | 必须保持的不变量 |
| --- | --- | --- |
| ClusterDeployment | preflight、deploy、upgrade、migrate、stop | HA/单节点模式不可混淆；变更前核实节点和 etcd quorum；迁移受显式确认及分阶段验证约束。 |
| KubeVirtVM | inspect、start、stop、restart、migrate、backup/restore | VM 操作需绑定 namespace/name 和依赖卷；创建/重启不等同于数据一致恢复。 |
| StorageVolume / Snapshot | attach、snapshot、restore、validate | 先验证存储类、快照能力、权限和恢复点；失败恢复不能以“重复执行即可”假设替代。 |
| EtcdRecovery | snapshot、preflight、restore | 恢复目标、快照可用性、现有集群状态及故障域需独立确认；不可静默自动恢复。 |
| BuildVerification | build、check、attest（候选） | 来源/版本、平台架构、摘要、验证结果与 run 身份可追踪；失败不能标记可发布。 |
| ArtifactPublication | request、approve、publish、verify | 审批主体与构建执行主体分离；只发布验收过的精确产物；失败保留既有已发布版本。 |

这些是**架构建议**而不是宣称已实现的 CRD 或持久化聚合。尤其 Kubernetes 原生对象（如 VM、PVC）已由各自控制器管理，统一平台不应再制造第二个互相竞争的真实状态源。

## 5. 统一操作契约与失败模式

未来如果统一平台入口，推荐每次操作最少表达：`operation_id`、`resource_kind/ref`、`requested_action`、`actor/approval`、`preconditions`、`idempotency_key`、`desired_revision`、`execution_state`、`observed_proof`、`timeout/retry_budget`、`compensation_or_manual_gate`、`audit_ref`。该契约是建议，不要求本试点写代码。

| 操作 | 执行者 / 前置条件 | 成功证据 | 失败处理边界 |
| --- | --- | --- | --- |
| Build/Verify | CI；固定来源版本、读权限、确定的平台架构 | 检查、包完整性、digest、Actions artifact | 失败即停止，不发布；可在独立运行中重试，但不得复用未验证结果 |
| Publish | 获授权发布主体；环境 reviewer、审批、已验证摘要 | 受保护缓存分支、LFS 对象、摘要匹配 | 失败保留上一有效缓存；不退化为宽权限直接 push |
| Deploy/Upgrade | 环境交付责任人；preflight、备份/回滚方案、目标 inventory | 节点/API/网络/etcd 现场验收 | 部分成功需人工判断；停止自动级联修改 |
| VM operation | 虚拟化操作主体；对象和存储依赖检查 | KubeVirt 条件、卷状态、工作负载可用性 | timeout 后先查询实际状态，禁止盲目重复创建/恢复 |
| Snapshot/Restore | 数据/存储责任人；恢复点、目标、数据风险批准 | 完整性与应用一致性验收 | 对不可逆/模糊结果 fail-closed，人工授权后继续 |

风险分级：只读查询可自动重试；幂等且可验证的瞬态失败可有限重试；可能已经产生副作用的超时须先对账；破坏性迁移、证书轮换、etcd/VM 恢复须显式确认。KubeBlocks 式统一抽象不意味着所有服务共用一套默认恢复策略。

## 6. 决策与责任登记（待用户/维护者审查）

| ID | 分类 | 建议决策 | 暂行责任角色 / 最终批准 | 验收与回退 |
| --- | --- | --- | --- | --- |
| R01 | KEEP | 保留 Ansible 机器 HA、单机与容器测试模式的职责分界 | 部署架构维护者；最终用户/项目 owner | 文档、inventory 与实测矩阵相符；若不能，先修正声明 |
| R02 | KEEP | 统一入口只抽象身份、审计、异步操作结果，不强行统一业务生命周期 | 平台架构负责人（待指派）；最终项目 owner | 对 cluster/VM/存储/恢复的无效操作可拒绝 |
| R03 | CHANGE-CANDIDATE | 推进 A09 的只读构建/受保护发布权限隔离，**以 PR #1 单独审批为准** | CI 维护者 + GitHub 仓库管理员；最终项目 owner | 代码审查、环境必需审核、分支保护、密钥隔离、试发布与回滚；未批准前不发布 |
| R04 | KEEP | 保留迁移、reset、证书轮换、etcd 与 VM 恢复的明确确认门禁 | 集群 SRE/数据责任人（待指派）；最终环境 owner | 对默认参数执行保护性 dry-run/静态测试；不得绕过审批 |
| R05 | REMOVE-CANDIDATE | 不引入“一种 Resource 支持所有 create/update/delete/restart”的通用领域模型 | 平台架构负责人（待指派）；最终项目 owner | 设计评审记录非法操作与类型适配策略；此项非删除已有代码 |
| R06 | DEFER | 不把自动重试/补偿推广到所有状态变更；先做操作幂等与失败分类 | 运行时/运维负责人（待指派）；最终项目 owner | 有限重试、歧义副作用、手工接管与恢复点的用例过审 |
| R07 | DEFER | 不宣布生产 HA、完整离线安装及二进制交付已验收 | 测试/交付负责人（待指派）；最终项目 owner | 环境部署、故障演练、离线镜像/系统依赖、LFS 与保护策略均提供证据 |
| R08 | CHANGE-CANDIDATE | 先完成遗留 VM/Workflow 路由经持久化 Runtime 的边界收敛；禁止新的 Router→Executor 直连，不在本试点实施 | API/Runtime 维护者（待指派）；最终架构 owner | 兼容性契约、Task 状态恢复、取消与重复请求测试通过后才能迁移，避免提前删除旧入口 |
| R09 | KEEP | 尊重已冻结的 Resource、API、Workflow 契约，若新模型不兼容，先提出版本化设计变更 | 架构委员会/项目 owner（实际流程待确认） | 设计差异清单、版本号、评审记录、兼容策略齐备 |

表内责任人均是**建议角色**，不是已核实的人事分工。需项目 owner 确认实际责任人及决策权限后才可进入实施。

## 7. 验证门禁与限制

**本轮已执行**：只读核对 `README.md`、`docs/ROADMAP.md`、`Makefile`、`master` 两个二进制工作流、CPP 冻结模型/API/Workflow 规格、部分 Runtime/路由代码及 A09 PR 提案运行手册；完成现行/提案分离、限界上下文和操作失败边界审查。

**本轮未执行**：修改部署/控制器/工作流代码、触发任何 CI、运行 Ansible、访问 live cluster、配置 GitHub Environment、测试 LFS 发布、合并 A09 或其他 PR。因此报告不是部署、安全或 HA 验收证明。

如后续获明确授权，建议验证顺序：

1. 静态测试：冻结规格与 API/Runtime 实现差异、资源种类与不支持的命令、前置条件/审批、`resource_version` 冲突、版本/摘要一致性、权限最小化；不在已有冻结契约外任意新造 Resource。
2. PR #1 独立审核：只读 CI 权限、生产 Secret 作用域、受保护环境 required reviewers 与分支规则；代码变更**不等于**设置生效。
3. 小规模隔离试验：构建-验证失败不能发布、产物摘要在验证和发布之间不被替换、发布失败不破坏旧缓存。
4. Runtime 收敛验证：API→Workflow→持久化 Task→Worker→Executor，在重启、孤儿任务、重复提交、并发更新、超时、取消下保持执行事实；在兼容性批准前不删除旧路由。
5. 环境验收：HA 故障域、etcd quorum、KubeVirt/存储恢复点以及完整 air-gap（镜像、依赖、网络配置）逐项记录。
6. 明确各项责任人和剩余风险；先基于现有冻结 API 与适配器边界判断差异，再单独决定是否需要扩展接口或资源适配层。

**试点判定**：Skill 适合用作设计评审与变更治理门禁；其价值是统一**审查问题与证据形式**，不是在此仓库立即实现统一控制器。未获批准的候选设计保留为候选，不自动成为开发任务。
