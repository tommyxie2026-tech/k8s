# CPP V2.0 — M3 Workflow / Runtime 收敛审查与实施门禁

> 日期：2026-10-30（Asia/Tokyo）
> 基线：`master`，审查时 HEAD `b55eff7170e0dcd964ab4a52805cde91603dcaca`
> 状态：**PROPOSED / 待项目 owner 审核的设计与验收清单，不是实施批准**
> 方法：私有 `architecture-design-review` Skill 的证据、限界上下文、操作语义和决策门禁四阶段审查
> 范围：`platform-api`、`docs/frozen/FROZEN-P1/P3/P4`、[上一轮架构试点](../architecture-design-review-pilot-2026-10-30.md)
> 非目标：重建 CPP Resource 模型；新增通用工作流产品；部署、发布、真实集群操作；变更冻结规格；未经批准删除兼容 API 或旧执行路径

## 1. 结论

**建议保留 FROZEN-P1 的 Resource/Workflow/Task 模型和 FROZEN-P3/P4 的 API、状态机与执行边界，采用兼容迁移而不是一轮大重构。** 当前最大的实现缺口不是缺少基础表或 Executor 抽象，而是**对外 API 仍通过旧执行通道绕开持久化 Workflow/Runtime**。建议分离“接受操作意图”与“执行基础设施命令”，先完成可靠的 durable Workflow→Task 关联、终态回写和失败隔离，再有序切换 API 入口。

一个领域的 `metadata/spec/status` 公共信封不能证明该领域支持任何其它领域的 `restart/delete/restore` 操作。动作必须经过类型能力、角色/授权、前置条件及可验证的独立生命周期约束。

### 两种路线的取舍

| 方案 | 优点 | 风险 | 建议 |
| --- | --- | --- | --- |
| A. 一次性替换所有 API/同步 Workflow/旧 Executor | 单次迁移看起来简单 | 无兼容回退窗口；旧 API 响应改变；破坏性操作和孤儿任务会引入隐性副作用 | **不采用** |
| B. 按冻结契约推进持久化 Workflow，逐个适配入口并保留可撤回路径 | 可验证中间状态；失败可隔离；不破坏冻结 API | 迁移期间有两套内部路径，必须明确单一权威入口并防止双重执行 | **推荐，待批准** |

## 2. 证据登记（相对于上述 master 基线）

