# CI 验证执行流程

## subagent prompt 模板

git push 成功后，Claude 应开 background subagent 执行以下流程：

1. `git diff --name-only $(git rev-parse @{push} 2>/dev/null || echo HEAD~1) HEAD` 获取改动文件（优先使用 @{push} 即 push 前的远程 HEAD，如果没有上游分支则回退到 HEAD~1）
2. 读取 `test-governance/config.yaml` 确定模块
3. `bash scripts/test-governance-gate.sh preflight`（截取最后 20 行）
4. 按 config.yaml 中每个有改动的模块执行对应的测试命令
5. 所有输出用 tail 截断
6. 汇报：哪些通过，哪些失败

## config.yaml 模块配置格式

```yaml
modules:
  module-name:
    language: typescript|go|swift|python
    src_dir: "src/"
    test_command: "npx vitest run"
    unit_command: "npm run test:unit"
    cross_command: "npm run test:cross"
    lint_command: "npm run lint"
    typecheck_command: "npx tsc --noEmit"
    test_dir: "src/__tests__"
```

CI subagent 读取 config.yaml，对每个有改动的模块执行 lint_command → typecheck_command → unit_command。跨模块改动额外执行 cross_command。

### 多语言 config.yaml 示例

**TypeScript（Node.js）**
```yaml
modules:
  macbook-agent:
    language: typescript
    src_dir: "src/"
    test_command: "npx vitest run"
    unit_command: "npm run test:unit"
    cross_command: "npm run test:cross"
    lint_command: "npm run lint"
    typecheck_command: "npx tsc --noEmit"
    test_dir: "src/__tests__"
    helper_dir: "src/__tests__/helpers"
```

**Go**
```yaml
modules:
  voice-tunnel:
    language: go
    src_dir: "."
    test_command: "go test -race ./..."
    unit_command: "go test -race ./pkg/..."
    cross_command: "go test -race ./test/..."
    lint_command: "golangci-lint run"
    typecheck_command: "go vet ./..."
    test_dir: "."
    helper_dir: "test/helpers"
```

**Swift（Xcode 项目）**
```yaml
modules:
  macos-app:
    language: swift
    src_dir: "VoiceToGo/"
    test_command: "xcodebuild test -project VoiceToGo.xcodeproj -scheme VoiceToGo -destination 'platform=macOS'"
    unit_command: "xcodebuild test -project VoiceToGo.xcodeproj -scheme VoiceToGo -destination 'platform=macOS' -enableThreadSanitizer YES"
    lint_command: "swiftlint"
    test_dir: "VoiceToGoTests/"
```

**Python**
```yaml
modules:
  backend:
    language: python
    src_dir: "src/"
    test_command: "pytest"
    unit_command: "pytest tests/unit/"
    cross_command: "pytest tests/integration/"
    lint_command: "ruff check ."
    typecheck_command: "mypy src/"
    test_dir: "tests/"
    helper_dir: "tests/helpers/"
```

## 改动范围判断逻辑

1. 获取改动文件列表
2. 对每个文件，匹配 config.yaml 中模块的 src_dir 前缀，归属到模块
3. 无法归属的文件（根目录配置等）不触发模块测试，只跑治理门禁
4. 纯文档/配置改动（所有文件扩展名为 .md/.yaml/.json/.toml/.txt/.cfg）→ 只跑门禁

## 失败处理策略

| 失败类型 | 处理方式 |
|----------|----------|
| 门禁失败 | 汇报具体违规项，不自动修复 |
| lint 失败 | 如果是自动可修复的（--fix），自动修复 + commit + push |
| 类型检查失败 | 汇报错误位置和原因 |
| 单元测试失败 | 分析失败原因，汇报到主对话 |
| 集成测试失败 | 分析失败原因，汇报到主对话 |
