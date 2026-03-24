---
description: 全模块深度审查：5 轮分析→筛选→红绿验证+修复→交叉检验→基础设施强化，对抗幻觉
allowed-tools: Read, Glob, Grep, Bash(*), Write, Edit, Agent
---

# /deep — 全模块深度审查

`/review --deep` 的独立命令版本。全模块循环强化：5 轮分析→筛选→红绿验证+修复→基础设施。

review 的核心产出是**测试基础设施**，不是 bug 修复。
找到的 bug 只是信号，用来发现测试体系的盲区 → 补基础设施让同类 bug 以后被自动抓住。

参考文档（自动加载）：
- 语言适配与扫描特征：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/language-adapters.md
- 测试维度定义：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/dimensions.md
- 测试运行策略：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/testing-strategy.md
- gate 骨架模板：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/gate-template.sh

## 输入

$ARGUMENTS — 可选：
- `/deep` — 全模块深度审查
- `/deep macbook-agent/ voice-tunnel/` — 指定模块深度审查

## 前置

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/bootstrap.md

## 正式流程：5 轮循环

**前 2 轮是只读发现，第 3 轮筛选过滤幻觉，第 4 轮用红绿测试做机械验证+修复，第 5 轮做影响范围扩展。**

```
第 1 轮（R1）：标准五类模式扫描（A 资源泄漏 / B 标记锁 / C 错误吞没 / D 并发安全 / E 安全边界）
    ↓
第 2 轮（R2）：更深层——架构问题、错误传播链路、状态机非法转换、测试体系自身盲区
    ↓ 汇总去重
第 3 轮（R3 筛选轮，opus 只读，不写测试）：
    对 R1+R2 每个发现，opus agent 读源码快速确认"bug 是否真实存在"
    - 确认存在 → 保留进入 R4
    - 源码证明不存在（防护已有、签名不符、逻辑安全等）→ 标记幻觉，丢弃
    - 不确定 → 保留进入 R4（交给红绿测试判定）
    ↓
第 4 轮（R4 红绿验证+修复 — 强制，不可跳过）：
    按模块拆 opus worktree agent，对 R3 筛选后的每个发现执行：
    a) 先读源码确认 bug 是否存在
    b) 写测试精确复现 bug → 运行 → 必须失败（红）
    c) 写 fix → 运行测试 → 必须通过（绿）
    d) **所有发现处理完后**，统一运行 1 次该模块 lint + 已有测试 → 必须无回归（不要每个 bug 单独跑）
    e) ✅ 的保留修复，❌ 的撤销测试和修复

    判定规则（严格，无中间态）：
    - 红绿都通过 + 无回归 → ✅ 已验证，保留修复
    - 步骤 b 测试直接通过（"bug"不存在）→ ❌ 幻觉，撤销测试和修复
    - 步骤 b 失败但原因与声称 bug 不符 → ❌ 幻觉，撤销
    - 步骤 d fix 后测试仍失败 → fix 有误，重写 fix 或丢弃
    - 步骤 d 已有测试回归 → fix 引入新问题，必须修复回归或丢弃该发现
    - 环境限制无法运行测试 → ⚠️ 未验证，标注原因，保留修复但标记
    - **编译级 bug**（如缺少 @MainActor、类型签名错误等无法用运行时测试复现竞态的问题）→ 允许用"编译失败→编译通过"作为红绿判定，标记为 ⚠️ 未验证

    **bug 分类与验证策略：**
    - **行为错误类**（现有代码输出/状态不符预期）→ 标准红绿：写测试复现错误行为 → 红 → 修 fix → 绿
    - **缺失机制类**（某机制不存在，如缺缓存、缺取消句柄、缺清理逻辑）→ 行为回归测试：写测试描述修复后的预期行为（如"缓存命中时不读磁盘"）→ 红（API 不存在导致编译失败，或旧行为不符预期导致运行时失败，都算合法的"红"）→ 实现机制 → 绿
    - **编译级 bug**（类型/修饰符缺失）→ 编译失败→编译通过作为红绿判定

    全部完成后：在 worktree 内 commit（只包含 ✅ 和 ⚠️ 的修复，❌ 的全部撤销）
    ⚠️ 不合并到 main，不 push。worktree 分支保留，等用户确认后由主会话合并。
    ↓
第 5 轮（R5 交叉检验）：只针对 R4 ✅ 已验证的问题
    a) Explore agent 扫描：同类模式是否在其他模块存在？修复是否影响兼容性/部署顺序？
       **R5 agent 的 prompt 必须包含 R4 已修复 bug 列表，明确告知"以下 bug 已在 R4 修复，不要重复报告"**
    b) 扫描结果中的"其他模块同类 bug"必须走红绿验证+修复（按模块拆 opus worktree）
    c) R5 worktree agent 的 prompt 必须包含 R4 同类 bug 的测试文件路径和测试模式摘要，作为参照。同类 bug 的测试应保持模式一致（如 R4 用 mock 验证双重通知，R5 同类 bug 也用相同的 mock 模式）
    d) R5 worktree 同样只 commit 不合并，等用户确认
    e) 兼容性/部署顺序影响无法用测试验证的，标注为 🔗⚠️
    ↓
按盲区组织 → 一次性输出确认清单 → 等用户确认
    ↓
主会话合并已确认的 worktree 分支到 main + push + 清理 worktree
```

