"""Chapter 4: tie it together, scan the repo and say how old each marker is and who added it."""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import gitblame as gb
from . import markers as mk
from . import tokenizer as tk

DAY = 86400


@dataclass
class Item:
    path: str
    marker: mk.Marker
    author: str = "uncommitted"
    time: int | None = None
    commit: str = ""

    def age_days(self, now: int) -> int | None:
        return None if self.time is None else max(0, (now - self.time) // DAY)


def read_text(path: str) -> str | None:
    with open(path, "rb") as fh:
        data = fh.read()
    if b"\0" in data[:8192]:
        return None  # binary: skip
    return data.decode("utf-8", "replace")  # never crash on non-UTF-8


def scan(root: str) -> list[Item]:
    pat = mk.compile_markers()
    items: list[Item] = []
    for rel in gb.list_files(root):
        lang = tk.lang_for(rel)
        full = os.path.join(root, rel)
        if lang is None or not os.path.isfile(full):
            continue
        text = read_text(full)
        if text is None:
            continue
        for line_no, body in tk.comments(text, lang):
            m = mk.parse(line_no, body, pat)
            if m:
                items.append(Item(rel, m))
    return items


def attribute(root: str, items: list[Item]) -> list[Item]:
    """Blame only the marker lines, one git call per file."""
    tracked = set(gb.git(root, "ls-files", "-z").split("\0"))
    by_file: dict[str, list[Item]] = {}
    for it in items:
        if it.path in tracked:  # untracked files have no history: they stay "uncommitted"
            by_file.setdefault(it.path, []).append(it)
    for path, group in by_file.items():
        blamed = gb.blame_lines(root, path, [i.marker.line for i in group])
        for it in group:
            b = blamed.get(it.marker.line)
            if b and b.time is not None:
                it.author, it.time, it.commit = b.author, b.time, b.sha
    return items


def oldest_first(items: list[Item]) -> list[Item]:
    return sorted(items, key=lambda i: (i.time is None, i.time or 0, i.path, i.marker.line))
