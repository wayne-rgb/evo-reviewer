#!/usr/bin/env python3
"""
Evo Review PostToolUse Hook

在 Edit/Write 工具调用后，对被修改的文件做轻量级静态检查，
发现违规时返回 systemMessage 让 Claude 修复。
"""

import json
import os
import re
import sys


# ==================== 内置规则 ====================

ts_rules = [
    {
        "id": "catch-swallow",
        "pattern": r"\.catch\(\s*\([^)]*\)\s*=>\s*\{\s*console\.(log|error)\([^)]*\);\s*\}\s*\)",
        "message": ".catch() 仅 console.log 属于错误吞没，需要标注 // @error-ignored: 原因 或重新抛出",
    },
    {
        "id": "empty-catch",
        "pattern": r"catch\s*\([^)]*\)\s*\{\s*\}",
        "message": "空 catch 块，需要标注 // @error-ignored: 原因 或处理错误",
    },
    {
        "id": "callback-unprotected",
        "pattern": r"this\.\w+Callback\s*\(",
        "negative_pattern": r"try\s*\{[^}]*this\.\w+Callback",
        "message": "this.xxxCallback() 调用应包裹在 try-catch 中，防止回调异常中断主流程",
    },
    {
        "id": "fs-readfile-no-size",
        "pattern": r"fs\.readFile\s*\(",
        "negative_pattern": r"fs\.stat|stats\.size|MAX_FILE_SIZE",
        "message": "fs.readFile 前应检查文件大小，防止读入超大文件",
    },
    {
        "id": "url-string-interpolation",
        "pattern": r"`[^`]*\$\{[^}]+\}[^`]*\?[^`]*\$\{[^}]+\}[^`]*`",
        "message": "URL 含 query 参数时应使用 URL/URLSearchParams 构建，避免字符串插值",
    },
]

go_rules = [
    {
        "id": "set-deadline-ignored",
        "pattern": r"conn\.Set(?:Read|Write)?Deadline\(",
        "negative_pattern": r"if\s+err\s*:=\s*conn\.Set(?:Read|Write)?Deadline",
        "message": "SetDeadline/SetReadDeadline/SetWriteDeadline 的返回值需要检查",
    },
    {
        "id": "header-no-trimspace",
        "pattern": r"r\.Header\.Get\(",
        "negative_pattern": r"strings\.TrimSpace\(r\.Header\.Get",
        "message": "HTTP Header.Get() 值应使用 strings.TrimSpace() 去除前后空格",
    },
    {
        "id": "write-no-deadline",
        "pattern": r"conn\.WriteMessage\(",
        "negative_pattern": r"SetWriteDeadline",
        "message": "WebSocket 写操作前应设置 WriteDeadline",
    },
]

swift_rules = [
    {
        "id": "observer-token-discard",
        "pattern": r"NotificationCenter\.default\.addObserver\(forName:",
        "negative_pattern": r"(let|var)\s+\w+\s*=\s*NotificationCenter",
        "message": "addObserver(forName:) 的返回 token 不应丢弃，需要存储以便后续 removeObserver",
    },
]

python_rules = [
    {
        "id": "bare-except",
        "pattern": r"except\s*:",
        "message": "避免 bare except，应指定具体异常类型",
    },
]

RULES_BY_EXT = {
    ".ts": ts_rules,
    ".tsx": ts_rules,
    ".js": ts_rules,
    ".jsx": ts_rules,
    ".go": go_rules,
    ".swift": swift_rules,
    ".py": python_rules,
}


# ==================== 项目自定义规则加载 ====================

def load_project_rules(ext: str) -> list:
    """从当前工作目录下的 test-governance/hook-rules.json 加载额外规则。"""
    rules_path = os.path.join(os.getcwd(), "test-governance", "hook-rules.json")
    if not os.path.exists(rules_path):
        return []
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 格式：{ ".ts": [...rules], ".go": [...rules], ... }
        return data.get(ext, [])
    except Exception:
        return []


# ==================== 检查逻辑 ====================

def check_file(file_path: str, content: str, rules: list) -> list:
    """对文件内容执行规则检查，返回违规列表。"""
    violations = []
    for rule in rules:
        pattern = rule.get("pattern", "")
        negative_pattern = rule.get("negative_pattern", "")

        # 检查主 pattern 是否在文件中匹配
        try:
            if not re.search(pattern, content, re.DOTALL):
                continue
        except re.error:
            continue

        # 如果有 negative_pattern，检查它是否也存在于文件中（粗略的整文件检查）
        if negative_pattern:
            try:
                if re.search(negative_pattern, content, re.DOTALL):
                    # 找到了 negative_pattern，说明可能已经有保护，跳过此规则
                    continue
            except re.error:
                pass

        violations.append({
            "id": rule["id"],
            "message": rule["message"],
        })

    return violations


# ==================== 主入口 ====================

def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        print("{}")
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # 只处理 Edit 和 Write 工具
    if tool_name not in ("Edit", "Write"):
        print("{}")
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print("{}")
        sys.exit(0)

    # 根据扩展名选择规则集
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    builtin_rules = RULES_BY_EXT.get(ext)
    if builtin_rules is None:
        print("{}")
        sys.exit(0)

    # 加载项目自定义规则
    project_rules = load_project_rules(ext)
    rules = builtin_rules + project_rules

    # 读取文件内容
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        print("{}")
        sys.exit(0)

    # 执行检查
    violations = check_file(file_path, content, rules)

    if not violations:
        print("{}")
        sys.exit(0)

    # 构建 systemMessage
    lines = ["⚠️ **Evo Review 检测到以下编码规范违规**：\n"]
    for i, v in enumerate(violations, 1):
        lines.append(f"{i}. [{v['id']}] {v['message']}")
    lines.append("\n请修复后继续。如果是有意为之，请标注原因。")

    result = {"systemMessage": "\n".join(lines)}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("{}")
        sys.exit(0)
