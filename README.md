# Evo Review

自进化代码审查框架 — Claude Code Plugin

**每次 review 都让系统变强：红绿验证对抗幻觉，门禁自动进化，hook 机械执行编码规范。**

## 核心特色

1. **红绿验证对抗幻觉** — 每个 AI 发现的 bug 必须通过红测试（复现失败）→ 绿测试（修复通过）→ 无回归，三项全过才算已验证。测试直接通过 = 幻觉，自动撤销。
2. **产出是测试基础设施** — review 的核心产出不是 bug 修复，而是让同类 bug 以后被自动抓住的基础设施（gate 规则、测试 helper）。
3. **门禁自动进化** — 违规日志 → 趋势分析 → 高频规则 → 编码规范 → 源头治理，形成正反馈闭环。
4. **Hook 机械执行** — posttooluse hook 在每次代码编辑后自动检查高频违规，比"请遵守规范"更可靠。

## 安装

```bash
# 在 Claude Code 中
/plugin install evo-review
```

或手动：
```bash
git clone <repo-url> ~/.claude/plugins/evo-review
```

## 使用

```bash
/review                    # 审查最近 5 个 commit 涉及的模块
/review src/task/          # 审查指定目录
/review --deep             # 全模块深度审查（5 轮分析 + 红绿验证 + 交叉检验）
/test-check path/to/test   # 检查测试文件的维度覆盖质量
```

## 首次使用

在任何项目中首次运行 `/review`，会自动 bootstrap：

```
test-governance/
├── config.yaml                 # 模块配置（语言、测试命令、helper 路径）
├── infrastructure.md           # 测试基础设施注册表
├── coding-guidelines.md        # 高频违规源头治理规范
├── dimension-coverage.yaml     # 测试维度覆盖映射
└── gate-violations.log         # 违规日志

scripts/
└── test-governance-gate.sh     # 门禁脚本
```

**不需要手动配置，不依赖 CLAUDE.md。**

## 工作流

### 普通模式 `/review`

```
分析（sonnet Explore）→ 输出确认清单 → 用户确认
    ↓
阶段 A：红绿验证 + 修复（opus worktree，按模块并行）
    ↓
阶段 C：输出验证报告 → 用户确认合并
    ↓
阶段 B：更新测试基础设施（gate 规则 + helper + 源头治理）
```

### 深度模式 `/review --deep`

```
R1: 标准五类扫描
R2: 假设 R1 修完后暴露的新问题
R3: 更深层架构/状态机/测试体系盲区
R4: 红绿验证 + 修复（按模块拆 opus worktree）
R5: 交叉检验（跨模块同类 bug）
    ↓
用户确认 → 合并 → 阶段 B
```

## Plugin 结构

```
evo-review/
├── .claude-plugin/
│   └── plugin.json                 # Plugin 元数据
├── skills/
│   ├── review/
│   │   ├── SKILL.md                # /review 命令（自包含）
│   │   └── references/
│   │       ├── dimensions.md       # 6 维度定义 + 适用性表
│   │       ├── language-adapters.md # 语言适配（泄漏形态/检测方式）
│   │       └── gate-template.sh    # 门禁骨架模板
│   └── test-check/
│       └── SKILL.md                # /test-check 命令
├── hooks/
│   ├── hooks.json                  # Hook 注册
│   └── posttooluse.py              # 编辑后自动检查违规
└── README.md
```

## 支持的语言

| 语言 | 泄漏检测 | Hook 规则 | Gate 规则 |
|------|---------|----------|----------|
| TypeScript/JavaScript | ✅ | ✅ | ✅ |
| Go | ✅ | ✅ | ✅ |
| Swift | ✅ | ✅ | ✅ |
| Python | ✅ | ✅ | ✅ |
| Rust/Java | ✅ | 基础 | 基础 |

## 许可证

MIT
