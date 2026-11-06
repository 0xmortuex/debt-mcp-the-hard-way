"""Chapter 1: the tokenizer finds real comments and ignores look-alikes."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import tokenizer as tk  # noqa: E402


def lines(name: str, src: str) -> list[int]:
    lang = tk.lang_for(name)
    assert lang is not None
    return [n for n, _ in tk.comments(src, lang)]


# --- real comments, in several languages -------------------------------------
assert lines("a.py", "x = 1  # one\n# two\n") == [1, 2]
assert lines("a.c", "int x; // one\n/* two\n   three */\n") == [1, 2, 3]
assert lines("a.sql", "SELECT 1; -- one\n/* two */\n") == [1, 2]
assert lines("a.sh", "# one\nls # two\n") == [1, 2]

# --- look-alikes: none of these contain a comment ------------------------------
assert lines("a.py", 'x = "# TODO"\n') == []
assert lines("a.py", "x = '# FIXME'\n") == []
assert lines("a.py", 's = """\n# not a comment\n"""\n') == []
assert lines("a.c", 'puts("// TODO");\n') == []
assert lines("a.c", 'puts("/* FIXME */");\n') == []
assert lines("a.js", "const u = 'http://example.com/x';\n") == []  # `//` inside a string (a URL)
assert lines("a.sql", "SELECT '-- TODO';\n") == []
assert lines("a.sh", "echo $#\n") == []  # `#` right after `$` is the argument count, not a comment

# --- robustness ----------------------------------------------------------------
assert lines("a.py", "x = 1\r\n# crlf\r\n") == [2]  # CRLF line endings
assert lines("a.py", "it's fine # real comment\n") == [1]  # an apostrophe does not open a string
assert lines("a.c", "/* never closed\nstill comment\n") == [1, 2, 3]  # unterminated: no crash, no loop (3 = the empty tail)
assert lines("a.py", "x = '" + "a" * 200_000 + "'  # end\n") == [1]  # very long line

print("chapter 1 ok: comments found, look-alikes ignored")
