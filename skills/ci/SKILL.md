---
name: ci
description: CI 验证 — git push 后自动执行。读取 test-governance/config.yaml 确定模块，按改动范围选择测试粒度，subagent 后台执行不阻塞对话。
allowed-tools: [Read, Glob, Grep, Bash, Agent]
---

# /ci — Post-Push CI 验证

## 触发方式

PostToolUse hook 检测到 git push 成功 → 输出信号 → Claude 开 background subagent 执行本 skill 的流程。

**用户无需手动调用。** hook 自动触发后，subagent 后台执行，不阻塞当前对话。

## 执行流程

### 1. 获取改动范围

```bash
# 优先使用 @{push}（push 前的远程 HEAD），如果没有上游分支则回退到 HEAD~1
git diff --name-only $(git rev-parse @{push} 2>/dev/null || echo HEAD~1) HEAD | tail -30
```

### 2. 读取模块配置

读取 `test-governance/config.yaml` 确定项目模块配置（语言、测试命令、目录结构）。

如果 config.yaml 不存在，只执行治理门禁（步骤 3），跳过模块测试。

### 3. 执行治理门禁

如果 `scripts/test-governance-gate.sh` 不存在，输出"测试治理体系尚未初始化，建议先运行 /review bootstrap"，跳过门禁和模块测试（步骤 4），直接到步骤 5 汇报。

```bash
bash scripts/test-governance-gate.sh preflight | tail -20
```

### 4. 按改动范围选测试

**遵循测试运行策略铁律：禁止随意跑全量测试。**

判断逻辑：

- **只改了文档/配置**（*.md, *.yaml, *.json, *.toml 等）→ 只跑治理门禁（步骤 3 已完成），结束
- **单模块改动** → 该模块执行：
  1. lint（lint_command，如有）
  2. 类型检查（typecheck_command，如有）
  3. 单元测试（unit_command）
  - 所有命令输出用 `| tail -20` 截断
- **跨模块改动** → 每个有改动的模块执行上述流程 + 额外执行集成测试（cross_command，如有）

### 5. 汇报结果

汇总输出：
```
## CI 验证结果

| 检查项 | 模块 | 状态 | 耗时 |
|--------|------|------|------|
| 治理门禁 | - | ✅/❌ | Ns |
| lint | module-a | ✅/❌ | Ns |
| 类型检查 | module-a | ✅/❌ | Ns |
| 单元测试 | module-a | ✅/❌ | Ns |
```

### 6. 失败处理

任何检查失败时，subagent 主动排查：
- 读取失败输出，定位原因
- **lint 失败**：如果是自动可修复的（--fix），自动修复 + commit + push；否则汇报
- **类型检查失败**：汇报错误位置和原因，不自动修复
- **测试失败**：分析失败原因并汇报给主对话，不自动修复
- **门禁失败**：汇报具体违规项，不自动修复

## 效率约束

- 所有 Bash 输出用 `| tail -N` 截断（默认 20 行）
- subagent 后台执行，不阻塞主对话
- 单模块改动只跑该模块的测试，绝不跑全量
- 预期超过 2 分钟的命令用 background 模式

## 参考

详细的 config.yaml 格式和模块测试命令配置见 `references/ci-procedure.md`。
