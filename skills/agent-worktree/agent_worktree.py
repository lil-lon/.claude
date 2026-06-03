#!/usr/bin/env python3
"""
agent_worktree.py — Spawn / clean up Claude Code sub-tasks running in
isolated git worktrees + tmux panes inside the caller's tmux window.

Subcommands:
  spawn <type> <name> <prompt>   Create worktree, split a new tmux pane next to
                                 the caller, and launch Claude Code there.
  status <name>                  Print status of a single task.
  cleanup <name>                 Kill the agent's tmux pane and remove the
                                 worktree + branch.

The skill requires the caller to be inside a tmux session ($TMUX_PANE set).
The child pane lives in the same window as the caller — no attach needed.

<type> must be a Conventional Commit type: feat, fix, chore, docs, refactor,
test, perf, build, ci, style, revert.

Conventions (fixed):
- Base branch:  main
- Agent CLI:    claude
- Branch:       <type>/<name>
- Worktree:     <repo_parent>/.worktrees/<repo_name>/<name>
- tmux pane:    split horizontally from the caller's pane (new pane on the right)

State is persisted at ~/.agent-worktree/state.json. Records created before the
split-window migration use ``session`` instead of ``pane_id``; status/cleanup
handle both shapes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path.home() / ".agent-worktree"
STATE_FILE = STATE_DIR / "state.json"

BASE_BRANCH = "main"
AGENT_CMD = "claude"
# Restricts <name> to a strict kebab-case slug. Required to prevent
# (a) shell injection in the tmux send-keys command below and
# (b) path traversal in the worktree / prompt-file paths derived from name.
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
CONVENTIONAL_TYPES = {
    "feat",
    "fix",
    "chore",
    "docs",
    "refactor",
    "test",
    "perf",
    "build",
    "ci",
    "style",
    "revert",
}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def run(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    r = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True
    )
    if check and r.returncode != 0:
        die(f"command failed: {' '.join(cmd)}\n  {(r.stderr or '').strip()}")
    return r


def repo_root() -> Path:
    return Path(run(["git", "rev-parse", "--show-toplevel"]).stdout.strip())


def tmux_alive(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session], check=False).returncode == 0


def pane_alive(pane_id: str) -> bool:
    r = run(["tmux", "list-panes", "-a", "-F", "#{pane_id}"], check=False)
    if r.returncode != 0:
        return False
    return pane_id in r.stdout.split()


def parent_pane_or_die() -> str:
    pane = os.environ.get("TMUX_PANE")
    if not pane:
        die(
            "agent-worktree requires the caller to be inside a tmux session "
            "($TMUX_PANE is not set). Start one (e.g. `tmux new -s work`) and "
            "re-run from inside it."
        )
    return pane


def load_state() -> dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict[str, dict]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def cmd_spawn(args: argparse.Namespace) -> None:
    type_: str = args.type
    name: str = args.name
    prompt: str = args.prompt

    if type_ not in CONVENTIONAL_TYPES:
        die(
            f"invalid type: {type_!r}. Must be one of: {', '.join(sorted(CONVENTIONAL_TYPES))}"
        )

    if not NAME_RE.match(name):
        die(
            f"invalid name: {name!r}. "
            "Use lowercase letters, digits, '-' or '_'; 1-64 chars; "
            "must start with letter or digit."
        )

    if not shutil.which("tmux"):
        die("tmux is not installed or not on PATH")
    if not shutil.which(AGENT_CMD):
        die(f"agent command not found on PATH: {AGENT_CMD!r}")

    parent_pane = parent_pane_or_die()

    root = repo_root()
    branch = f"{type_}/{name}"
    worktree_dir = root.parent / ".worktrees" / root.name / name

    state = load_state()
    if name in state:
        die(f"task already exists: {name}  (run cleanup first or pick another name)")

    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    run(
        ["git", "worktree", "add", "-b", branch, str(worktree_dir), BASE_BRANCH],
        cwd=root,
    )

    prompts_dir = STATE_DIR / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = prompts_dir / f"{name}.md"
    prompt_file.write_text(prompt)

    # Split the caller's tmux pane so the child Claude Code instance appears
    # in the same window. ``-h`` puts the new pane to the right of the caller
    # (left/right split). ``-d`` keeps focus on the caller's pane so the user
    # is not yanked away from whatever they were doing.
    pane_id = run(
        [
            "tmux",
            "split-window",
            "-t",
            parent_pane,
            "-h",
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-c",
            str(worktree_dir),
        ]
    ).stdout.strip()

    run(
        [
            "tmux",
            "send-keys",
            "-t",
            pane_id,
            f"cat {shlex.quote(str(prompt_file))} | {AGENT_CMD}",
            "Enter",
        ]
    )

    state[name] = {
        "name": name,
        "type": type_,
        "branch": branch,
        "worktree": str(worktree_dir),
        "pane_id": pane_id,
        "parent_pane": parent_pane,
        "repo_root": str(root),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_state(state)

    print(
        json.dumps(
            {
                "ok": True,
                "name": name,
                "branch": branch,
                "worktree": str(worktree_dir),
                "pane_id": pane_id,
                "hint": "New pane opened to the right. Use Ctrl-b o (or Ctrl-b arrow) to focus it.",
            },
            indent=2,
        )
    )


def cmd_status(args: argparse.Namespace) -> None:
    state = load_state()
    info = state.get(args.name)
    if not info:
        die(f"unknown task: {args.name}")

    info = dict(info)
    if "pane_id" in info:
        info["status"] = "running" if pane_alive(info["pane_id"]) else "stopped"
    else:
        # Legacy record from before the split-window migration.
        info["status"] = "running" if tmux_alive(info["session"]) else "stopped"

    worktree = Path(info["worktree"])
    if worktree.exists():
        r = run(
            ["git", "-C", str(worktree), "log", "-1", "--format=%h %s"], check=False
        )
        info["last_commit"] = r.stdout.strip() if r.returncode == 0 else None
        r = run(["git", "-C", str(worktree), "status", "--porcelain"], check=False)
        info["dirty"] = bool(r.stdout.strip()) if r.returncode == 0 else None

    print(json.dumps(info, indent=2))


def unsaved_work(worktree: Path, root: Path, branch: str) -> list[str]:
    problems: list[str] = []

    if worktree.exists():
        r = run(["git", "-C", str(worktree), "status", "--porcelain"], check=False)
        if r.returncode == 0 and r.stdout.strip():
            problems.append(f"worktree has uncommitted changes: {worktree}")

    r = run(
        ["git", "-C", str(root), "log", "--format=%H", f"{BASE_BRANCH}..{branch}"],
        check=False,
    )
    branch_only = r.stdout.strip().splitlines() if r.returncode == 0 else []
    if branch_only:
        r = run(
            ["git", "-C", str(root), "log", "--format=%H", f"origin/{branch}"],
            check=False,
        )
        pushed = set(r.stdout.strip().splitlines()) if r.returncode == 0 else set()
        unpushed = [c for c in branch_only if c not in pushed]
        if unpushed:
            problems.append(
                f"branch {branch!r} has {len(unpushed)} commit(s) "
                f"not merged into {BASE_BRANCH} and not pushed"
            )

    return problems


def cmd_cleanup(args: argparse.Namespace) -> None:
    state = load_state()
    info = state.get(args.name)
    if not info:
        die(f"unknown task: {args.name}")

    worktree = Path(info["worktree"])
    root = Path(info["repo_root"])
    branch = info["branch"]

    if not args.force:
        problems = unsaved_work(worktree, root, branch)
        if problems:
            die(
                "refusing to clean up — unsaved work would be lost:\n  "
                + "\n  ".join(problems)
                + "\n\nMerge or push the work first, or re-run with --force."
            )

    if "pane_id" in info:
        if pane_alive(info["pane_id"]):
            run(["tmux", "kill-pane", "-t", info["pane_id"]], check=False)
    elif "session" in info and tmux_alive(info["session"]):
        # Legacy record from before the split-window migration.
        run(["tmux", "kill-session", "-t", info["session"]], check=False)

    if worktree.exists():
        run(
            ["git", "worktree", "remove", str(worktree), "--force"],
            cwd=root,
            check=False,
        )

    run(["git", "branch", "-D", branch], cwd=root, check=False)

    prompt_file = STATE_DIR / "prompts" / f"{args.name}.md"
    if prompt_file.exists():
        prompt_file.unlink()

    del state[args.name]
    save_state(state)
    print(json.dumps({"ok": True, "cleaned": args.name}, indent=2))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        prog="agent_worktree.py",
        description="Spawn Claude Code sub-tasks in isolated git worktrees + tmux panes.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("spawn", help="Create worktree + tmux pane + launch agent.")
    sp.add_argument(
        "type",
        help=f"Conventional Commit type ({', '.join(sorted(CONVENTIONAL_TYPES))}).",
    )
    sp.add_argument("name", help="Task name (kebab-case).")
    sp.add_argument("prompt", help="Prompt to send to Claude Code.")
    sp.set_defaults(func=cmd_spawn)

    ss = sub.add_parser("status", help="Show status of a single task.")
    ss.add_argument("name")
    ss.set_defaults(func=cmd_status)

    sc = sub.add_parser("cleanup", help="Kill tmux pane, remove worktree, delete branch.")
    sc.add_argument("name")
    sc.add_argument(
        "--force",
        action="store_true",
        help="Force cleanup even if the branch has uncommitted or unpushed work.",
    )
    sc.set_defaults(func=cmd_cleanup)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
