## Installation

`install.py` symlinks shared config items from this repo into `$CLAUDE_CONFIG_DIR`. Edits in this repo are immediately reflected in the target — nothing is copied.

### 1. Set `CLAUDE_CONFIG_DIR`

The installer reads the target from `$CLAUDE_CONFIG_DIR`. If unset, it falls back to `~/.claude` with a warning.

### 2. Run the installer

```bash
uv run python install.py
```

Re-running is safe: the script is idempotent. New files are picked up automatically, and symlinks whose source no longer exists are cleaned up. If a target path already exists as a regular file or directory, install aborts and asks you to resolve manually.

## What gets installed

Each entry in `ITEMS` (defined in `install.py`) is symlinked individually from this repo into `$CLAUDE_CONFIG_DIR`:

| Item | Purpose |
|------|---------|
| `CLAUDE.md` | Repo-wide guidance loaded into Claude's context |
| `settings.json` | Claude Code settings (theme, permissions, hooks) |
| `bin/` | Hook scripts and other executables referenced from `settings.json` |

The repo as a whole is **not** symlinked — only these specific items — so Claude Code's runtime state (`projects/`, `todos/`, …) under `$CLAUDE_CONFIG_DIR` is untouched.