| ID | 分类 | 事实或缺口 | 仓库证据 | 需要补证 |
| --- | --- | --- | --- | --- |
| E01 | CURRENT（冻结设计） | Workflow 是聚合/资源；API 创建 Workflow、Workflow 创建 Task、Runtime 调用 Executor；复杂/破坏性动作不能直接调用 Executor | [FROZEN-P1](../frozen/FROZEN-P1-01-DOMAIN-MODEL-v1.0.md)、[FROZEN-P3](../frozen/FROZEN-P3-API-SPECIFICATION-v1.0.md)、[FROZEN-P4](../frozen/FROZEN-P4-WORKFLOW-ENGINE-v1.0.md) | 冻结契约与实现的自动追踪检查 |
| E02 | CURRENT（代码） | `POST /api/v1/workflows` 调用 `workflow_engine.create()`，`create()` 内同步调用 `run()`，后者直接调用旧 `Executor.run_playbook()` | [routers/workflows.py](../../platform-api/app/routers/workflows.py)、[services/workflow.py](../../platform-api/app/services/workflow.py)、[services/executor.py](../../platform-api/app/services/executor.py) | 请求超时、失败与取消的兼容测试 |
| E03 | CURRENT（代码） | 旧 Workflow 用 `WorkflowStore` 的单个 JSON 文件保存记录，`WorkflowEngine.create()` 在进程内逐步运行；它没有经持久化 WorkflowStep/Runtime 调度 | [services/workflow_store.py](../../platform-api/app/services/workflow_store.py)、[services/workflow.py](../../platform-api/app/services/workflow.py) | 并发写入、崩溃恢复与原子性测试 |
| E04 | CURRENT（代码） | `RuntimeService.submit()` 能创建持久化 queued Task；`LocalTaskWorker.run_once()` 能 claim 并记录成功/失败 | [runtime/service.py](../../platform-api/app/runtime/service.py)、[runtime/worker.py](../../platform-api/app/runtime/worker.py)、[db/repositories.py](../../platform-api/app/db/repositories.py) | 真实工作进程/数据库重启情况下的恢复试验 |
| E05 | CURRENT（代码） | `main.py` 挂载的是 `routers/kubevirt.py`（非 `routers/vm.py`）；已挂载的 KubeVirt、Backup、Governance、Cluster 路由仍调用 `app.core.executor.executor.submit()` | [main.py](../../platform-api/app/main.py)、[kubevirt.py](../../platform-api/app/routers/kubevirt.py)、[backup.py](../../platform-api/app/routers/backup.py)、[governance.py](../../platform-api/app/routers/governance.py)、[clusters.py](../../platform-api/app/routers/clusters.py) | 所有对外路由与执行入口的自动库存 |
| E06 | CURRENT（代码） | `RuntimeService.execute()` 先将 Task 置为 running 再获取 Registry Executor；`registry.get()` 发生异常时位于其 `try` 外，存在留下 running 状态的**推断风险**；`LocalTaskWorker.run_once()` 的异常处理更完整 | [runtime/service.py](../../platform-api/app/runtime/service.py)、[runtime/worker.py](../../platform-api/app/runtime/worker.py) | 先写“未知 Executor”回归测试，确认实际缺口与预期策略 |
| E07 | CURRENT（代码） | `recover_orphaned()` 对心跳过期的 running Task 重新排队；代码并未在这一方法内核实外部命令是否已产生副作用 | [db/repositories.py](../../platform-api/app/db/repositories.py)、[runtime/worker.py](../../platform-api/app/runtime/worker.py) | 确认副作用歧义情况下的恢复/人工接管协议，勿默认重放破坏性操作 |
| E08 | CURRENT（代码） | Workflow/Step/Task 表、状态转换、step 依赖/重试计划和日志基础已有实现；API 路由尚未把它们编成闭环 | [db/models.py](../../platform-api/app/db/models.py)、[db/workflow_steps.py](../../platform-api/app/db/workflow_steps.py)、[services/workflow_state.py](../../platform-api/app/services/workflow_state.py) | 完整 Workflow→Task→Step 终态回写整合测试 |
| E09 | CURRENT（测试范围） | `test_runtime_service.py` 覆盖 submit、正常终态、Executor 抛错及终态不可取消；不能据此声称完整异步工作流、鉴权、分布式/孤儿恢复已验收 | [test_runtime_service.py](../../platform-api/tests/test_runtime_service.py) | 针对竞争条件和进程崩溃的新增验证 |
| E10 | CURRENT（代码/接口差异） | 冻结的 `POST /api/v1/workflows/{id}/cancel` 与 `/retry`、`GET /api/v1/tasks` 等接口在已检查的 `routers/workflows.py` 和 `routers/jobs.py` 中未完整体现；`jobs.py` 仍读内存 TaskStore | [FROZEN-P3](../frozen/FROZEN-P3-API-SPECIFICATION-v1.0.md)、[workflows.py](../../platform-api/app/routers/workflows.py)、[jobs.py](../../platform-api/app/routers/jobs.py) | API 路由列表和 schema contract tests |
| E11 | CURRENT（合并事实） | A09 PR #1 已合并；主分支构建/缓存验证工作流使用只读权限；PR #3 修复过 Ansible YAML；架构试点 PR #2 已合并 | [PR #1](https://github.com/tommyxie2026-tech/k8s/pull/1)、[PR #3](https://github.com/tommyxie2026-tech/k8s/pull/3)、[PR #2](https://github.com/tommyxie2026-tech/k8s/pull/2) | GitHub Environment/reviewer/LFS/离线全链路验收仍 UNKNOWN |
| E12 | UNKNOWN | 实际集群是否满足生产 HA、RBAC、可恢复 RTO/RPO、脱网部署和发布权限验收，本次未访问运行环境 | 需要环境 owner 提供现场审计证据 | 不得依据静态测试断言生产就绪 |

