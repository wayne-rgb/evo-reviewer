# Evo Review

**让 AI Code Review 的每一个发现都经得起验证的 Claude Code 插件。**

AI 做 code review 最大的问题不是"找不到 bug"，而是"报了一堆看起来像 bug 的东西，你花时间看完发现大部分是幻觉"。Evo Review 用红绿测试验证每一个发现——测试直接通过说明 bug 不存在，自动撤销，不浪费你的时间。

## 核心理念

**Review 的产出不是"修了几个 bug"，而是"测试体系变强了多少"。**

```
发现 bug → 为什么现有测试没抓到？→ 补回归测试 + 补基础设施让同类 bug 自动被抓
```

每次 review 都在强化项目的免疫系统，而不只是打补丁。

## 安装

```bash
claude mcp add-plugin evo-review -- /path/to/evo-review/plugins/evo-review
```

## 三个命令

| 命令 | 做什么 | 触发方式 |
|------|--------|----------|
| `/review` | 跨模块业务流审查 + 红绿验证 + 门禁进化 | 手动 |
| `/test-check` | 评估测试文件的维度覆盖质量 | 手动 |
| `/ci` | 按改动范围自动跑测试 | git push 后 hook 自动触发 |

### /review

```bash
/review              # 审查近 5 次 commit 涉及的业务流
/review src/task/     # 审查指定目录相关的业务流
/review *             # 全模块扫描
```

**三阶段执行：**

```
阶段 1  业务流追踪
        从 config.yaml 读取业务流定义，结合近期 git diff 筛选受影响的子集。
        Explore agent 并行追踪每条业务流，重点检查模块交界处的契约一致性。
        → 输出发现清单，等你确认。

阶段 2  红绿验证
        在 git worktree 中隔离执行。每个 bug：写测试复现(红) → 写修复(绿) → 无回归。
        测试直接通过 = 幻觉，自动撤销，不报给你。
        → 输出验证报告，等你确认合并。

阶段 3  基础设施进化
        新增 gate 规则、更新文档、趋势分析。
        高频违规自动纳入编码规范，从源头治理。
```

### /test-check

```bash
/test-check path/to/test.ts
```

基于 6 个维度评估测试质量：正常路径、副作用清理、并发安全、错误恢复、安全边界、故障后可用性。根据被测代码类型（纯函数 / 有状态类 / 单例服务 / 共享资源）判断哪些维度必须覆盖。

### /ci（自动）

git push 成功后，PostToolUse hook 自动检测并开后台 subagent 执行：

1. 治理门禁 `scripts/test-governance-gate.sh preflight`
2. 按改动范围选择测试（单模块只跑单模块，跨模块加集成测试）
3. 失败时主动排查修复

## 首次使用

首次执行 `/review` 会自动 bootstrap：

- 枚举项目模块，识别语言和测试命令
- 创建 `test-governance/` 目录（config.yaml、infrastructure.md 等）
- 生成 `scripts/test-governance-gate.sh` 门禁脚本
- 从 CLAUDE.md 通信拓扑推导跨模块业务流

**零配置开箱即用，单模块项目也能用。**

## Hook 机制

插件注册了两个 PostToolUse hook：

| 触发时机 | 做什么 |
|----------|--------|
| 每次 Edit/Write 文件后 | 自动检查编码规范违规（错误吞没、资源泄漏、未保护回调等），发现问题立即提醒修复 |
| 每次 Bash 执行后 | 检测 git push 成功，触发 CI subagent |

编码规范检查支持 TypeScript、Go、Swift、Python，且可通过项目的 `test-governance/hook-rules.json` 扩展自定义规则。

## 检查维度

### 跨模块交界（F1-F4，优先）

| 编号 | 检查项 | 典型问题 |
|------|--------|----------|
| F1 | 消息格式对齐 | 发送端加了字段，接收端没解析 |
| F2 | 状态机一致 | 前后端枚举值不一致，状态转换死锁 |
| F3 | 失败处理 | 一步失败，下游无超时无降级，永久挂起 |
| F4 | 时序假设 | 隐含的先后依赖被并发打破 |

### 代码模式（A-E，沿业务流路径顺带扫描）

| 编号 | 检查项 | 过滤条件 |
|------|--------|----------|
| A | 资源泄漏 | timer/listener/fd 未清理 |
| B | 标记锁未重置 | 异常路径状态标记残留 |
| C | 错误吞没 | catch 块未传播错误 |
| D | 并发安全 | 共享状态无保护 |
| E | 安全边界 | 入口未校验输入 |

**所有 A-E 发现必须能描述用户可感知的影响，纯理论风险不报。**

## 门禁自进化

```
违规日志（每次 preflight 自动记录）
    → 趋势分析（按规则/文件统计高频违规）
        → 高频规则纳入编码规范（从源头治理）
            → 卫生检查（删除从未触发的过时规则）
```

运行 `bash scripts/test-governance-gate.sh trend` 查看当前违规趋势。

## 支持语言

| 语言 | 支持程度 |
|------|----------|
| TypeScript / JavaScript | 完整（hook 规则 + 测试维度 + CI） |
| Go | 完整 |
| Swift | 完整 |
| Python | 完整 |
| Rust / Java | 基础（测试维度 + CI，无 hook 规则） |

## 插件结构

```
evo-review/
├── commands/
│   ├── review.md              # /review 命令定义
│   └── test-check.md          # /test-check 命令定义
├── skills/
│   ├── review/references/     # 审查流程参考文档
│   │   ├── bootstrap.md       #   首次初始化流程
│   │   ├── flow-tracing.md    #   业务流追踪 + 语言运行时排除规则
│   │   ├── dimensions.md      #   6 维度定义
│   │   ├── phase-b.md         #   阶段 3 基础设施更新
│   │   ├── efficiency.md      #   效率约束
│   │   ├── testing-strategy.md#   测试运行策略
│   │   └── gate-template.sh   #   门禁脚本骨架模板
│   └── ci/
│       ├── SKILL.md           # /ci 技能定义
│       └── references/
│           └── ci-procedure.md#   CI 执行流程
└── hooks/
    ├── hooks.json             # hook 注册配置
    ├── posttooluse.py         # 编码规范实时检查
    └── post-push-signal.sh    # git push CI 信号
```

## 许可证

MIT
