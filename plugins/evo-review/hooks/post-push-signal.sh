#!/bin/bash
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# 精确匹配 git push 命令（排除 dry-run、delete、echo 等）
# 必须以 git push 开头或在 && / ; 后跟 git push
if ! echo "$COMMAND" | grep -qE '(^|&&\s*|;\s*)git\s+push(\s|$)'; then
  exit 0
fi

# 排除 dry-run 和 delete
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--(dry-run|delete)'; then
  exit 0
fi

# PostToolUse 本身就保证了工具成功执行，无需额外检查 exit_code
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "✅ [CI-SIGNAL] git push 成功。请立即开一个 background subagent 执行 CI 验证（按项目 test-governance/config.yaml 的模块配置）。"
  }
}
EOF
