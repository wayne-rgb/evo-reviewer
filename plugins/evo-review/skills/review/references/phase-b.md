# 阶段 3：基础设施更新

**主会话直接执行，不开 subagent。**

## 步骤

1. **gate 规则**：在 gate.sh 新增 WARN 级规则。优先新增跨模块契约检查规则（枚举一致性、消息字段覆盖、状态机同步），其次覆盖单模块代码模式。一次性写完。
2. **preflight**：`bash scripts/test-governance-gate.sh preflight 2>&1 | tail -20`，BLOCK 失败则修正（最多 2 次）
3. **文档更新**：
   - infrastructure.md：新增 gate 规则 + 回归测试条目
   - dimension-coverage.yaml：新增测试的维度映射
4. **趋势检查**：`bash scripts/test-governance-gate.sh trend 2>&1 | tail -30`
   - ≥10 次高频规则：检查 coding-guidelines.md 是否有对应 ❌/✅ 示例，缺失则补
   - 最高频的 1 条规则：按 coding-guidelines.md 的 ✅ 写法批量修复存量违规，跑单元测试验证
5. **卫生检查**：trend 输出末尾自动包含"门禁卫生检查"段落（从未触发的规则列表）。若项目 gate.sh 的 `show_trend()` 缺少卫生检查段落，从插件 gate-template.sh 补入。对列出的规则，grep 确认对应代码模式是否仍存在 → 已消失的建议删除（列出，不自动删）
6. **commit + push**
