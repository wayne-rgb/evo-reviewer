# Phase B：更新测试基础设施

**这一步是 review 的核心产出，不能跳过。**

**执行方式：直接在 main 上执行，不使用 worktree。** Phase B 改动的是 gate 脚本、test-governance 文档、编码规范等基础设施文件，不涉及业务代码，无需 worktree 隔离。直接在 main 上改动可避免 worktree 路径解析问题（gate 脚本的 ROOT_DIR 在 worktree 下可能不正确）。

根据已验证 bug 的模式，更新以下四类基础设施：

1. **gate 新增规则**（治本）— 在 `scripts/test-governance-gate.sh` 中新增静态分析规则：
   - 分析已验证 bug 的共性模式
   - 每个模式对应一个 gate 规则，能在 preflight 时自动检测同类问题
   - 新规则默认仅警告不阻塞，验证稳定后再升级为阻塞
   - 运行 `bash scripts/test-governance-gate.sh preflight` 验证新规则不破坏门禁

2. **测试 helper 扩展**（治本）— 在对应模块的测试基础设施中新增通用方法：
   - 先查 test-governance/config.yaml 中是否记录了测试基础设施路径
   - 没有则搜索项目中已有的测试 helper/fixture/infrastructure 文件
   - 新 helper 必须被至少一个回归测试使用

3. **更新 test-governance/ 文档**：
   - infrastructure.md：gate 规则描述 + 测试基础设施表 + 新增回归测试条目
   - coding-guidelines.md：高频违规的 ❌/✅ 对比示例
   - dimension-coverage.yaml：新增测试的维度映射

4. **高频违规源头治理**（自动，不需用户提醒）：
   - 重新执行 `bash scripts/test-governance-gate.sh trend`
   - 对所有 ≥10 次的高频规则，检查 test-governance/coding-guidelines.md 是否已有对应指导
   - 缺失的：从违规日志提取典型模式，编写 ❌/✅ 对比示例，加入 coding-guidelines.md
   - 已有但仍高频的：说明规范已存在但未生效，在 commit message 中记录

5. **存量违规清理**（自动，每次 review 清一批）：
   - 从 trend 输出中取触发次数最多的 1 条规则
   - 按 coding-guidelines.md 中的 ✅ 正确写法批量修复
   - 修复后跑该模块的单元测试验证无回归
   - 一次只清 1 条规则，下次 review 清第 2 条

6. **识别架构约束 → 建议写入 CLAUDE.md**（自动）：
   - 从已验证 bug 中识别跨模块/跨端/跨文件的架构级约束
   - 如有发现，在确认清单/报告中单独列出
   - 不自动写入 CLAUDE.md，由用户确认后写入

subagent 内部：写 gate 规则 + 写 helper → 跑 preflight 验证 → 趋势分析 + 源头治理 → 存量违规清理（top 1 规则）→ 更新 test-governance/ → commit + push
