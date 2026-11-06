"""Chapter 3: talk to git and read `git blame --porcelain`."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass


def git(root: str, *args: str) -> str:
    """Run git with an argument LIST (never a shell string) and without touching the repo."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(["git", "-C", root, *args], capture_output=True, env=env, stdin=subprocess.DEVNULL)
    if p.returncode:
        raise RuntimeError(f"git {args[0]} failed: {p.stderr.decode('utf-8', 'replace').strip()}")
    return p.stdout.decode("utf-8", "replace")  # replacement chars instead of crashes on odd bytes


def list_files(root: str) -> list[str]:
    """Tracked + untracked-but-not-ignored files: .gitignore is honoured for free."""
    out = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted(set(p for p in out.split("\0") if p))


@dataclass
class Blame:
    sha: str
    author: str
    time: int | None  # None = not committed yet
    summary: str


_HEADER = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64}) (\d+) (\d+)(?: (\d+))?$")


def parse_porcelain(raw: str) -> dict[int, Blame]:
    """Porcelain format: a header line per source line; the commit's metadata
    (author, author-time, summary ...) is printed only the FIRST time a commit
    shows up, so we remember it by sha. The source line itself starts with a TAB.
    """
    commits: dict[str, dict[str, str]] = {}
    result: dict[int, Blame] = {}
    cur: tuple[str, int] | None = None
    for line in raw.split("\n"):
        if cur is None:
            m = _HEADER.match(line)
            if m:
                cur = (m.group(1), int(m.group(3)))
            continue
        if line.startswith("\t"):
            sha, final_line = cur
            meta = commits[sha]
            uncommitted = set(sha) == {"0"}  # all-zero sha = edited in the work tree
            result[final_line] = Blame(
                sha,
                "uncommitted" if uncommitted else meta["author"],
                None if uncommitted else int(meta["author-time"]),
                meta.get("summary", ""),
            )
            cur = None
        else:
            key, _, val = line.partition(" ")
            commits.setdefault(cur[0], {})[key] = val
    return result


def blame_lines(root: str, path: str, lines: list[int]) -> dict[int, Blame]:
    """-w ignores whitespace-only changes, -M follows lines moved inside the file,
    -L limits git to the lines we care about (a big file with 3 TODOs is cheap)."""
    args = ["blame", "--porcelain", "-w", "-M"]
    for n in sorted(set(lines)):
        args += ["-L", f"{n},{n}"]
    return parse_porcelain(git(root, *args, "--", path))
