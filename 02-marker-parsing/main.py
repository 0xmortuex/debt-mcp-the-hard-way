"""Chapter 2: comment text -> marker, author, tickets, with a strict word rule."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import markers as mk  # noqa: E402
from debtlite import tokenizer as tk  # noqa: E402

PAT = mk.compile_markers()


def parse(src: str, name: str = "a.py") -> list[tuple[str, str | None, list[str], str]]:
    lang = tk.lang_for(name)
    assert lang is not None
    out = []
    for n, body in tk.comments(src, lang):
        m = mk.parse(n, body, PAT)
        if m:
            out.append((m.marker, m.author, m.tickets, m.text))
    return out


# --- annotations ---------------------------------------------------------------
assert parse("# TODO: plain\n") == [("TODO", None, [], "plain")]
assert parse("# TODO(alice): owned\n") == [("TODO", "alice", [], "owned")]
assert parse("# FIXME[JIRA-9] ticketed\n") == [("FIXME", None, ["JIRA-9"], "ticketed")]
assert parse("# TODO(bob, #123): both\n") == [("TODO", "bob", ["#123"], "both")]
assert parse("# HACK see #45 and PROJ-7\n") == [("HACK", None, ["#45", "PROJ-7"], "see #45 and PROJ-7")]
assert parse("/// TODO: rust doc comment\n", "a.rs") == [("TODO", None, [], "rust doc comment")]
assert parse("/*\n * FIXME: star-prefixed block line\n */\n", "a.c") == [("FIXME", None, [], "star-prefixed block line")]

# --- the false-positive corpus: comments that mention a marker without being one --
for prose in (
    "# TODOS are tracked elsewhere",
    "# todo_list is a variable",
    "# see the TODO list in the wiki",
    "# Mastodon FIXME",
    "# lowercase todo is ignored",
):
    assert parse(prose + "\n") == [], prose

# --- identifiers in code never reach the parser, because they are not comments ----
assert parse("todos_list = []\nTODOS = 3\nMastodon = 1\n") == []

print("chapter 2 ok: annotations parsed, prose and identifiers rejected")
