---
name: review
description: /review — 自进化代码审查：红绿验证对抗幻觉 + 门禁自动进化。使用 /review 审查最近改动，/review path/ 审查指定目录，/review --deep 全模块深度审查。
argument-hint: [path...] [--deep]
allowed-tools: [Read, Glob, Grep, Bash, Write, Edit, Agent]
---

# /review — 自动测试体系强化

review 的核心产出是**测试基础设施**，不是 bug 修复。
找到的 bug 只是信号，用来发现测试体系的盲区 → 补基础设施让同类 bug 以后被自动抓住。

## 输入

$ARGUMENTS — 可选：
- `/review` — 最近 5 个 commit 涉及的模块
- `/review macbook-agent/src/task/` — 指定目录（可指定多个）
- `/review --deep` — 全模块循环强化模式（5 轮分析→红绿验证+修复→基础设施，对抗幻觉）

## 前置：模块枚举 + 就绪检查

### Bootstrap（首次运行自动初始化）

如果项目没有 `test-governance/` 目录，按以下步骤初始化：

1. 创建 test-governance/ 目录及核心文件：
   - `test-governance/config.yaml` — 扫描项目生成模块配置（语言、测试命令、helper 路径）
   - `test-governance/infrastructure.md` — 空的基础设施注册表模板
   - `test-governance/coding-guidelines.md` — 空的编码规范模板
   - `test-governance/dimension-coverage.yaml` — 空的维度映射

config.yaml 格式：
```yaml
# test-governance/config.yaml
modules:
  module-name:
    language: typescript|go|swift|python|rust|java
    src_dir: "src/"
    test_command: "npx vitest run"
    unit_command: "npm run test:unit"
    cross_command: "npm run test:cross"
    lint_command: "npm run lint"
    typecheck_command: "npx tsc --noEmit"
    test_dir: "src/__tests__"
    helper_dir: "src/__tests__/helpers"
```

2. 如果项目没有 `scripts/test-governance-gate.sh`，按 references/gate-template.sh 生成。

3. 追加测试原则到项目 CLAUDE.md：
   - 读取 references/testing-strategy.md，追加到项目 CLAUDE.md（如果尚未包含"测试运行策略"章节）
   - 读取 references/dimensions.md 中的维度定义和适用性表，追加到项目 CLAUDE.md（如果尚未包含"测试编写的 6 个维度"章节）
   - 追加 CI 策略说明

4. 配置 post-push CI hook：
   - 先检查项目 .claude/settings.json 中是否已有功能等价的 post-push hook（检查现有 hook 命令中是否包含 "git push" 和 "subagent" 关键词），如果有则跳过创建，避免重复触发
   - 如果没有等价 hook，在 .claude/settings.json 中添加 post-push hook 配置
   - 创建 .claude/hooks/post-push-signal.sh（从 evo-review 的 hooks/ 复制）

5. 检查 .gitignore 是否包含 `test-governance/gate-violations.log`，如果没有则追加，避免违规日志被提交到版本控制。

Bootstrap 产物纳入确认清单，和 review 发现一起确认。

### test-governance 文件填充策略

bootstrap 创建的文件初始为空模板，由 /review 的 Phase B 逐步填充。以下是每个文件的结构和填充规则：

#### infrastructure.md（测试基础设施注册表）

结构：按模块分组的表格，每行记录一项基础设施。

| 列 | 说明 |
|----|------|
| 基础设施名称 | 简短描述（如"全局 setInterval 泄漏检测"） |
| 文件路径 | 相对路径 |
| 覆盖场景 | 这个基础设施能自动抓住什么类型的 bug |
| 来源 | 哪次 /review 引入的（commit hash 或日期） |

填充规则：
- Phase B 每新增一个 gate 规则、test helper 或回归测试，必须登记到此表
- 不登记 = 不存在（后续 /review 会重复建设同类基础设施）

#### coding-guidelines.md（编码规范）

