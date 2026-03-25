# 前置：模块枚举 + 就绪检查

## Bootstrap（首次运行自动初始化）

如果项目没有 `test-governance/` 目录，按以下步骤初始化：

1. 创建 test-governance/ 目录及核心文件：
   - `config.yaml` — 扫描项目生成模块配置（语言、测试命令、helper 路径）
   - `infrastructure.md` — 空的基础设施注册表模板
   - `coding-guidelines.md` — 空的编码规范模板
   - `dimension-coverage.yaml` — 空的维度映射

config.yaml 格式：
```yaml
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

2. 如果没有 `scripts/test-governance-gate.sh`，按 gate 骨架模板生成（@${CLAUDE_PLUGIN_ROOT}/skills/review/references/gate-template.sh）。

3. 追加测试原则到项目 CLAUDE.md（如果尚未包含）：
   - 测试运行策略（@${CLAUDE_PLUGIN_ROOT}/skills/review/references/testing-strategy.md）
   - 6 维度定义（@${CLAUDE_PLUGIN_ROOT}/skills/review/references/dimensions.md）
   - CI 策略说明

4. 检查 .gitignore 是否包含 `test-governance/gate-violations.log`。

5. **跨模块通信拓扑扫描**（多模块项目自动执行，单模块跳过）：
   - 搜索通信模式（WebSocket、HTTP、gRPC 等），识别模块间通信关系
   - 识别共享类型定义和状态机
   - 写入 config.yaml 的 `cross_module` 段，在 gate.sh 生成初始跨模块规则

Bootstrap 产物纳入确认清单，和 review 发现一起确认。

## 确定范围

- `/review`（无参数）：`git diff --name-only HEAD~5` 归属到模块
- `/review dir/`：指定目录
- `/review *`：全模块

## 就绪检查

对每个模块确认：
- **缺测试信息** → 推断测试命令，补入 config.yaml
- **零测试** → 该模块只建测试骨架，不扫 bug
- **环境跑不了** → 扫 bug 但跳过测试执行，标注 ⚠️
- **无 gate.sh** → 按骨架模板生成
