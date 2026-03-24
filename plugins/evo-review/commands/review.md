---
description: 自进化代码审查：红绿验证对抗幻觉 + 门禁自动进化
allowed-tools: Read, Glob, Grep, Bash(*), Write, Edit, Agent
---

# /review — 自动测试体系强化

review 的核心产出是**测试基础设施**，不是 bug 修复。
找到的 bug 只是信号，用来发现测试体系的盲区 → 补基础设施让同类 bug 以后被自动抓住。

参考文档（自动加载）：
- 语言适配与扫描特征：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/language-adapters.md
- 测试维度定义：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/dimensions.md
- 测试运行策略：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/testing-strategy.md
- gate 骨架模板：@${CLAUDE_PLUGIN_ROOT}/skills/review/references/gate-template.sh

## 输入

$ARGUMENTS — 可选：
- `/review` — 最近 5 个 commit 涉及的模块
- `/review macbook-agent/src/task/` — 指定目录（可指定多个）
- `/review --deep` 或 `/deep` — 全模块循环强化模式（独立命令，详见 `/deep`）

## 前置

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/bootstrap.md

## 正式流程（普通模式）

### 第一步：分析

用 Explore agent 扫描（多模块并行，每个 agent 只传该语言的扫描特征）：
- A 资源泄漏 / B 标记锁 / C 错误吞没 / D 并发安全 / E 安全边界

**对每个发现，核心问题不是"怎么修这个 bug"，而是：**
1. 现有测试为什么没抓住？
2. 需要什么基础设施来**自动抓住这一类** bug？

### 第二步：输出确认清单

按**测试体系缺口**组织（不是按 bug 组织）：
```
## 模块：xxx（语言）

### 盲区 1：xxx（N 个同类问题）
- 缺口：没有检测...的机制
- 基础设施方案：在哪个文件加什么
- 佐证 bug：列出发现的具体 bug（修 bug 是附带的，基础设施才是目的）
```

末尾固定：**"以上 N 个盲区，确认后我直接开 subagent 执行。有要增删的吗？"**

暂停，等用户确认。

### 第三步：用户确认后，立即开 subagent 执行

**不再追问。** 多模块按模块拆 subagent 并行（不同语言不混）。

subagent 的工作分三阶段：

#### 阶段 A：红绿验证 + 修复（按模块拆 opus worktree agent 并行）

**每个发现必须经过红绿验证，对抗幻觉。**

对确认清单中的每个 bug，subagent 按顺序执行：
1. **读源码确认** — bug 是否存在
2. **写测试精确复现** → 运行 → 必须失败（红）
3. **写 fix** → 运行测试 → 必须通过（绿）
4. **跑该模块已有测试** → 必须无回归
5. 新测试的维度覆盖登记到 `test-governance/dimension-coverage.yaml`

**判定规则（无中间态）：**
- 红绿都通过 + 无回归 → ✅ 已验证，保留修复
- 步骤 2 测试直接通过（bug 不存在）→ ❌ 幻觉，撤销测试和修复
- 步骤 2 失败但原因与声称 bug 不符 → ❌ 幻觉，撤销
- 步骤 3 fix 后测试仍失败 → fix 有误，重写 fix 或丢弃
- 步骤 4 已有测试回归 → fix 引入新问题，必须修复回归或丢弃该发现
- 环境限制无法运行测试 → ⚠️ 未验证，标注原因

全部完成后：在 worktree 内 commit（只包含 ✅ 和 ⚠️ 的修复，❌ 的全部撤销）。
⚠️ 不合并到 main，不 push。worktree 分支保留，等用户确认后由主会话合并+push。

**幻觉发现（❌）不出现在最终报告的修复列表中，但在报告末尾单独列出供参考。**

#### 阶段 B：更新测试基础设施（阶段 A 完成后，单独 subagent）

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/phase-b.md

#### 阶段 C：输出验证报告 + 等待用户确认合并

阶段 A worktree 完成后，主会话汇总验证结果：

```
## 验证结果

| # | 标记 | 模块 | bug | 修复 |

### 建议写入 CLAUDE.md 的架构约束（如有）
| # | 约束（一句话） | 来源 bug | 详情 |

### 幻觉记录（❌）
| # | 声称的 bug | 实际情况 |
```

末尾固定：**"以上 N 个 ✅ 已验证修复在 worktree 分支中，确认后我合并到 main 并 push。"**

暂停，等用户确认。

用户确认后：
1. 合并已确认的 worktree 分支到 main + push
2. 清理 worktree
3. 执行阶段 B 更新测试基础设施

## --deep 模式

已独立为 `/deep` 命令。`/review --deep` 仍可用，等价于调用 `/deep`。

### 出报告前自检（强制，不可跳过）

在输出最终报告之前，逐项检查以下清单。任何未完成项必须补完后才能出报告：

- [ ] 阶段 A：所有 ✅ bug 已通过红绿验证 + 已在 worktree commit
- [ ] 阶段 C：验证报告已输出，用户已确认，worktree 已合并 + push
- [ ] Phase B-1：新 bug 模式已转化为 gate 规则（preflight 通过）
- [ ] Phase B-2：新测试 helper 已创建且被至少一个测试使用
- [ ] Phase B-3：test-governance/ 已更新
- [ ] Phase B-4：trend 已重新执行，高频规则已检查覆盖情况
- [ ] Phase B-5：top 1 高频规则的存量违规已清理
- [ ] Phase B-6：已检查是否有架构约束需建议写入 CLAUDE.md
- [ ] 所有改动已 commit + push
- [ ] worktree 已清理

最终报告：
```
## Review 报告

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

### 幻觉记录
| # | 声称的 bug | 实际情况 |
```

## 效率约束

@${CLAUDE_PLUGIN_ROOT}/skills/review/references/efficiency.md

### subagent 模型分配（必须遵守）

| 阶段 | agent 类型 | model 参数 | 理由 |
|------|-----------|-----------|------|
| 分析 | Explore agent | `model: "sonnet"` | 代码扫描是机械性工作，sonnet 快 3-4 倍 |
| 阶段 A 红绿验证+修复 | worktree agent | `model: "opus"` | 判断 bug 真实性需要准确性 |
| Phase B 基础设施 | worktree agent | `model: "sonnet"` | 写 gate 规则+更新文档，sonnet 够用 |

主会话保持 opus 做决策、去重、合并 worktree。