结构：按语言分组，每条规范包含 ❌ 错误写法和 ✅ 正确写法的对比示例。

填充规则：
- gate trend 分析中 ≥10 次的高频违规规则，自动提取为编码规范
- 每条规范必须有具体的代码示例（不是抽象描述）
- 规范和 posttooluse hook 的规则对应，hook 机械执行规范

#### p0-cases.tsv（P0 场景矩阵）

结构：TSV 格式，每行一个关键场景。

| 列 | 说明 |
|----|------|
| 场景 ID | 唯一标识（如 PAIRING_KEY_NIL_CLEARS_LOCAL） |
| 场景描述 | 用户视角的一句话描述 |
| 验证关键词 | gate preflight 用 grep 检查的关键词 |
| 验证范围 | 在哪些目录下搜索关键词 |

填充规则：
- /review 发现的涉及核心用户链路的 bug，如果回归会导致产品不可用，加入 P0 矩阵
- 不是所有 bug 都是 P0，只有"用户完全无法使用某个核心功能"才算
- gate preflight 会自动检查所有 P0 场景是否有对应的测试覆盖

#### dimension-coverage.yaml（测试维度映射）

结构：YAML，按模块 → 测试文件 → 维度编号列表。

填充规则：
- Phase B 每次新增或修改测试文件时，更新对应条目
- 维度编号 1-6 对应：正常路径/副作用清理/并发安全/错误恢复/安全边界/故障后可用
- gate 的 check_dimension_coverage 从此文件读取数据，统计维度分布

#### config.yaml（模块配置）

填充规则：
- bootstrap 时自动扫描项目结构生成
- /review 发现新模块（如新增的子包）时更新
- 用户手动调整测试命令后应同步更新

### 1. 枚举模块
扫描项目根目录（package.json / go.mod / *.xcodeproj / pyproject.toml / setup.py / setup.cfg / requirements.txt / Cargo.toml / build.gradle），输出：
```
| 模块 | 语言 | 源文件数 | 测试文件数 | 基础设施 |
```
单模块项目跳过。

### 2. 确定范围
- 无参数：`git diff --name-only HEAD~5` 归属到模块
- `--deep`：所有模块（>5 个时取 top 5）

### 3. 就绪检查
对每个模块确认：能不能跑单文件测试？有没有测试？

- **缺测试信息** → 推断测试命令，补入 test-governance/config.yaml，和 review 发现一起确认
- **零测试** → 该模块只建测试骨架（按 references/language-adapters.md），不扫 bug
- **环境跑不了**（如缺 Xcode）→ 扫 bug 但跳过测试执行，标注 ⚠️
- **无 gate.sh** → 首次 review 时按 references/gate-template.sh 生成，纳入确认清单

### 4. 违规趋势读取（进化闭环）
如果项目有 `scripts/test-governance-gate.sh`，执行 `bash scripts/test-governance-gate.sh trend`。
- **高频规则（≥10 次）**→ 本轮分析重点关注该类问题，并在确认清单中建议将对应模式加入 test-governance/coding-guidelines.md
- **高频文件** → 优先分析这些文件
- **无 gate.sh 或无日志** → 跳过，不阻塞

## 正式流程（普通模式）

### 第一步：分析

用 Explore agent 扫描（多模块并行，每个 agent 只传该语言的扫描特征，参照 references/language-adapters.md）：
- A 资源泄漏 / B 标记锁 / C 错误吞没 / D 并发安全 / E 安全边界

**对每个发现，核心问题不是"怎么修这个 bug"，而是：**
1. 现有测试为什么没抓住？
2. 需要什么基础设施来**自动抓住这一类** bug？

### 第二步：输出确认清单

按**测试体系缺口**组织（不是按 bug 组织）：
```
## 模块：xxx（语言）

### 盲区 1：xxx（N 个同类问题）
- 缺口：没有检测...的机制
- 基础设施方案：在哪个文件加什么
- 佐证 bug：列出发现的具体 bug（修 bug 是附带的，基础设施才是目的）
```

