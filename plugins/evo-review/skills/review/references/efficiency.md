# 效率约束

- 分析用 Explore agent 并行，不在主会话逐文件读
- subagent 只跑单文件测试，不跑全量
- Bash 输出 `| tail -N` 截断
- 单个 subagent 修复项 ≤ 5
- 不同语言拆不同 subagent
- worktree 合并后立即清理，不留残余
