#!/bin/bash
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# 只匹配 git push 命令
[[ "$COMMAND" == *"git push"* ]] || exit 0

# PostToolUse 本身就保证了工具成功执行，无需额外检查 exit_code
# PostToolUse hook 必须用 hookSpecificOutput.additionalContext 才能注入 Claude 上下文
# 纯文本和顶层 systemMessage 在 PostToolUse 中会被忽略
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "✅ [CI-SIGNAL] git push 成功。请立即开一个 background subagent 执行 CI 验证（按项目 test-governance/config.yaml 的模块配置）。"
  }
}
EOF
