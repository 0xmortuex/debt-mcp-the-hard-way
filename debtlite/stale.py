"""Chapter 5: an old TODO in a busy file and one in a dead file are different problems."""

from __future__ import annotations

from collections import Counter

from . import attribution as at
from . import gitblame as gb


def commits_per_file(root: str, since_epoch: int) -> Counter[str]:
    """How many commits touched each file since `since_epoch` (git log --name-only)."""
    raw = gb.git(root, "log", f"--since={since_epoch}", "--no-renames", "--name-only", "--format=@@%H")
    counts: Counter[str] = Counter()
    for line in raw.split("\n"):
        if line and not line.startswith("@@"):
            counts[line] += 1
    return counts


def stale(
    root: str, now: int, older_than_days: int = 180, window_days: int = 90, min_commits: int = 2
) -> dict[str, list[at.Item]]:
    items = at.attribute(root, at.scan(root))
    activity = commits_per_file(root, now - window_days * at.DAY)
    buckets: dict[str, list[at.Item]] = {"hot": [], "cooling": [], "dead": []}
    for it in at.oldest_first(items):
        age = it.age_days(now)
        if age is None or age < older_than_days:
            continue
        n = activity.get(it.path, 0)
        buckets["hot" if n >= min_commits else "cooling" if n else "dead"].append(it)
    return buckets