注：`CURRENT` 只代表在基线代码/文档中能直接观察到，**不表示功能已通过真实环境验收**。E06/E07 的风险是从实现推导的、待测试验证的问题，不应伪称已发生事故。

## 3. 限界上下文与状态权威

| 上下文 | 唯一职责/权威状态 | 不得越界 |
| --- | --- | --- |
| API + Authorization | 请求结构、身份与授权、确认凭证、幂等键、资源版本约束；输出 Workflow ID | 不直接启动 Playbook/外部命令，不假定 UI 确认能代替服务端校验 |
| Workflow Orchestrator | 持久化 Workflow/Step，检查依赖，计算 step/Workflow 终态，产生审计决策 | 不直接调用 ansible/kubectl；不创建第二个任务真相表 |
| Runtime / Task Repository | 持久化 Task、claim/租约、执行状态、日志/回执、有限恢复 | 不解释业务上的 VM/存储/etcd 是否可安全重放 |
| Worker / Executor Adapter | 仅执行已经过校验、具有稳定 Task ID 的具体命令并报告返回 | 不直接决定 Workflow 成功或业务回滚；不可自行重试有歧义副作用的操作 |
| Kubernetes/KubeVirt/Storage | 各领域的资源实际观测状态及不可逆副作用 | 不能被 GitHub CI、Workflow 文件状态取代 |
| CI/Publication | 建造、验证、审批及发布产物的独立权限域 | CI 绿色不能等同于部署、真实数据可恢复或发布审批已生效 |

权威关系：`WorkflowRepository/WorkflowStepRepository` 管编排状态；`TaskRepository` 管持久化执行状态；Kubernetes/KubeVirt/存储 API 管实际资源状态。`WorkflowStore`、`_JOBS`、旧 `task_store` 只能在有限兼容窗口作为历史视图或显式迁移对象，不能与新库同时可写并宣称双权威。

## 4. 统一操作契约及危险状态

建议在现有冻结 API 和 Repository 边界内，检验每次操作记录至少具备：`operation/workflow_id`、`actor`、`target_ref`、`definition_version`、`confirmation/authorization`、`idempotency_key`、`resource_version`、`desired_action`、`task_id`、`execution_state`、`observed_evidence`、`retry_budget`、`audit_ref`。**这是审查字段候选，不代表当前表结构都有这些列，也不是授权新增通用 Operation 表**。

| 场景 | 风险 | 安全默认和验收条件 |
| --- | --- | --- |
| POST 后连接中断、客户端重试 | 同一操作重复提交/重复运行 | 稳定请求/Workflow ID 与幂等键；对账后返回既有记录 |
| Worker 已启动外部命令但心跳超时 | 重新入队可能重复产生副作用 | 对可疑 running 操作 `UNKNOWN / needs-reconciliation`（设计候选）；先查询真实状态或人工审查；不盲目重放 |
| Registry 查不到 Executor / 构造执行命令失败 | Task 可能留在 running | 失败可持久化并可追踪；单元测试需覆盖执行器选择与构造异常 |
| Task 执行成功但 DB 写终态失败 | 用户可能重试已经成功的外部动作 | 按 Task ID、命令回执和外部可观察结果对账，禁止直接重复破坏性操作 |
| VM restore / etcd 恢复 | 无法简单回滚 | 显式审查确认、目标/恢复点检查、备份与现场验收；失败进入人工接管 |
| Workflow 失败/取消 | 执行中进程未必能被立即终止 | best-effort 取消 + 明确异步回执，不把“取消已请求”当作“外部动作已停止” |

## 5. R01–R09 决策复核

以下保持原[架构试点](../architecture-design-review-pilot-2026-10-30.md)编号，仅转化为下一阶段可审批清单。**责任角色是候选，不代表已经确认任何具体人员。**

