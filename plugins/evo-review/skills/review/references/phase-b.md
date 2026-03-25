# 阶段 3：基础设施更新

**主会话直接执行，不开 subagent。**

## 步骤

1. **gate 规则**：在 gate.sh 新增 WARN 级规则，覆盖本轮 bug 的共性模式。一次性写完。
2. **preflight**：`bash scripts/test-governance-gate.sh preflight 2>&1 | tail -20`，BLOCK 失败则修正（最多 2 次）
3. **文档更新**：
   - infrastructure.md：新增 gate 规则 + 回归测试条目
   - dimension-coverage.yaml：新增测试的维度映射
4. **趋势检查**：`bash scripts/test-governance-gate.sh trend 2>&1 | tail -30`
   - ≥10 次高频规则：检查 coding-guidelines.md 是否有对应 ❌/✅ 示例，缺失则补
   - 最高频的 1 条规则：按 coding-guidelines.md 的 ✅ 写法批量修复存量违规，跑单元测试验证
5. **卫生检查**：trend 中长期 0 触发的规则，grep 确认模式已从代码消失 → 建议删除（列出，不自动删）
6. **commit + push**
