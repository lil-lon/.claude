---
name: agent-worktree
description: Spawn an isolated Claude Code sub-task in a fresh git worktree, split into a new tmux pane next to the caller, then clean up when done. Use this whenever the user wants to delegate a small, self-contained side task without disturbing the current session — e.g. they say "do this in a worktree", "spawn a sub-agent", "start a side task", "run this in the background", or ask for parallel work like "fix this typo while you keep refactoring". Always use this skill for those requests instead of editing files directly when the user's intent is to fork off a parallel job.
---

# agent-worktree

Dispatch a side task to a separate git worktree running its own Claude Code instance in a new tmux pane next to the caller, then tear everything down when the task finishes.

## When to use

Trigger this skill when the user wants to fork off work into a parallel, isolated workspace. Common phrasings:

- "spawn a worktree for X"
- "do X in a side branch / sub-agent / background"
- "start a parallel task"
- "/agent-worktree ..." or similar slash-style invocation
- The user describes a task that is clearly independent from what the current session is doing

Do **not** use this skill when:

- The task touches the same files the current session is actively editing (merge conflicts will follow).
- The task needs live context from the current session that hasn't been written down.
- The user just wants a quick edit in-place.

## Prerequisites

- `tmux` on PATH
- The caller must be running inside a tmux session (`$TMUX_PANE` set). The script will refuse to spawn otherwise.
- `git` 2.5+
- `claude` CLI on PATH
- Current working directory is inside a git repository

## Workflow

### 1. Pick a Conventional Commit type and a name

From the user's request, pick:

- **type**: one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`, `revert` (Conventional Commits).
- **name**: short kebab-case description.

Examples:

| User request                                  | type       | name             |
|-----------------------------------------------|------------|------------------|
| "Fix the typo in README"                      | `docs`     | `readme-typo`    |
| "Add a unit test for the parser"              | `test`     | `parser`         |
| "Bump the lodash version"                     | `chore`    | `bump-lodash`    |
| "Refactor the auth module into smaller files" | `refactor` | `auth-split`     |
| "Add a new login endpoint"                    | `feat`     | `login-endpoint` |

The resulting branch will be `<type>/<name>` (e.g. `docs/readme-typo`), matching Conventional Commits convention.

Briefly confirm the type, name, and prompt with the user before spawning, unless they have explicitly said "just do it".

### 2. Spawn the sub-agent

The script is invoked directly via its shebang (same pattern as `bin/validate_bash.py`):

```bash
$CLAUDE_CONFIG_DIR/skills/agent-worktree/agent_worktree.py spawn <type> <name> "<prompt>"
```

The `<prompt>` should be self-contained — include any file paths, requirements, and acceptance criteria explicitly. The sub-agent cannot see the current session's context.

The script prints JSON with the new pane's `pane_id` (e.g. `%47`) and a focus hint. The pane is opened to the right of the caller's pane with focus left on the caller. Tell the user they can switch to it with `Ctrl-b o` (cycle panes) or `Ctrl-b →` (focus right).

### 3. Monitor (optional)

```bash
$CLAUDE_CONFIG_DIR/skills/agent-worktree/agent_worktree.py status <name>
```

Reports whether the agent's tmux pane is still alive, the last commit on the branch, and whether the working tree is dirty.

### 4. Clean up

```bash
$CLAUDE_CONFIG_DIR/skills/agent-worktree/agent_worktree.py cleanup <name>
```

Kills the agent's tmux pane, removes the worktree, and deletes the `<type>/<name>` branch.

The script refuses to clean up when the worktree is dirty or the branch has commits that are neither merged into `main` nor pushed — it prints what would be lost and exits non-zero. Merge or push first, then re-run. Pass `--force` only when you genuinely want to discard the work.

## What the script does under the hood

For `spawn docs readme-typo "..."` (called from a tmux pane):

- Branch: `docs/readme-typo` (forked from `main`)
- Worktree: `<repo_parent>/.worktrees/<repo_name>/readme-typo`
- tmux pane: `tmux split-window -h -d` from the caller's `$TMUX_PANE` — new pane to the right, focus stays on the caller
- Prompt saved to `~/.agent-worktree/prompts/<name>.md` (outside the worktree so it stays clean) and piped into `claude` via stdin in the new pane
- State tracked in `~/.agent-worktree/state.json` (records include `pane_id`; legacy records from before the split-window migration carry `session` and are still handled by status/cleanup)

## Caveats

- **Conflict avoidance is the caller's responsibility.** This skill does not check whether the side task touches files the main session is editing.
- **Prompt is fire-and-forget.** Once spawned, the sub-agent can't see the main session's context.
- **Cleanup deletes the branch.** Merge or push anything you want to keep before cleaning up.
