---
name: complete-implementation
description: |
  Complete an implementation end-to-end: stage targeted changes, run
  `codex-review`, fix any P1/P2 findings (loop up to 3×), commit using
  Conventional Commits, then push. Use when the user asks to finalize,
  ship, wrap up, or "complete" the current implementation.
allowed-tools:
  - Bash
  - AskUserQuestion
  - Skill
---

1. Run `git status`. Decide the staging set:
   - If the conversation makes the target obvious, stage directly with
     `git add <file>` (never `-A` / `.` / `-u`).
   - Otherwise ask the user via AskUserQuestion. Wait at this step if
     the user wants to narrow the scope further.

2. Invoke the `codex-review` skill against the staged change set.

3. If the review reports any P1 or P2 finding: fix the code, re-stage
   the updated files, and re-invoke `codex-review`. Cap this loop at 3
   iterations total. If iteration 3 still surfaces P1/P2, stop and
   report to the user — do not commit.

4. P3/P4-only or no findings: draft a Conventional Commits message in
   the form `<type>(<optional-scope>): <subject>` (type ∈ feat / fix /
   refactor / docs / test / chore / perf / build / ci / style / revert),
   subject in imperative mood and under ~70 chars. Add a body
   explaining *why* if not obvious from the diff. Confirm the message
   with the user, then `git commit -m "<message>"` (HEREDOC for
   multi-line).

5. Determine the current branch with `git branch --show-current`, then
   push with upstream tracking: `git push -u origin <branch>`.
