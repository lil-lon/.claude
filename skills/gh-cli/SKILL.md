---
name: gh-cli
description: |
  Use the GitHub CLI (`gh`) to fetch information from GitHub: issues, PRs,
  comments, reviews, workflow runs, repos, and search. A curated set of
  read-only `gh` subcommands and read-only `gh api` endpoints are
  pre-approved and run without prompts. The sandbox
  lets `gh *` reach the network unsandboxed.

  Write operations (anything that changes state on GitHub) are NOT
  pre-approved and MUST NOT be executed unless the user explicitly asks
  for that write. Even when explicitly requested, run the natural command
  and let the harness's approval prompt fire — NEVER reshape the command
  to evade pattern matching.

  Use this skill whenever you need information from GitHub. Proactively
  invoke it (do NOT answer from memory or prior conversation) when the
  user references a GitHub issue, PR, review, comment, action run, or
  repo, or asks things like "show me the comments", "what's in PR #N",
  "what did the reviewer say".
allowed-tools:
  - Bash
---

## Read-only commands (pre-approved, run freely)

- `gh issue list ...` — list issues with filters (state, label, author,
  assignee, search)
- `gh issue view <n>` (incl. `--comments`) — one issue's body and
  metadata; `--comments` adds the conversation
- `gh pr list ...` — list PRs with filters (state, label, author, base,
  head)
- `gh pr view <n>` (incl. `--comments`) — one PR's body and metadata;
  `--comments` adds issue comments + review summaries (NOT inline
  review comments — see `gh api` below)
- `gh pr diff <n>` — show the diff of a PR
- `gh pr checks <n>` — CI / check status of a PR
- `gh repo view [owner/repo]` — repo metadata (description, default
  branch, README)
- `gh run list ...` — list workflow runs (CI history)
- `gh run view <id>` (incl. `--log`) — one run's status; `--log` adds
  the full log
- `gh search <type> ...` — search across GitHub: `issues`, `prs`,
  `code`, `commits`, `repos`

## Read-only `gh api` endpoints (pre-approved, exact form only)

`gh pr view --comments` shows issue comments and review summaries but
NOT inline (line-level) review comments. For those, use `gh api`. The
following three GET endpoints are pre-approved:

- `gh api repos/<owner>/<repo>/issues/<n>/comments` — issue/PR conversation comments
- `gh api repos/<owner>/<repo>/pulls/<n>/comments` — inline review comments on code lines
- `gh api repos/<owner>/<repo>/pulls/<n>/reviews` — review summaries

The patterns are deliberately exact (no trailing `*`). Any extra flag
or query string — `--paginate`, `?per_page=100`, `-q`, `--jq`, etc. —
falls through to an approval prompt. Do NOT widen, split, or otherwise
reshape the call to slip past this; if the bare form is not enough,
accept the prompt.

## Write operations

A write operation is any `gh` invocation that changes state on GitHub.
Writes are NOT pre-approved — every write surfaces an approval prompt.

### In scope: writes you may run when the user explicitly asks

When the user explicitly requests one of these, construct the natural
command and run it. The harness will prompt for approval; that prompt
is the user's confirmation.

- `gh pr <subcommand>` — typical writes: `create`, `close`, `reopen`,
  `comment`, `edit`, `merge`, `review`, `ready`
- `gh issue <subcommand>` — typical writes: `create`, `close`,
  `reopen`, `comment`, `edit`

### Out of scope

Any other write — `gh repo` writes, `gh release ...`, `gh run cancel /
delete / rerun`, `gh secret ...`, `gh workflow ...`, `gh api` with
`-X POST | PATCH | DELETE | PUT` or `--method ...`, etc. — has no
current use case. Do not execute these.

### Rules

1. **Never execute a write unless the user explicitly asks for that
   write.** Phrases like "add a comment", "comment on the PR", "merge
   it", "close this issue" are explicit. Inferring writes from context
   ("ship this", "let them know") is NOT explicit — ask first.

2. **When the user does ask (in-scope writes), run the natural
   command.** Example: `gh pr comment 123 --body "..."`. The command
   is not in the allow-list, so the harness surfaces an approval
   prompt. **That prompt is the user's confirmation. Do not try to
   skip it.**

3. **Never reshape a write to evade pattern matching.** Prohibited:
   - Hiding the body via `--body-file -`, here-docs, or stdin pipes
     to disguise the visible command shape.
   - Splitting one API call into several to slip under allow-list
     rules.
   - Using a different channel (web URL, `git push` of a
     PR-creating commit, etc.) to achieve the same write without
     going through the prompt.

   If a write requires approval, let it require approval.

4. If unsure whether a command writes, treat it as a write.
