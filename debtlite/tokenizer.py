"""Chapter 1: find comments without being fooled by strings.

A grep for TODO cannot tell `# TODO: fix` from `x = "# TODO"`. The only way to
tell is to walk the file once and remember whether we are inside a string.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    name: str
    line: tuple[str, ...]  # line-comment openers
    block: tuple[tuple[str, str], ...] = ()  # (open, close) block comments
    triple: tuple[str, ...] = ()  # Python-style triple-quoted strings
    ws_before_line: bool = False  # `#` only starts a comment after whitespace (shell)


PYTHON = Lang("python", ("#",), triple=('"""', "'''"))
C_LIKE = Lang("c-like", ("//",), block=(("/*", "*/"),))
SHELL = Lang("shell", ("#",), ws_before_line=True)
SQL = Lang("sql", ("--",), block=(("/*", "*/"),))

BY_EXT = {
    "py": PYTHON,
    "c": C_LIKE, "h": C_LIKE, "cpp": C_LIKE, "java": C_LIKE, "js": C_LIKE, "ts": C_LIKE, "go": C_LIKE, "rs": C_LIKE,
    "sh": SHELL, "bash": SHELL,
    "sql": SQL,
}  # fmt: skip


def lang_for(path: str) -> Lang | None:
    return BY_EXT.get(path.rsplit(".", 1)[-1].lower()) if "." in path else None


def comments(text: str, lang: Lang) -> list[tuple[int, str]]:
    """Return [(line_number, comment_text_on_that_line)], 1-based.

    A block comment spanning three lines yields three entries, because the
    marker rules (chapter 2) work one line at a time.
    """
    text = text.replace("\r\n", "\n")  # CRLF files: never let \r leak into comment text
    out: list[tuple[int, str]] = []
    i, n, line = 0, len(text), 1

    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue

        # 1. triple-quoted strings (Python): skip to the closing triple
        tri = next((t for t in lang.triple if text.startswith(t, i)), None)
        if tri:
            end = text.find(tri, i + 3)
            end = n if end == -1 else end + 3
            line += text.count("\n", i, end)
            i = end
            continue

        # 2. block comments: record every physical line
        blk = next((b for b in lang.block if text.startswith(b[0], i)), None)
        if blk:
            end = text.find(blk[1], i + len(blk[0]))
            stop = n if end == -1 else end
            body = text[i + len(blk[0]) : stop]
            for k, part in enumerate(body.split("\n")):
                out.append((line + k, part))
            line += body.count("\n")
            i = n if end == -1 else end + len(blk[1])
            continue

        # 3. line comments
        opener = next((p for p in lang.line if text.startswith(p, i)), None)
        if opener and not (lang.ws_before_line and i > 0 and text[i - 1] not in " \t\n"):
            end = text.find("\n", i)
            end = n if end == -1 else end
            out.append((line, text[i + len(opener) : end]))
            i = end
            continue

        # 4. ordinary strings: skip them whole so a '#' inside is not a comment.
        #    A quote with no partner on its line (an apostrophe) is just a character.
        if ch in "\"'":
            j = i + 1
            while j < n and text[j] != "\n":
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == ch:
                    break
                j += 1
            if j < n and text[j] == ch:
                i = j + 1
                continue

        i += 1
    return out