**确认清单标记：**

| 标记 | 含义 | 用户操作建议 |
|------|------|-------------|
| ✅ 已验证 | 红绿测试 + 无回归，三项全过 | 确认后执行 |
| ⚠️ 未验证 | 环境限制无法跑测试（须标注原因） | 用户自行判断 |
| 🔗✅ 已验证扩展 | 跨模块同类 bug，已通过红绿验证 | 和对应 ✅ 一起处理 |
| 🔗⚠️ 未验证扩展 | 兼容性/部署影响，无法用测试验证 | 用户自行判断 |

**幻觉发现（❌）不出现在确认清单中，但在报告末尾单独列出供参考。**

**规则：**
- R1-R2：每轮用独立 Explore agent（prompt 含前轮发现摘要，避免重复）
- R3 筛选轮：opus agent，只读不写，按模块并行，每个 agent 收到该模块的全部发现列表，逐条读源码确认
- R4：按模块拆 opus worktree agent，且不得复用发现该 bug 的 agent（降低确认偏差）
- R4 agent 的 prompt 必须包含："如果测试直接通过，说明 bug 不存在，标记为幻觉并丢弃。不要修改测试让它强行失败。"
- **R4 步骤 d 必须包含 lint 检查**（如 `npm run lint`），不能只跑测试。lint error 会破坏 CI。
- 新测试的维度覆盖登记到 `test-governance/dimension-coverage.yaml`
- 某轮新发现 = 0 → 提前终止（仅适用于 R1-R2）
- 多模块时每轮内各模块 agent 并行

用户确认后：
1. 合并已确认的 R4/R5 worktree 分支到 main + push
2. 丢弃未确认的 worktree 分支
3. 清理所有 worktree
4. 执行 Phase B 更新测试基础设施

### Phase B：更新测试基础设施（用户确认合并后执行）

**Phase B 直接在 main 上执行，不使用 worktree。** 改动内容是 gate 脚本和 test-governance 文档，不涉及业务代码，无需隔离。

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/phase-b.md

### 出报告前自检（强制，不可跳过）

在输出最终报告之前，逐项检查以下清单。任何未完成项必须补完后才能出报告：

- [ ] R4：所有 ✅ bug 已修复 + 回归测试已通过 + 已在 worktree commit
- [ ] R5：跨模块扩展已验证+修复 + 已在 worktree commit
- [ ] 用户确认后合并 worktree + push + 清理
- [ ] Phase B-1：新 bug 模式已转化为 gate 规则（preflight 通过）
- [ ] Phase B-2：新测试 helper 已创建且被至少一个测试使用
- [ ] Phase B-3：test-governance/ 已更新
- [ ] Phase B-4：trend 已重新执行，高频规则已检查覆盖情况
- [ ] Phase B-5：top 1 高频规则的存量违规已清理
- [ ] Phase B-6：已检查是否有跨模块约束需建议 gate 规则或写入 CLAUDE.md
- [ ] 所有改动已 commit + push

最终报告：
```
## Deep Review 报告

### 测试体系强化
| 模块 | 新增基础设施 | 能自动抓住的问题类型 | 验证结果 |

### 基础设施更新（Phase B）
| 类型 | 新增项 | 说明 |

### 附带修复的 bug
| # | 标记 | 模块 | bug | 修复 |

### 验证统计
| 发现数 | ✅ 已验证 | ❌ 幻觉 | ⚠️ 未验证 |

### 架构约束建议（如有）
| # | 约束 | 来源 |

### 确认但本轮未修复（溢出）
| # | 模块 | bug | 严重程度 | 原因 |

### 幻觉记录
| # | 声称的 bug | 实际情况 |
```

## 效率约束

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/efficiency.md

### subagent 模型分配（必须遵守）

| 阶段 | agent 类型 | model 参数 | 理由 |
|------|-----------|-----------|------|
| R1-R2 分析 | Explore agent | `model: "sonnet"` | 代码扫描是机械性工作，sonnet 快 3-4 倍 |
| R3 筛选轮 | 普通 agent（只读） | `model: "opus"` | 判断 bug 真实性需要准确性，但不需要 worktree |
| R4 验证+修复 | worktree agent | `model: "opus"` | 红绿验证需要准确性 |
| R5 交叉扫描 | Explore agent | `model: "sonnet"` | 模式匹配，sonnet 够用 |
| R5 交叉验证+修复 | worktree agent | `model: "opus"` | 同 R4 |
| Phase B-1 gate 规则 | 普通 agent（直接在 main） | `model: "opus"` | 写 gate 规则 + 1 次 preflight + commit |
| Phase B-2 文档+治理 | 普通 agent（直接在 main） | `model: "opus"` | B-1 完成后串行：更新文档 + 趋势 + 存量清理 + commit |

主会话保持 opus 做决策、去重、合并 worktree。
