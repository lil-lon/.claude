---
name: codex-review
description: |
  Review staged changes with Codex by piping `git diff --cached` to
  `codex exec` and asking for P1-P4 labeled findings. Use when the user
  asks for a Codex-specific review on staged work ("codex review",
  "review with codex"). Do NOT auto-invoke for generic "review this"
  requests — those belong to the built-in `/review` skill.
allowed-tools:
  - Bash
---

Run the review script that lives next to this SKILL.md, from the user's
current working directory (so `git diff --cached` operates on their
repo):

```
bash "$CLAUDE_CONFIG_DIR/skills/codex-review/review.sh"
```

The script aborts with exit 1 when no staged changes exist — surface
that message and stop.

Print the script's stdout verbatim. Do not paraphrase, trim, or add a
summary on top.

## Sandbox

The Claude Code sandbox blocks `codex exec` from accessing its session,
so run this script unsandboxed. It is safe because the script itself
passes `--sandbox read-only` to `codex exec`.

TODO: narrow the `sandbox.excludedCommands` glob in `settings.json` so
that this wrapper script is matched and the explicit unsandbox flag is
no longer needed.
