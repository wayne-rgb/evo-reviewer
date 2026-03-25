# Evo Review

自进化测试框架 — Claude Code Plugin

## 三层架构

| 层级 | 能力 | 触发 |
|------|------|------|
| **执行层** `/ci` | git push 后自动 CI 验证 | PostToolUse hook 自动 |
| **优化层** `/review` | 跨模块业务流审查 + 红绿验证 + 基础设施进化 | 手动 |
| **检查层** `/test-check` | 测试维度覆盖质量评估 | 手动 |

## 核心特色

1. **红绿验证对抗幻觉** — 每个发现必须红(复现)→绿(修复)→无回归，测试直接通过=幻觉，自动撤销
2. **产出是测试基础设施** — bug 是信号，目的是让同类 bug 以后被自动抓住
3. **门禁自动进化** — 违规日志 → 趋势分析 → 高频规则 → 编码规范 → 源头治理
4. **Hook 机械执行** — posttooluse hook 在每次编辑后自动检查违规
5. **业务流驱动** — 从 P0 场景和通信拓扑推导受影响的端到端业务流，在模块交界处检查契约一致性

## 使用

```bash
/review                    # 审查近 5 次 commit 涉及的业务流
/review src/task/          # 审查指定目录
/review *                  # 全模块扫描
/test-check path/to/test   # 检查测试维度覆盖
```

`/ci` 由 git push 后 hook 自动触发，无需手动调用。

## /review 流程（3 阶段）

```
阶段 1：业务流追踪（Explore agent 并行）→ 确认清单 → 用户确认
    ↓
阶段 2：验证+修复（worktree agent）→ 验证报告 → 用户确认合并
    ↓
阶段 3：基础设施更新（主会话直接做）→ gate 规则 + 文档 → push
```

## 首次使用

首次 `/review` 自动 bootstrap：
- 创建 `test-governance/` 目录（config.yaml、infrastructure.md 等）
- 生成 `scripts/test-governance-gate.sh` 门禁脚本
- 追加测试原则到项目 CLAUDE.md

## 插件结构

```
evo-review/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── review.md                   # /review 命令（用户直接调用）
│   └── test-check.md               # /test-check 命令
├── skills/
│   ├── review/
│   │   └── references/
│   │       ├── bootstrap.md        # 首次 bootstrap 流程
│   │       ├── phase-b.md          # 阶段 3 基础设施更新
│   │       ├── efficiency.md       # 效率约束
│   │       ├── flow-tracing.md     # 业务流追踪指南 + 排除规则
│   │       ├── dimensions.md       # 6 维度定义
│   │       ├── testing-strategy.md # 测试运行策略
│   │       └── gate-template.sh    # 门禁骨架模板
│   └── ci/
│       ├── SKILL.md                # /ci（hook 自动触发）
│       └── references/
│           └── ci-procedure.md
├── hooks/
│   ├── hooks.json
│   ├── posttooluse.py
│   └── post-push-signal.sh
└── README.md
```

## 支持语言

TypeScript/JavaScript、Go、Swift、Python（完整支持）；Rust/Java（基础支持）

## 许可证

MIT
