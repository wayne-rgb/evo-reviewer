# 前置：模块枚举 + 就绪检查

## Bootstrap（首次运行自动初始化）

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

2. 如果项目没有 `scripts/test-governance-gate.sh`，按 gate 骨架模板生成。

3. 追加测试原则到项目 CLAUDE.md：
   - 测试运行策略（如果尚未包含"测试运行策略"章节）
   - 维度定义和适用性表（如果尚未包含"测试编写的 6 个维度"章节）
   - CI 策略说明

4. 配置 post-push CI hook：
   - 先检查项目 .claude/settings.json 中是否已有功能等价的 post-push hook，如果有则跳过
   - 如果没有，在 .claude/settings.json 中添加 post-push hook 配置
   - 创建 .claude/hooks/post-push-signal.sh

5. 检查 .gitignore 是否包含 `test-governance/gate-violations.log`，如果没有则追加。

Bootstrap 产物纳入确认清单，和 review 发现一起确认。

## test-governance 文件填充策略

bootstrap 创建的文件初始为空模板，由阶段 B 逐步填充。以下是每个文件的结构和填充规则：

### infrastructure.md（测试基础设施注册表）

结构：按模块分组的表格，每行记录一项基础设施。

| 列 | 说明 |
|----|------|
| 基础设施名称 | 简短描述（如"全局 setInterval 泄漏检测"） |
| 文件路径 | 相对路径 |
| 覆盖场景 | 这个基础设施能自动抓住什么类型的 bug |
| 来源 | 哪次 /review 引入的（commit hash 或日期） |

填充规则：
- Phase B 每新增一个 gate 规则、test helper 或回归测试，必须登记到此表
- 不登记 = 不存在（后续 review 会重复建设同类基础设施）

### coding-guidelines.md（编码规范）

结构：按语言分组，每条规范包含 ❌ 错误写法和 ✅ 正确写法的对比示例。

填充规则：
- gate trend 分析中 ≥10 次的高频违规规则，自动提取为编码规范
- 每条规范必须有具体的代码示例（不是抽象描述）
- 规范和 posttooluse hook 的规则对应，hook 机械执行规范

### p0-cases.tsv（P0 场景矩阵）

结构：TSV 格式，每行一个关键场景。

| 列 | 说明 |
|----|------|
| 场景 ID | 唯一标识（如 PAIRING_KEY_NIL_CLEARS_LOCAL） |
| 场景描述 | 用户视角的一句话描述 |
| 验证关键词 | gate preflight 用 grep 检查的关键词 |
| 验证范围 | 在哪些目录下搜索关键词 |

填充规则：
- 发现的涉及核心用户链路的 bug，如果回归会导致产品不可用，加入 P0 矩阵
- 不是所有 bug 都是 P0，只有"用户完全无法使用某个核心功能"才算

### dimension-coverage.yaml（测试维度映射）

结构：YAML，按模块 → 测试文件 → 维度编号列表。

填充规则：
- Phase B 每次新增或修改测试文件时，更新对应条目
- 维度编号 1-6 对应：正常路径/副作用清理/并发安全/错误恢复/安全边界/故障后可用

### config.yaml（模块配置）

填充规则：
- bootstrap 时自动扫描项目结构生成
- 发现新模块时更新
- 用户手动调整测试命令后应同步更新

## 1. 枚举模块
扫描项目根目录（package.json / go.mod / *.xcodeproj / pyproject.toml / setup.py / setup.cfg / requirements.txt / Cargo.toml / build.gradle），输出：
```
| 模块 | 语言 | 源文件数 | 测试文件数 | 基础设施 |
```
单模块项目跳过。

## 2. 确定范围

由调用方指定：
- `/review`（无参数）：`git diff --name-only HEAD~5` 归属到模块
- `/review dir/`：指定目录
- `/deep`（无参数）：所有模块（>5 个时取 top 5）
- `/deep dir/`：指定模块

## 3. 就绪检查
对每个模块确认：能不能跑单文件测试？有没有测试？

- **缺测试信息** → 推断测试命令，补入 test-governance/config.yaml，和 review 发现一起确认
- **零测试** → 该模块只建测试骨架，不扫 bug
- **环境跑不了**（如缺 Xcode）→ 扫 bug 但跳过测试执行，标注 ⚠️
- **无 gate.sh** → 首次运行时按 gate 骨架模板生成，纳入确认清单

## 4. 违规趋势读取（进化闭环）
如果项目有 `scripts/test-governance-gate.sh`，执行 `bash scripts/test-governance-gate.sh trend`。
- **高频规则（≥10 次）**→ 本轮分析重点关注该类问题，并在确认清单中建议将对应模式加入 test-governance/coding-guidelines.md
- **高频文件** → 优先分析这些文件
- **无 gate.sh 或无日志** → 跳过，不阻塞
