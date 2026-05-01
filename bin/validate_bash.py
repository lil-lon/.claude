#!/usr/bin/env python3
"""PreToolUse hook for Bash: block compound/dangerous shell constructs."""

from __future__ import annotations

import json
import re
import sys

# Blocks compound commands and shell features that can chain or smuggle
# additional commands. `|` also catches `||`; `>` also catches `>>` and `>&`.
BLOCKED_PATTERN = re.compile(r"(&&|\||;|\$\(|`|>)")
MESSAGE = "Error: Commands containing &&, |, ;, $(, `, or > are not allowed."


def main() -> None:
    payload = json.load(sys.stdin)

    command = payload.get("tool_input", {}).get("command", "")
    if BLOCKED_PATTERN.search(command):
        print(MESSAGE, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
