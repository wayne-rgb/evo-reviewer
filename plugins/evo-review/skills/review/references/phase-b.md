# Phase B：更新测试基础设施

**这一步是 review 的核心产出，不能跳过。**

**执行方式：直接在 main 上执行，不使用 worktree。** Phase B 改动的是 gate 脚本、test-governance 文档、编码规范等基础设施文件，不涉及业务代码，无需 worktree 隔离。直接在 main 上改动可避免 worktree 路径解析问题（gate 脚本的 ROOT_DIR 在 worktree 下可能不正确）。

**Phase B 拆为两个串行 subagent，降低单 agent 复杂度、避免 preflight 循环：**

## Phase B-1：gate 规则 + preflight（subagent 1）

任务范围：只写 gate 规则和 test helper，写完后跑 1 次 preflight，然后 commit。

1. **gate 新增规则**（治本）— 在 `scripts/test-governance-gate.sh` 中新增静态分析规则：
   - 分析已验证 bug 的共性模式
   - 每个模式对应一个 gate 规则，能在 preflight 时自动检测同类问题
   - 新规则默认仅警告不阻塞（WARN），验证稳定后再升级为阻塞
   - **所有新规则写完后只跑 1 次 `bash scripts/test-governance-gate.sh preflight 2>&1 | tail -30`**，禁止每写一条就跑一次

2. **测试 helper 扩展**（治本）— 在对应模块的测试基础设施中新增通用方法：
   - 先查 test-governance/config.yaml 中是否记录了测试基础设施路径
   - 没有则搜索项目中已有的测试 helper/fixture/infrastructure 文件
   - 新 helper 必须被至少一个回归测试使用

3. **识别跨模块约束 → 优先建议 gate 规则**（自动）：
   - 从已验证 bug 中识别跨模块/跨端/跨文件的架构级约束
   - **跨模块契约类**（类型定义不一致、状态机不同步、枚举缺失等）→ 优先建议新增 gate 规则到 `scripts/test-governance-gate.sh` 的跨模块检查区块，用 diff/grep 机械检测，不依赖 AI
   - **架构约束类**（部署顺序、兼容性、设计决策等）→ 建议写入 CLAUDE.md
   - 如有发现，在确认清单/报告中单独列出，标明建议类型（gate 规则 / CLAUDE.md）
   - 不自动写入，由用户确认后执行

**B-1 完成后 commit + push。**

**B-1 效率铁律：**
- preflight 最多跑 **1 次**（所有规则写完后统一验证），禁止每条规则单独跑
- 新规则都是 WARN 级别，即使有误报也不会阻塞门禁，后续 review 再修正
- 如果 preflight 失败，检查是哪条新规则导致的，修正后再跑 1 次，总计不超过 2 次
- 预期 tool uses ≤ 30

## Phase B-2：文档更新 + 趋势治理 + 存量清理（subagent 2）

任务范围：B-1 commit 后执行。更新文档、趋势分析、存量清理、卫生检查。不再修改 gate.sh。

1. **更新 test-governance/ 文档**：
   - infrastructure.md：gate 规则描述 + 测试基础设施表 + 新增回归测试条目
   - coding-guidelines.md：高频违规的 ❌/✅ 对比示例
   - dimension-coverage.yaml：新增测试的维度映射

2. **高频违规源头治理**（自动，不需用户提醒）：
   - 执行 `bash scripts/test-governance-gate.sh trend 2>&1 | tail -40`
   - 对所有 ≥10 次的高频规则，检查 test-governance/coding-guidelines.md 是否已有对应指导
   - 缺失的：从违规日志提取典型模式，编写 ❌/✅ 对比示例，加入 coding-guidelines.md
   - 已有但仍高频的：说明规范已存在但未生效，在 commit message 中记录

3. **存量违规清理**（自动，每次 review 清一批）：
   - 从 trend 输出中取触发次数最多的 1 条规则
   - 按 coding-guidelines.md 中的 ✅ 正确写法批量修复
   - 修复后跑该模块的单元测试验证无回归
   - 一次只清 1 条规则，下次 review 清第 2 条

4. **gate 规则卫生检查**（自动，防止 gate.sh 无限膨胀）：
   - 从 trend 输出中找**长期 0 触发**的规则（连续多次 review 均无违规记录）
   - 对每条 0 触发规则，grep codebase 确认该模式是否已从代码中消失。消失了 → 规则完成使命，建议删除
   - **注意：hook 和 gate 是互补关系，不是冗余关系。** hook 只在 Claude 编辑时触发（预防新增），gate 扫描全量代码（发现存量 + 非 Claude 写的代码）。不能因为 hook 有同类规则就删 gate 规则
   - 检查是否有多条规则检查同一类问题的不同变体 → 建议合并（合并 ≠ 删除，是减少重复代码）
   - 检查扫描路径是否包含了不该扫的目录（如标准库、vendor、node_modules）→ 建议排除
   - 淘汰/合并建议列入确认清单，由用户确认后执行

**B-2 完成后 commit + push。**

**B-2 效率铁律：**
- 不修改 gate.sh（gate 规则由 B-1 负责）
- trend 只跑 1 次，存量清理只清 top 1
- 预期 tool uses ≤ 25
