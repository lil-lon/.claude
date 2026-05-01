#!/usr/bin/env python3
"""Install shared CLAUDE config into a CLAUDE_CONFIG_DIR via symlinks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ITEMS = ["CLAUDE.md", "settings.json", "bin"]
DEFAULT_TARGET = Path.home() / ".claude"


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def resolve_target() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        return Path(env).expanduser()

    print(
        f"warning: CLAUDE_CONFIG_DIR is not set; "
        f"falling back to default ({DEFAULT_TARGET})",
    )
    return DEFAULT_TARGET


def main() -> int:
    target = resolve_target()
    target.mkdir(parents=True, exist_ok=True)
    root = repo_root()

    for name in ITEMS:
        src = root / name
        dst = target / name

        if not src.exists():
            continue

        if dst.is_symlink():
            if dst.resolve() == src.resolve():
                print(f"skip: {dst} already links to {src}")
                continue
            print(f"removing stale symlink: {dst} -> {dst.resolve()}")
            dst.unlink()
        elif dst.exists():
            print(
                f"conflict: {dst} already exists as a regular file or directory; "
                "resolve manually",
                file=sys.stderr,
            )
            return 1

        dst.symlink_to(src)
        print(f"linked: {dst} -> {src}")

    # Clean up symlinks whose target was removed from the repo. Path.exists()
    # follows symlinks, so a broken link returns False here.
    for name in ITEMS:
        dst = target / name
        if dst.is_symlink() and not dst.exists():
            dst.unlink()
            print(f"removed dangling: {dst}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
