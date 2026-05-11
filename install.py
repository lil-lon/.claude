#!/usr/bin/env python3
"""Install shared CLAUDE config into a CLAUDE_CONFIG_DIR.

By default each top-level item (CLAUDE.md, settings.json, bin, skills) is
symlinked from this repo so upstream changes flow through to the install.
With --copy each item is copied verbatim instead, and any destination that
already exists is left alone so local customizations survive re-runs.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ITEMS = ["CLAUDE.md", "settings.json", "bin", "skills"]


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def resolve_target() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if not env:
        print("error: CLAUDE_CONFIG_DIR is not set", file=sys.stderr)
        sys.exit(1)
    return Path(env).expanduser()


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--copy",
        action="store_true",
        help="copy each item instead of symlinking; skip entries that already exist",
    )
    return p.parse_args(argv)


def install_symlink(src: Path, dst: Path) -> int:
    if dst.is_symlink():
        if dst.resolve() == src.resolve():
            print(f"skip: {dst} already links to {src}")
            return 0
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
    return 0


def install_copy(src: Path, dst: Path) -> int:
    if dst.is_symlink() or dst.exists():
        print(f"skip: {dst} already exists")
        return 0
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)
    print(f"copied: {src} -> {dst}")
    return 0


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = resolve_target()
    target.mkdir(parents=True, exist_ok=True)
    root = repo_root()

    install = install_copy if args.copy else install_symlink

    for name in ITEMS:
        src = root / name
        dst = target / name
        if not src.exists():
            continue
        if install(src, dst) != 0:
            return 1

    if not args.copy:
        # Drop broken symlinks left by entries removed from the repo. Skipped
        # in copy mode because those entries are user data, not managed links.
        for name in ITEMS:
            dst = target / name
            if dst.is_symlink() and not dst.exists():
                dst.unlink()
                print(f"removed dangling: {dst}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
