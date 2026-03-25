# 效率约束

## 业务流推导阶段
- 在主会话完成（读 config.yaml + git diff，1-3 次 tool use；无 cross_module 时退化为从 CLAUDE.md 推导，3-5 次）
- 业务流数量 ≤ 6，超出按优先级裁剪（近期改动涉及的 > P0 场景涉及的 > 其余）
- 单模块项目退化为按模块扫描

## 扫描阶段
- 按业务流拆 Explore agent 并行，每个 agent 跨读多模块
- 每条业务流最多 6 个发现（交界检查更聚焦，比按模块的 8 个更紧凑）

## worktree 验证阶段
- tool uses ≤ 50/agent，超过立即停止汇报
- **禁止在 worktree 内跑 preflight / gate.sh** — 回 main 后由主会话跑
- 修复项 ≤ 5/agent，超出拆第二个（同样 ≤ 5）
- 不同语言拆不同 agent
- lint + 单元测试在所有修复完成后统一跑 1 次，不要每个 bug 单独跑
- worktree 合并后立即清理

## 基础设施更新阶段
- 主会话直接做，不开 subagent
- gate 规则一次性写完再跑 preflight（最多 2 次）
- trend 只跑 1 次

## 通用
- Bash 输出 `| tail -N` 截断（默认 20 行）
- 长命令（>2min）交 subagent 后台，主会话只收摘要
- 失败先分析原因，不盲目重试