末尾固定：**"以上 N 个盲区，确认后我直接开 subagent 执行。有要增删的吗？"**

暂停，等用户确认。

### 第三步：用户确认后，立即开 subagent 执行

**不再追问。** 多模块按模块拆 subagent 并行（不同语言不混）。

subagent 的工作分三阶段：

#### 阶段 A：红绿验证 + 修复（按模块拆 opus worktree agent 并行）

**每个发现必须经过红绿验证，对抗幻觉。** 流程与 --deep R4 相同，但只有一轮分析（无 R2/R3/R5）。

对确认清单中的每个 bug，subagent 按顺序执行：
1. **读源码确认** — bug 是否存在
2. **写测试精确复现** → 运行 → 必须失败（红）
3. **写 fix** → 运行测试 → 必须通过（绿）
4. **跑该模块已有测试** → 必须无回归
5. 新测试的维度覆盖登记到 `test-governance/dimension-coverage.yaml`（格式见 references/dimensions.md）

**判定规则（与 --deep 一致，无中间态）：**
- 红绿都通过 + 无回归 → ✅ 已验证，保留修复
- 步骤 2 测试直接通过（bug 不存在）→ ❌ 幻觉，撤销测试和修复
- 步骤 2 失败但原因与声称 bug 不符 → ❌ 幻觉，撤销
- 步骤 3 fix 后测试仍失败 → fix 有误，重写 fix 或丢弃
- 步骤 4 已有测试回归 → fix 引入新问题，必须修复回归或丢弃该发现
- 环境限制无法运行测试 → ⚠️ 未验证，标注原因

全部完成后：在 worktree 内 commit（只包含 ✅ 和 ⚠️ 的修复，❌ 的全部撤销）。
⚠️ 不合并到 main，不 push。worktree 分支保留，等用户确认后由主会话合并+push。

**幻觉发现（❌）不出现在最终报告的修复列表中，但在报告末尾单独列出供参考。**

#### 阶段 B：更新测试基础设施（阶段 A 完成后，单独 subagent）

**这一步是 review 的核心产出，不能跳过。** 根据已验证 bug 的模式，更新以下四类基础设施：

1. **gate 新增规则**（治本）— 在 `scripts/test-governance-gate.sh` 中新增静态分析规则：
   - 分析已验证 bug 的共性模式（如"回调未加 try-catch"、"递归无深度限制"、"空 catch 块"）
   - 每个模式对应一个 gate 规则，能在 preflight 时自动检测同类问题
   - 新规则默认仅警告不阻塞，验证稳定后再升级为阻塞
   - 运行 `bash scripts/test-governance-gate.sh preflight` 验证新规则不破坏门禁

2. **测试 helper 扩展**（治本）— 在对应模块的测试基础设施中新增通用方法：
   - 先查 test-governance/config.yaml 中是否记录了测试基础设施路径，有则直接使用
   - 没有则搜索项目中已有的测试 helper/fixture/infrastructure 文件，就近放置
   - 例如：`verifyCallbackErrorIsolation()`、`verifyResourceCleanupOnError()` 等
   - 新 helper 必须被至少一个回归测试使用

3. **更新 test-governance/ 文档**：
   - infrastructure.md：gate 规则描述 + 测试基础设施表 + 新增回归测试条目
   - coding-guidelines.md：高频违规的 ❌/✅ 对比示例
   - dimension-coverage.yaml：新增测试的维度映射

