"""Chapter 2: from comment text to a marker with an author and tickets."""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_MARKERS = ("TODO", "FIXME", "HACK", "XXX", "BUG")
_DECORATION = " \t*/#!-=;>@"  # what may sit in front of the marker: `///`, ` * `, `# `
_TICKET = re.compile(r"(?<![\w/-])([A-Z][A-Z0-9]{1,9}-\d+)\b|(?<![\w&/])#(\d{1,7})\b")


@dataclass
class Marker:
    line: int
    marker: str
    text: str
    author: str | None
    tickets: list[str]


def compile_markers(names: tuple[str, ...] = DEFAULT_MARKERS) -> re.Pattern[str]:
    # (?![A-Za-z0-9_]) is the word boundary: TODOS and TODO_LIST do not match.
    return re.compile("(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + ")(?![A-Za-z0-9_])")


def tickets_in(s: str) -> list[str]:
    found = [a or "#" + b for a, b in _TICKET.findall(s)]
    return list(dict.fromkeys(found))


def parse(line_no: int, body: str, pat: re.Pattern[str]) -> Marker | None:
    """A marker counts only as the FIRST WORD of a comment line.

    That one rule removes almost every false positive: "see the TODO list" is
    prose, "# TODO: fix" is a finding.
    """
    k = 0
    while k < len(body) and body[k] in _DECORATION:
        k += 1
    m = pat.match(body, k)
    if not m:
        return None
    rest = body[m.end() :]
    author = None
    ann = re.match(r"\s*[(\[]([^)\]]{0,80})[)\]]", rest)  # an annotation right after the marker: (alice) or [JIRA-9]
    ticket_list: list[str] = []
    if ann:
        for part in ann.group(1).split(","):
            part = part.strip()
            if tickets_in(part):
                ticket_list += tickets_in(part)
            elif part and author is None:
                author = part.lstrip("@")
        rest = rest[ann.end() :]
    text = rest.lstrip(" \t:-").rstrip()
    for t in tickets_in(rest):
        if t not in ticket_list:
            ticket_list.append(t)
    return Marker(line_no, m.group(1), text[:300], author, ticket_list)
