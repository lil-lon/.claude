#!/usr/bin/env python3
"""PreToolUse hook for Bash: block compound/dangerous shell constructs."""

from __future__ import annotations

import json
import re
import sys

# Blocks chain operators, redirects, and shell-expansion vectors:
#   && (AND), & (background), ; (separator),
#   > (any output redirect), < (any input redirect, including
#   here-string/here-doc/process substitution),
#   | (pipe), ` (backtick subst),
#   $( (cmd subst), $' (ANSI-C quoting), $" (locale-aware string),
#   ${ (parameter expansion), $[ (legacy arithmetic),
#   newline (multi-line composition).
# Plain $VAR (variable reference without an expansion sigil) is allowed.
BLOCKED_PATTERN = re.compile(r"&&|&|;|>|<|\||`|\$[(\'\"{[]|\n")
# Stripped from the command before the block check so the Claude Code
# co-author trailer survives the < and > rules. Anchored to a closing
# quote at end-of-string so the substitution cannot consume an angle
# bracket that the shell would interpret as a redirect (e.g.
# `cmd <noreply@anthropic.com> out`). Requires the trailer to be in
# the LAST -m argument of git commit.
COAUTHOR_TRAILER = re.compile(r"<noreply@anthropic\.com>(?=['\"]\Z)")
MESSAGE = (
    "Error: Commands containing &&, &, ;, >, <, |, `, "
    "$(, $', $\", ${, $[, or newlines are not allowed."
)


def main() -> None:
    payload = json.load(sys.stdin)

    command = payload.get("tool_input", {}).get("command", "")
    if command.startswith("git commit "):
        command = COAUTHOR_TRAILER.sub("", command)
    if BLOCKED_PATTERN.search(command):
        print(MESSAGE, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
