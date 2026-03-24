# 效率约束

- 分析用 Explore agent 并行，不在主会话逐文件读
- subagent 只跑单文件测试，不跑全量
- Bash 输出 `| tail -N` 截断
- 单个 subagent 修复项 ≤ 5
- 某模块确认 bug > 5 时：按 HIGH→MEDIUM→LOW 排序，前 5 项进入第一个 R3 agent，剩余拆第二个 R3 agent（同样 ≤ 5）。如总数 > 10，超出部分列入报告的"确认但本轮未修复"栏
- 不同语言拆不同 subagent
- worktree 合并后立即清理，不留残余
- Phase B 的 preflight 最多跑 1 次（所有规则写完后统一验证），禁止逐条验证