4. **高频违规源头治理**（自动，不需用户提醒）：
   - 重新执行 `bash scripts/test-governance-gate.sh trend`
   - 对所有 ≥10 次的高频规则，检查 test-governance/coding-guidelines.md 是否已有对应指导
   - **缺失的**：从违规日志提取典型模式，编写 ❌/✅ 对比示例，加入 coding-guidelines.md
   - **已有但仍高频的**：说明规范已存在但未生效，在 commit message 中记录，不重复添加
   - coding-guidelines.md 更新后，posttooluse hook 会自动读取并执行实时检查
   - 这一步是闭环的关键——gate 拦截是治标，生成指导是治本

5. **存量违规清理**（自动，每次 review 清一批）：
   - 从 `bash scripts/test-governance-gate.sh trend` 的输出中取触发次数最多的 1 条规则
   - 定位该规则对应的所有存量违规文件和位置
   - 按 coding-guidelines.md 中的 ✅ 正确写法批量修复（如果 guidelines 中没有，先补 guidelines 再修）
   - 修复后跑该模块的单元测试验证无回归
   - 一次只清 1 条规则（避免改动过大），下次 review 清第 2 条
   - 如果 top 1 规则的存量已清零，取 top 2，依此类推
   - 全部高频规则（≥10 次）存量清零后，此步骤自动跳过

6. **识别架构约束 → 建议写入 CLAUDE.md**（自动）：
   - 从已验证 bug 中识别**跨模块/跨端/跨文件的架构级约束**
   - 判断标准：该约束无法通过单文件 hook 或 gate regex 可靠检测，必须依赖 Claude 写代码时的主动意识
   - 典型模式：修改 A 文件时必须同步 B 文件、共享状态的访问顺序、API 版本兼容规则等
   - 如有发现，在阶段 C 的确认清单中**单独列出**，格式为一句话约束 + 详情指向 coding-guidelines.md
   - **不自动写入 CLAUDE.md**，由用户确认后手动或由主会话写入
   - 已有类似约束在 CLAUDE.md 中的，不重复建议

subagent 内部：写 gate 规则 + 写 helper → 跑 preflight 验证 → 趋势分析 + 源头治理 → 存量违规清理（top 1 规则）→ 更新 test-governance/ → commit + push

#### 阶段 C：输出验证报告 + 等待用户确认合并

阶段 A worktree 完成后，主会话汇总验证结果，按以下格式输出：

```
## 验证结果

| # | 标记 | 模块 | bug | 修复 |
| ✅ / ❌ / ⚠️ |

### 建议写入 CLAUDE.md 的架构约束（如有）
| # | 约束（一句话） | 来源 bug | 详情 |
（格式："修改 X 时必须同步 Y。详见 coding-guidelines.md。"）

### 幻觉记录（❌）
| # | 声称的 bug | 实际情况 |
```

末尾固定：**"以上 N 个 ✅ 已验证修复在 worktree 分支中，确认后我合并到 main 并 push。"**
如有架构约束建议，追加：**"另有 N 条架构约束建议写入 CLAUDE.md，确认后我帮你加。"**

暂停，等用户确认。

用户确认后：
1. 合并已确认的 worktree 分支到 main + push
2. 清理 worktree
3. 执行阶段 B 更新测试基础设施

## --deep：3 轮发现 + 1 轮红绿验证+修复 + 1 轮交叉检验

**前 3 轮是只读发现，第 4 轮用红绿测试做机械验证+修复（对抗幻觉+消除重复劳动），第 5 轮做影响范围扩展。**

**核心改进：R4 红绿验证与修复合并为一步，按模块拆 agent，验证通过的直接修复提交。不再有独立的阶段 A。**

