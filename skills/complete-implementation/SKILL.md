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

1. Run `git branch --show-current`. If the current branch is a main
   branch — `main`, `master`, `dev`, or `develop` — create a feature
   branch and switch to it before staging: pick a name in
   `<type>/<short-scope>` form matching the Conventional Commits type
   for the work (e.g. `feat/...`, `fix/...`, `refactor/...`) based on
   the conversation. After this step `git branch --show-current` must
   return the new branch name; if it still returns a main branch,
   stop and re-run with a command that both creates and switches.

2. Run `git status`. Decide the staging set:
   - If the conversation makes the target obvious, stage directly with
     `git add <file>` (never `-A` / `.` / `-u`).
   - Otherwise ask the user via AskUserQuestion. Wait at this step if
     the user wants to narrow the scope further.

3. Invoke the `codex-review` skill against the staged change set.

4. If the review reports any P1 or P2 finding: fix the code, re-stage
   the updated files, and re-invoke `codex-review`. Cap this loop at 3
   iterations total. If iteration 3 still surfaces P1/P2, stop and
   report to the user — do not commit.

5. P3/P4-only or no findings: draft a Conventional Commits message in
   the form `<type>(<optional-scope>): <subject>` (type ∈ feat / fix /
   refactor / docs / test / chore / perf / build / ci / style / revert),
   subject in imperative mood and under ~70 chars. Add a body
   explaining *why* if not obvious from the diff. Confirm the message
   with the user, then commit. For a single-paragraph message, use
   `git commit -m "<subject>"`. For multi-paragraph messages, pass one
   `-m` per paragraph (e.g. `git commit -m "<subject>" -m "<body>"`);
   HEREDOC is unavailable because the Bash hook blocks `<` and
   newlines. If the message requires backtick-formatted inline code,
   write it to `/tmp/claude/<file>` and use
   `git commit -F /tmp/claude/<file>`.

6. Determine the current branch with `git branch --show-current`, then
   push with upstream tracking: `git push -u origin <branch>`.
