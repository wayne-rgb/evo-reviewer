#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // "0"')

[[ "$COMMAND" == *"git push"* ]] || exit 0
[[ "$EXIT_CODE" == "0" ]] || exit 0

echo "[post-push] git push 成功，请开 subagent 后台执行 CI 验证（按项目 test-governance/config.yaml 的模块配置）"