```
第 1 轮：标准五类模式扫描（A 资源泄漏 / B 标记锁 / C 错误吞没 / D 并发安全 / E 安全边界）
    ↓ 收集发现，假设这些问题已修
第 2 轮：修复后会暴露什么新问题？（错误不再被吞 → 暴露并发问题等）
    ↓
第 3 轮：更深层——架构问题、错误传播链路、状态机非法转换、测试体系自身盲区
    ↓ 汇总去重
第 4 轮（红绿验证+修复 — 强制，不可跳过）：
    按模块拆 opus worktree agent，对前 3 轮每个发现执行：
    a) 先读源码确认 bug 是否存在
    b) 写测试精确复现 bug → 运行 → 必须失败（红）
    c) 写 fix → 运行测试 → 必须通过（绿）
    d) 运行该模块已有测试 → 必须无回归
    e) ✅ 的保留修复，❌ 的撤销测试和修复

    判定规则（严格，无中间态）：
    - 红绿都通过 + 无回归 → ✅ 已验证，保留修复
    - 步骤 b 测试直接通过（"bug"不存在）→ ❌ 幻觉，撤销测试和修复
    - 步骤 b 失败但原因与声称 bug 不符 → ❌ 幻觉，撤销
    - 步骤 d fix 后测试仍失败 → fix 有误，重写 fix 或丢弃
    - 步骤 d 已有测试回归 → fix 引入新问题，必须修复回归或丢弃该发现
    - 环境限制无法运行测试（如缺 Xcode）→ ⚠️ 未验证，标注原因，保留修复但标记

    全部完成后：在 worktree 内 commit（只包含 ✅ 和 ⚠️ 的修复，❌ 的全部撤销）
    ⚠️ 不合并到 main，不 push。worktree 分支保留，等用户确认后由主会话合并。
    ↓
第 5 轮（交叉检验）：只针对第 4 轮 ✅ 已验证的问题，检查跨模块影响范围
    a) Explore agent 扫描：同类模式是否在其他模块存在？修复是否影响兼容性/部署顺序？
    b) 扫描结果中的"其他模块同类 bug"必须走红绿验证+修复（复用第 4 轮流程，按模块拆 opus worktree）
       - 红绿通过 → 🔗✅ 已验证扩展
       - 红绿失败（bug 不存在）→ 丢弃
    c) R5 worktree 同样只 commit 不合并，等用户确认
    d) 兼容性/部署顺序影响无法用测试验证的，标注为 🔗⚠️ 并说明原因
    ↓
按盲区组织 → 一次性输出确认清单 → 等用户确认
    ↓
主会话合并已确认的 worktree 分支到 main + push + 清理 worktree
```

**确认清单两档标记（⚠️ 仅用于环境限制，不作为幻觉的逃生口）：**

| 标记 | 含义 | 用户操作建议 |
|------|------|-------------|
| ✅ 已验证 | 红绿测试 + 无回归，三项全过 | 确认后执行 |
| ⚠️ 未验证 | 环境限制无法跑测试（须标注原因） | 用户自行判断 |
| 🔗✅ 已验证扩展 | 跨模块同类 bug，已通过红绿验证 | 和对应 ✅ 一起处理 |
| 🔗⚠️ 未验证扩展 | 兼容性/部署影响，无法用测试验证（须标注原因） | 用户自行判断 |

**幻觉发现（第 4 轮 ❌）不出现在确认清单中，但在报告末尾单独列出供参考。**

**规则：**
- 第 1-3 轮：每轮用独立 Explore agent（prompt 含前几轮发现摘要，避免重复）
- 第 4 轮：**按模块拆 opus worktree agent**（每模块一个 agent 批量处理该模块所有发现），且该 agent 不得复用发现该 bug 的 agent（降低确认偏差）
- 第 4 轮 agent 的 prompt 必须包含："如果测试直接通过，说明 bug 不存在，标记为幻觉并丢弃。不要修改测试让它强行失败。"
- 第 4 轮 agent 在 worktree 内 commit，**不合并 main、不 push**，等用户确认后由主会话合并
- 新测试的维度覆盖登记到 `test-governance/dimension-coverage.yaml`
- 第 5 轮：Explore agent 扫描跨模块影响，但扫描出的"同类 bug"必须走红绿验证+修复才能进确认清单
- 某轮新发现 = 0 → 提前终止（仅适用于第 1-3 轮）
- 多模块时每轮内各模块 agent 并行

