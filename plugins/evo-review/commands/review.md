---
name: review
description: 跨模块业务流审查：追踪端到端业务流，在模块交界处找真实 bug。红绿验证对抗幻觉 + 门禁自动进化。
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, Agent
argument-hint: "[dir/ or *]"
---

# /review — 跨模块业务流审查

核心产出是**用户真正会碰到的问题**。优先查跨模块交界处的契约断裂，同时沿业务流路径扫描单模块内的可感知 bug。

业务流追踪指南：[flow-tracing.md](${CLAUDE_PLUGIN_ROOT}/skills/review/references/flow-tracing.md)

## 输入

$ARGUMENTS — 可选：
- `/review` — 近 5 次 commit 涉及的业务流
- `/review dir/` — 指定目录相关的业务流
- `/review *` — 全业务流扫描

## 前置（每次执行）

1. 如果没有 `test-governance/` → 读取 [bootstrap.md](${CLAUDE_PLUGIN_ROOT}/skills/review/references/bootstrap.md) 并执行 bootstrap
2. `bash scripts/test-governance-gate.sh preflight 2>&1 | tail -20`
3. `bash scripts/test-governance-gate.sh trend 2>&1 | tail -30`
4. 确定扫描范围：无参数用 `git diff --name-only HEAD~5`，`*` 扫全模块

## 阶段 1：业务流追踪

### 1a. 推导受影响业务流（主会话，不开 agent）

从 `test-governance/config.yaml` 的 `cross_module.business_flows` 读取已定义的业务流，结合近期变更筛选受影响的子集：
1. **已定义业务流**：读 `config.yaml` 的 `cross_module.business_flows`（bootstrap 时生成）
2. **近期变更**：`git diff --name-only HEAD~5`，确定哪些模块/交界被改动
3. **筛选**：改动涉及的模块 ∩ 业务流涉及的模块 → 受影响的业务流
4. **补充**：如果改动了 `cross_module.shared_types` 中的文件 → 所有消费该类型的业务流也加入
5. **`/review dir/` 模式**：找所有经过该目录所属模块的业务流

如果 `config.yaml` 无 `cross_module` 段（未 bootstrap 或单模块），先从 CLAUDE.md 通信拓扑 + `p0-cases.tsv` 推导。

输出：受影响的业务流清单（**3-6 条**），每条包含：
- 流名称（如"iOS 审批任务 → togo-agent 状态转换 → Bot 通知"）
- 涉及模块列表
- 入口文件和关键交界点

**单模块项目**：无跨模块交界，退化为代码模式扫描（A-E），按模块拆 agent。

### 1b. 按业务流拆 Explore agent 并行

每个 agent 负责 **1 条业务流**（跨读多个模块），prompt 必须包含上方已加载的 flow-tracing.md 的完整内容，加上：

**主要检查（模块交界处 F1-F4）**：
- F1 消息格式对齐：发送端字段 vs 接收端字段，有无遗漏/类型不匹配
- F2 状态机一致：前后端枚举值和允许转换是否一致
- F3 失败处理：一步失败时下游有无超时/重试/降级
- F4 时序假设：隐含的先后依赖是否可能被打破

**同步检查（A-E，沿业务流路径顺带扫描）**：
在追踪业务流经过的每个模块时，顺带检查该路径上的：
- A 资源泄漏：流经的代码中 timer/listener/fd 创建后是否清理
- B 标记锁未重置：流经的状态标记在异常路径是否重置
- C 错误吞没：流中的 catch 块是否正确传播错误
- D 并发安全：流涉及的共享状态是否有保护
- E 安全边界：流的入口是否校验了输入

A-E 发现的**过滤条件**：必须能描述出用户可感知的影响（如"连续语音输入时界面卡顿""按钮永久 disabled"），纯理论风险不报。

**约束**：
- **每条业务流最多 6 个发现**（F1-F4 + A-E 合计），按用户影响严重度排序
- F1-F4 优先于 A-E（同等严重度下，交界问题排前面）
- 每个发现必须含：文件:行号、代码证据、**用户可感知的影响**（F1-F4 需标注交界两侧文件）
- 没有用户可感知影响的发现不要报
- 趋势热点文件优先分析

→ 主会话汇总去重，**按业务流组织**输出确认清单，等用户确认。

## 阶段 2：验证+修复（用户确认后）

按模块拆 worktree agent 并行（不同语言不混）。

每个 bug：
1. 读源码确认 → 写测试复现(红) → 写 fix(绿)
2. 测试直接通过 = 幻觉，撤销测试和修复，不要修改测试强行失败
3. 全部完成后统一跑 1 次 lint + 单元测试，确认无回归
4. commit 在 worktree 内，不合并不 push

**判定规则：**
- 红绿通过 + 无回归 → ✅
- 测试直接通过 → ❌ 幻觉，撤销
- fix 后测试仍失败 → 重写或丢弃
- 已有测试回归 → 修复回归或丢弃
- 环境限制无法测试 → ⚠️ 标注原因

**bug 验证策略：**
- 行为错误类 → 标准红绿
- 缺失机制类 → 写预期行为测试 → 红（不存在）→ 实现 → 绿
- 编译级 bug → 编译失败→通过作为红绿
- 跨模块契约断裂 → 在消费端写测试，用真实的发送端数据格式验证解析是否正确 → 红（格式不匹配）→ 修一侧 → 绿

**worktree 硬约束（见 [efficiency.md](${CLAUDE_PLUGIN_ROOT}/skills/review/references/efficiency.md)）：**
- tool uses ≤ 50，超过立即停止汇报
- **禁止在 worktree 内跑 preflight / gate.sh**
- 修复项 ≤ 5/agent，超出拆第二个
- 同一业务流涉及多语言时，按语言拆 agent 但共享该流的上下文（发现列表 + 交界说明）

→ 主会话输出验证报告，等用户确认合并。
→ 用户确认后：合并 worktree + push + 清理 worktree → 阶段 3。

## 阶段 3：基础设施更新（主会话直接做，不开 subagent）

见 [phase-b.md](${CLAUDE_PLUGIN_ROOT}/skills/review/references/phase-b.md)

## 报告模板

```
## Review 报告

### 业务流检查
| 业务流 | 涉及模块 | 发现数 | 关键问题 |

### 测试体系强化
| 模块 | 新增基础设施 | 能自动抓住的问题类型 |

### 附带修复的 bug
| # | 标记 | 业务流 | 交界点 | bug | 修复 |

### 验证统计
| 发现数 | ✅ 已验证 | ❌ 幻觉 | ⚠️ 未验证 |

### 幻觉记录
| # | 声称的 bug | 实际情况 |
```