| ID | 候选决定 | 复核建议和事实变化 | 建议负责角色 / 最终批准 |
| --- | --- | --- | --- |
| R01 | KEEP | 保留 HA/单节点/容器试验三种部署模式边界；生产状态仍需现场证据 | 部署维护者（unassigned）/环境 owner |
| R02 | KEEP | 统一资源信封/身份/操作审计，不统一不同资源的生命周期 | 领域架构负责人（unassigned）/项目 owner |
| R03 | CHANGE → 部分 CURRENT + UNKNOWN | **A09 代码已合并**；只读验证与受保护发布的配置/审批/试发布尚需独立验收，不能再标为未合并设计 | CI 维护者、GitHub 管理员（unassigned）/项目 owner |
| R04 | KEEP，但需验证 | 破坏性确认语义已冻结；目前已挂载的恢复类 Action API 仍直连旧 Executor，迁移门禁优先级高 | SRE/数据责任人（unassigned）/环境 owner |
| R05 | REMOVE-CANDIDATE（设计） | 不引入所有 Resource 共享 `restart/delete` 的通用领域生命周期；不删除既有 `metadata/spec/status` | 领域架构负责人（unassigned）/项目 owner |
| R06 | DEFER 自动补偿 | 先做幂等、副作用歧义、租约与恢复策略分类，不允许“故障自动重试一切” | Runtime 负责人（unassigned）/项目 owner |
| R07 | DEFER 生产就绪声明 | HA/air-gap、证书/备份/恢复、LFS 发布及权限均需证据 | 交付和验收负责人（unassigned）/环境 owner |
| R08 | CHANGE-CANDIDATE（最高优先级） | 收敛旧同步 Workflow 与已挂载 Router 的直连执行路径到持久化 M3；先补测试再切换 | API + Runtime 维护者（unassigned）/架构 owner |
| R09 | KEEP | FROZEN-P1/P3/P4 作为兼容基线；破坏性变更必须提新版本设计 | 架构 owner（unassigned）/项目 owner |

**审批含义**：建议先让 owner 确认 R01–R09 分类以及 R08 的实施顺序；确认人事责任和真实环境信息后，方可对代码分阶段授权。未获批准时均为 `PROPOSED`。

## 6. M3 最小改造切片（建议拆成独立 PR）

| 切片 | 内容与对应任务 | 安全边界 | 验收标准（非生产部署） |
| --- | --- | --- | --- |
| **M3-0** 契约/回归门禁 | 冻结 API 与现有路由矩阵；给 Registry 异常、并发重复、无授权确认、超时/副作用歧义写可复现测试；记录 `main.py` 实际挂载的 Router | 不改生产调用路径，不触发真实 Playbook | 自动测试能明确指出旧/新执行路径；失败安全测试有独立结论 |
| **M3-1** Workflow 定义和持久化（WF-001～003） | 版本化内置 WorkflowDefinition；按单一 DB 事务创建 Workflow 与有序 Step；请求端只返回 pending/queued，不同步执行 | 延续既有 workflow name/target/confirmation；拒绝不支持参数/操作 | 原子提交、错误回滚、重复请求不产生多个有效执行、重启后可查询 |
| **M3-2** 调度和回写（WF-004～006） | 只对依赖满足的 Step 提交持久化 Task；保存 Step→Task 映射；由 Task 终态回写 Step，再聚合 Workflow 状态 | 再次调度不能双重提交同一 Step；Worker 不直接改 Workflow 状态 | 持久化成功/失败、依赖阻断、重启重放、Task/Workflow 审计完整性测试 |
| **M3-3** 失败与取消策略 | 有界重试、持久化 backoff、幂等/副作用分类、取消确认和人工接管 | 禁止对 VM restore、etcd restore 等有歧义外部副作用的命令直接自动重试 | 断连/心跳超时/取消竞争/重复请求/补偿失败的负向测试通过 |
| **M3-4** 兼容 API 切换（WF-007～008） | `/api/v1/workflows` 迁移为异步 Orchestrator；补齐冻结 cancel/retry/task 查询契约；逐步适配已挂载 Action API | 不改 URL/确认语义/对象身份；绝不能双通道同时实际执行同一操作；保留可撤回开关或等效回退路径 | API 响应契约、鉴权、未授权拒绝、全量相关路由、read-only 与 destructive 负向集成测试 |
| **M3-5** 环境验收（后续独立授权） | A09 GitHub Environment/reviewer、存储/VM 恢复、HA/离线、日志审计等现场验证 | 属于真实环境审批，不通过文档 PR 执行 | SRE/环境 owner 提交时间戳、现场证据、回退记录和验收签字 |

