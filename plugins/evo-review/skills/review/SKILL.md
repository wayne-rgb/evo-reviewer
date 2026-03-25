---
name: review
description: 自进化代码审查：红绿验证对抗幻觉 + 门禁自动进化。/review 扫描近 5 次 commit，/review dir/ 指定目录，/review * 全模块扫描。
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, Agent
---

# /review — 自动测试体系强化

核心产出是**测试基础设施**，不是 bug 修复。bug 是信号 → 发现测试盲区 → 补基础设施。

扫描指南（含排除规则）：[language-adapters.md](references/language-adapters.md)

## 输入

$ARGUMENTS — 可选：
- `/review` — 近 5 次 commit 涉及的模块
- `/review dir/` — 指定目录
- `/review *` — 全模块扫描

## 前置（每次执行）

1. 如果没有 `test-governance/` → 读取 [bootstrap.md](references/bootstrap.md) 并执行 bootstrap
2. `bash scripts/test-governance-gate.sh preflight 2>&1 | tail -20`
3. `bash scripts/test-governance-gate.sh trend 2>&1 | tail -30`
4. 确定扫描范围：无参数用 `git diff --name-only HEAD~5`，`*` 扫全模块

## 阶段 1：扫描

按模块拆 Explore agent 并行。每个 agent 的 prompt 必须包含上方已加载的 language-adapters.md 的完整内容（特别是排除规则），加上：
- 扫描五类模式：A 资源泄漏 / B 标记锁 / C 错误吞没 / D 并发安全 / E 安全边界
- 全模块模式（`*`）额外关注：架构问题、状态机非法转换、跨端一致性、测试体系盲区
- **每模块最多 8 个发现**，按严重程度排序
- 每个发现必须含：文件:行号、代码证据、为什么这不是语言运行时的正常行为
- 趋势热点文件优先分析

→ 主会话汇总去重，输出确认清单（按测试体系缺口组织），等用户确认。

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

**worktree 硬约束（见 [efficiency.md](references/efficiency.md)）：**
- tool uses ≤ 50，超过立即停止汇报
- **禁止在 worktree 内跑 preflight / gate.sh**
- 修复项 ≤ 5/agent，超出拆第二个

→ 主会话输出验证报告，等用户确认合并。
→ 用户确认后：合并 worktree + push + 清理 worktree → 阶段 3。

## 阶段 3：基础设施更新（主会话直接做，不开 subagent）

见 [phase-b.md](references/phase-b.md)

## 报告模板

```
## Review 报告

### 测试体系强化
| 模块 | 新增基础设施 | 能自动抓住的问题类型 |

### 附带修复的 bug
| # | 标记 | 模块 | bug | 修复 |

### 验证统计
| 发现数 | ✅ 已验证 | ❌ 幻觉 | ⚠️ 未验证 |

### 幻觉记录
| # | 声称的 bug | 实际情况 |
```
