## Guidance

- Write all code, code comments, and documentation in English.
- Keep code as simple as possible. Do not add flexible arguments, defensive `try`/`except` blocks, or speculative abstractions unless explicitly requested.
- Always ground every output — code, comments, documentation, explanations, anything you produce — in sources you have actually inspected. Only write what you can verify. If something prevents you from confirming what you need, do NOT guess — stop and ask the user to supply the missing context.
  - Concretely, when writing or modifying code, read the relevant source files first: the function/module you are editing, its callers, the types and signatures it depends on. Do not write code based on what an API "probably" looks like.

## Tool usage

- Bash commands used for file reading — `cat`, `head`, `tail`, `find`, `grep`, etc. — are prohibited as a matter of policy. Use Claude Code's built-in tools (`Read`, `Grep`, `Glob`) for these tasks instead. `ls` is allowed for directory listing since no built-in tool covers it.
- Chaining, redirecting, and shell-expansion in commands is prohibited because compound commands can slip dangerous operations past user review. Do not run commands containing `&&`, `&`, `;`, `>`, `<`, `|`, `` ` ``, `$(`, `$'`, `$"`, `${`, `$[`, or newlines — the rule matches the literal characters anywhere in the command string, so even a `;` inside a commit message will be rejected. Plain `$VAR` (variable reference without an expansion sigil) is allowed.
- Commit messages must be assembled from multiple `-m` flags (HEREDOC syntax requires blocked characters). Each `-m` becomes a paragraph; put the Co-Authored-By trailer in the last `-m`. Example: `git commit -m "subject" -m "body" -m "Co-Authored-By: Claude <noreply@anthropic.com>"`.
- When a workflow legitimately needs a pipe or backtick command substitution, write a script under `./bin/` and invoke it as a single command. The script is committed and reviewed via the standard commit/codex-review flow; do not run an unreviewed script as a way to hide the blocked operators. For commit messages that need backtick-formatted inline code, write the message to `/tmp/claude/<file>` and use `git commit -F /tmp/claude/<file>` (or `gh pr create --body-file ...` for PR bodies).

## Development flow

When the user explicitly asks to wrap up an implementation ("create a PR",
"commit this", "ship it", or similar), use the `complete-implementation` skill.

## Review policy

For generic "review" or "check" requests on recent code changes, use the
built-in `/review` skill. Use the `codex-review` skill only when the user
explicitly asks for a Codex review (e.g. "codex review", "review with
codex"), or when another skill (such as `complete-implementation`)
invokes it.
