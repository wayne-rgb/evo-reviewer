# Evo Review

自进化测试框架 — Claude Code Plugin

**涵盖测试原则、测试执行、测试优化的综合框架：铁律+6维度写入项目DNA，post-push CI 自动验证，review 红绿验证+门禁进化让系统持续变强。**

## 四层架构

| 层级 | 能力 | 触发方式 |
|------|------|----------|
| **原则层** | 测试铁律 + 6 维度 + CI 策略写入项目 CLAUDE.md | 首次 `/review` 自动 bootstrap |
| **执行层** `/ci` | git push 后自动 CI 验证（lint + 类型检查 + 单元测试） | PostToolUse hook 自动触发 |
| **优化层** `/review` | 代码审查 + 红绿验证 + 基础设施进化 | 手动调用 |
| **检查层** `/test-check` | 测试文件维度覆盖质量评估 | 手动调用 |

## 核心特色

1. **原则内化** — 首次 bootstrap 自动将测试铁律（禁止随意跑全量）、6 维度标准、CI 策略写入项目 CLAUDE.md，成为项目 DNA。
2. **Post-Push CI** — git push 成功后 hook 自动触发，subagent 后台按改动范围选测试，不阻塞对话。
3. **红绿验证对抗幻觉** — 每个 AI 发现的 bug 必须通过红测试（复现失败）→ 绿测试（修复通过）→ 无回归，三项全过才算已验证。测试直接通过 = 幻觉，自动撤销。
4. **产出是测试基础设施** — review 的核心产出不是 bug 修复，而是让同类 bug 以后被自动抓住的基础设施（gate 规则、测试 helper）。
5. **门禁自动进化** — 违规日志 → 趋势分析 → 高频规则 → 编码规范 → 源头治理，形成正反馈闭环。
6. **Hook 机械执行** — posttooluse hook 在每次代码编辑后自动检查高频违规，比"请遵守规范"更可靠。

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

`/ci` 无需手动调用 — git push 成功后由 PostToolUse hook 自动触发，Claude 开 background subagent 后台执行 CI 验证：
- 读取 `test-governance/config.yaml` 确定模块配置
- 按改动范围选测试（只改文档 → 只跑门禁；单模块 → lint + 类型检查 + 单元测试；跨模块 → 额外跑集成测试）
- 结果自动反馈到对话，失败时主动排查

## 首次使用

在任何项目中首次运行 `/review`，会自动 bootstrap 全套测试体系：

**测试治理目录：**
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

**项目 CLAUDE.md 自动追加：**
- 测试运行策略铁律（禁止随意跑全量测试的决策树）
- 测试编写的 6 个维度标准 + 适用性表
- CI 策略说明（post-push 自动验证流程）

**Post-Push CI Hook 自动配置：**
- `.claude/hooks/post-push-signal.sh` — git push 后触发 CI 信号
- `.claude/settings.json` 中注册 hook（如尚未配置）

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

### Post-Push CI `/ci`（自动）

```
git push 成功 → hook 信号
    ↓
Claude 开 background subagent
    ↓
读取 config.yaml → 按改动范围选测试 → 执行
    ↓
结果反馈到对话（失败时主动排查）
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
│   │       ├── gate-template.sh    # 门禁骨架模板
│   │       └── testing-strategy.md # 测试运行策略铁律 + CI 策略
│   ├── ci/
│   │   ├── SKILL.md                # /ci 命令（post-push 自动触发）
│   │   └── references/
│   │       └── ci-procedure.md     # CI 执行流程 + config.yaml 格式
│   └── test-check/
│       └── SKILL.md                # /test-check 命令
├── hooks/
│   ├── hooks.json                  # Hook 注册（编码规范 + post-push CI）
│   ├── posttooluse.py              # 编辑后自动检查违规
│   └── post-push-signal.sh         # git push 后触发 CI 信号
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
