## Guidance

- Write all code, code comments, and documentation in English.
- Keep code as simple as possible. Do not add flexible arguments, defensive `try`/`except` blocks, or speculative abstractions unless explicitly requested.

## Development flow

When the user explicitly asks to wrap up an implementation ("create a PR",
"commit this", "ship it", or similar), use the `complete-implementation` skill.

## Review policy

For generic "review" or "check" requests on recent code changes, use the
built-in `/review` skill. Use the `codex-review` skill only when the user
explicitly asks for a Codex review (e.g. "codex review", "review with
codex"), or when another skill (such as `complete-implementation`)
invokes it.
