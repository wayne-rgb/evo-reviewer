# 阶段 3：基础设施更新

**主会话直接执行，不开 subagent。** 改动内容是 gate 脚本和 test-governance 文档，不需要 subagent 的推理能力。

## 步骤

1. **gate 规则**：在 gate.sh 新增 WARN 级规则，覆盖本轮 bug 的共性模式。一次性写完。
2. **preflight**：`bash scripts/test-governance-gate.sh preflight 2>&1 | tail -20`，BLOCK 失败则修正（最多 2 次）
3. **文档更新**：
   - infrastructure.md：新增 gate 规则 + 回归测试条目
   - dimension-coverage.yaml：新增测试的维度映射
4. **趋势检查**：`bash scripts/test-governance-gate.sh trend 2>&1 | tail -30`，≥10 次高频规则检查 coding-guidelines.md
5. **commit + push**