用户确认后：
1. 主会话合并已确认的 R4/R5 worktree 分支到 main + push
2. 丢弃未确认的 worktree 分支
3. 清理所有 worktree
4. 执行阶段 B 更新测试基础设施（与普通模式相同）

用户可以只确认 ✅ 项，⚠️ 项留待下轮。

### 出报告前自检（强制，不可跳过）

在输出最终报告之前，逐项检查以下清单。**任何未完成项必须补完后才能出报告**：

**普通模式：**
- [ ] 阶段 A：所有 ✅ bug 已通过红绿验证 + 已在 worktree commit
- [ ] 阶段 C：验证报告已输出，用户已确认，worktree 已合并 + push
- [ ] Phase B-1：新 bug 模式已转化为 gate 规则（preflight 通过）
- [ ] Phase B-2：新测试 helper 已创建且被至少一个测试使用
- [ ] Phase B-3：test-governance/ 已更新（infrastructure.md + coding-guidelines.md + dimension-coverage.yaml）
- [ ] Phase B-4：`trend` 已重新执行，≥10 次高频规则已检查 coding-guidelines.md 覆盖情况，缺失的已补上
- [ ] Phase B-5：top 1 高频规则的存量违规已批量清理 + 单元测试无回归（全部清零则跳过）
- [ ] Phase B-6：已检查是否有架构约束需建议写入 CLAUDE.md，如有已列入阶段 C 报告
- [ ] 所有改动已 commit + push
- [ ] worktree 已清理

**--deep 模式（在普通模式基础上追加）：**
- [ ] R4：所有 ✅ bug 已修复 + 回归测试已通过 + 已在 worktree commit
- [ ] R5：跨模块扩展已验证+修复 + 已在 worktree commit
- [ ] 用户确认后合并 worktree + push + 清理

最终报告：
```
## Review 报告

### 测试体系强化
| 模块 | 新增基础设施 | 能自动抓住的问题类型 | 验证结果 |

### 基础设施更新（Phase B）
| 类型 | 新增项 | 说明 |
（包含：新 gate 规则、新测试 helper、test-governance/ 更新项）

### 附带修复的 bug
| # | 标记 | 模块 | bug | 修复 |

### 验证统计
| 发现数 | ✅ 已验证 | ❌ 幻觉 | ⚠️ 未验证 |
（--deep 追加：| 🔗 扩展 |）

### 架构约束建议（如有）
| # | 约束 | 来源 |

### 幻觉记录
| # | 声称的 bug | 实际情况 |
```

## 效率约束

- 分析用 Explore agent 并行，不在主会话逐文件读
- subagent 只跑单文件测试，不跑全量
- Bash 输出 `| tail -N` 截断
- 单个 subagent 修复项 ≤ 5
- 不同语言拆不同 subagent
- worktree 合并后立即清理，不留残余

### subagent 模型分配（必须遵守）

| 阶段 | agent 类型 | model 参数 | 理由 |
|------|-----------|-----------|------|
| 普通模式：分析 | Explore agent | `model: "sonnet"` | 代码扫描是机械性工作，sonnet 快 3-4 倍 |
| 普通模式：阶段 A 红绿验证+修复 | worktree agent | `model: "opus"` | 判断 bug 真实性 + 红绿多步骤需要准确性 |
| --deep：R1-R3 分析 | Explore agent | `model: "sonnet"` | 同上 |
| --deep：R4 验证+修复 | worktree agent | `model: "opus"` | 同上 |
| --deep：R5 交叉扫描 | Explore agent | `model: "sonnet"` | 同上 |
| --deep：R5 交叉验证+修复 | worktree agent | `model: "opus"` | 同上 |
| Phase B 基础设施 | worktree agent | `model: "sonnet"` | 写 gate 规则+更新文档，sonnet 够用 |

主会话保持 opus 做决策、去重、合并 worktree。
