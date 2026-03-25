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

2. 如果没有 `scripts/test-governance-gate.sh`，读取 [gate-template.sh](gate-template.sh) 按骨架模板生成。

3. 追加测试原则到项目 CLAUDE.md（如果尚未包含）：
   - 测试运行策略（读取 [testing-strategy.md](testing-strategy.md)）
   - 6 维度定义（读取 [dimensions.md](dimensions.md)）
   - CI 策略说明

4. 检查 .gitignore 是否包含 `test-governance/gate-violations.log`。

5. **跨模块通信拓扑扫描**（多模块项目自动执行，单模块跳过）：
   - 读取项目 CLAUDE.md 的通信拓扑描述（搜索 ASCII 图、"通信"/"拓扑"/"架构"关键词）
   - 搜索通信模式（WebSocket、HTTP、gRPC、消息队列等），识别模块间通信关系
   - 识别共享类型定义文件（搜索 types/、models/、Message、Codable 等关键词）
   - 识别状态机定义文件（搜索 state-machine、StateMachine、状态转换等）
   - 如果存在 `test-governance/p0-cases.tsv`，读取并按功能域聚合为初始业务流
   - 写入 config.yaml 的 `cross_module` 段：
     ```yaml
     cross_module:
       topology_source: "CLAUDE.md 通信拓扑段"
       shared_types:
         - path/to/types/index.ts
         - path/to/Message.swift
       state_machines:
         - path/to/state-machine.ts
         - path/to/TaskViewModel.swift
       communication_pairs:
         - { from: "module-a", to: "module-b", protocol: "WebSocket", port: 8765 }
         - { from: "module-c", to: "module-b", protocol: "HTTP", port: 13284 }
       business_flows:
         - name: "端到端业务流名称"
           modules: [module-a, module-b, module-c]
           entry_files: ["module-a/src/handler.ts"]
           boundary_files: ["module-a/src/types/index.ts", "module-b/Sources/Message.swift"]
           p0_cases: [CASE_ID_1, CASE_ID_2]
     ```
   - 在 gate.sh 生成初始跨模块规则

Bootstrap 产物纳入确认清单，和 review 发现一起确认。

## 确定范围

- `/review`（无参数）：从 config.yaml 的 business_flows 筛选近期改动涉及的业务流
- `/review dir/`：找所有经过该目录所属模块的业务流
- `/review *`：全部业务流

## 就绪检查

对每个模块确认：
- **缺测试信息** → 推断测试命令，补入 config.yaml
- **零测试** → 该模块只建测试骨架，不扫 bug
- **环境跑不了** → 扫 bug 但跳过测试执行，标注 ⚠️
- **无 gate.sh** → 按骨架模板生成
