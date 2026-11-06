"""Chapter 6: cheap debt signals that need no git at all."""

from __future__ import annotations

import re
from collections import Counter

from . import tokenizer as tk

SUPPRESSIONS = {
    "noqa": re.compile(r"\bnoqa\b", re.I),
    "type: ignore": re.compile(r"\btype:\s*ignore\b"),
    "@ts-ignore": re.compile(r"@ts-ignore\b"),
    "eslint-disable": re.compile(r"\beslint-disable"),
    "pylint: disable": re.compile(r"\bpylint:\s*disable"),
}


def count_suppressions(text: str, lang: tk.Lang) -> Counter[str]:
    """Count in comment text only: a string that merely CONTAINS '# noqa' is not a suppression."""
    counts: Counter[str] = Counter()
    for _, body in tk.comments(text, lang):
        for name, rx in SUPPRESSIONS.items():
            if rx.search(body):
                counts[name] += 1
    return counts


def long_file(text: str, limit: int = 1000) -> int | None:
    n = text.count("\n")
    return n if n > limit else None


_CODEY = re.compile(r"[;{}]\s*$|^\s*(def|class|import|return|if|for|while)\b|^\s*[\w.\[\]]+\s*=\s*\S|\w\([^()]*\)\s*$")


def commented_out_blocks(text: str, lang: tk.Lang, min_lines: int = 3) -> list[tuple[int, int]]:
    """Runs of >= min_lines consecutive comment lines where most look like code."""
    blocks: list[tuple[int, int]] = []
    run: list[tuple[int, str]] = []

    def flush() -> None:
        if len(run) >= min_lines and sum(1 for _, b in run if _CODEY.search(b)) / len(run) >= 0.6:
            blocks.append((run[0][0], run[-1][0]))

    for line_no, body in tk.comments(text, lang):
        if run and line_no != run[-1][0] + 1:
            flush()
            run.clear()
        run.append((line_no, body))
    flush()
    return blocks


def longest_function(text: str) -> tuple[str, int] | None:
    """Python only: a function ends at the next non-blank line indented no deeper than its `def`."""
    lines = text.split("\n")
    best: tuple[str, int] | None = None
    for i, line in enumerate(lines):
        m = re.match(r"(\s*)(?:async\s+)?def\s+(\w+)", line)
        if not m:
            continue
        indent, last = len(m.group(1)), i
        for j in range(i + 1, len(lines)):
            if lines[j].strip():
                if len(lines[j]) - len(lines[j].lstrip()) <= indent:
                    break
                last = j
        if best is None or last - i + 1 > best[1]:
            best = (m.group(2), last - i + 1)
    return best