**M3-1 的原子性**：当前 `RuntimeService.submit()` 自行 `commit()`，将来由 Orchestrator 创建 Workflow+Step+Task 时，应明确事务边界和 outbox/调度回收点，避免“Workflow 已保存但 Task 丢失”及“已执行但 Workflow 未记录”的状态。不要求本试点先设计新的分布式事务框架。

**兼容期原则**：旧执行入口可以保留为受控回退，不允许与新入口并行消费同一个实际操作；新 API 生效前必须先确认相应路由在 `main.py` 注册，并完整覆盖备份/恢复的服务端确认逻辑。

## 7. 建议验收矩阵

| 用例 | 必须观察到的结果 | 主责（待分配） |
| --- | --- | --- |
| 仅创建 Workflow | API 返回可追踪 ID/queued；请求内没有执行 Ansible | API 维护者 |
| 重复提交相同 idempotency key | 同一业务操作不发生重复外部执行 | Workflow 维护者 |
| 重启发生于 Workflow/Step/Task 各阶段 | 可以查询并对账；不会无条件双重执行 | Runtime 维护者 |
| 并发 Worker claim 与 heartbeat | 同一 Task 的执行权/超时恢复不冲突 | Runtime 维护者 |
| Executor 不可用、启动失败、返回码失败 | 失败记录持久化，Workflow 根据策略失败或可安全重试 | Runtime 维护者 |
| 运行中取消与确认竞态 | 取消请求可审计，不虚报进程已停止 | Runtime + SRE |
| 未确认的 VM/存储/etcd 破坏性动作 | 服务端拒绝，且执行器零调用 | API + 安全责任人 |
| Task 成功后写库失败或 worker 断连 | 外部状态对账，无法证明安全时人工接管 | Runtime + 环境 owner |
| 上游 API/旧客户端兼容 | 路径、必需字段、响应和错误码经契约测试 | API 维护者 |
| 真实集群 / CI 发布 | 独立环境证据，不用静态 CI 绿色代替 | 环境 owner / GitHub 管理员 |

必须覆盖：`pytest`、`ruff`/`mypy`（项目若已配置则按仓库既有命令）、SQLite 持久化测试、相关集成测试以及现有 GitHub CI；不引入会在 PR 阶段操作真实集群或发布产物的默认检查。

## 8. 已确认、未确认与合并门禁

**已确认（CURRENT）：** FROZEN-P1/P3/P4、老的同步 Workflow/旧 Router 直连、持久化 Runtime/Worker、WorkflowStep/Retry 辅助对象、A09 代码合并与 Ansible YAML 修复均可从仓库直接读取。

**待批准（PROPOSED）：** M3-0～M3-4 的分步 PR，最终 API 兼容策略、幂等键的持久化位置、恢复安全策略、各 R 编号的责任人与验收标准。

**未验证（UNKNOWN）：** 真正的多 Worker 并发、取消/超时后进程存活、外部副作用对账、审计全链路、生产 HA/air-gap、受保护 Publish Environment 的完整运行配置和现场恢复演练。

**建议门禁：** 先由项目 owner 批准 R01–R09 的责任与处置、R08 的分步顺序及初始 M3-0 只测试范围；再提交单独、可回退的测试 PR。之后每个有实际副作用的代码切片均需针对冻结契约单独审查和明确批准。此文档的合并不意味着授权执行 M3 代码迁移或环境部署。
