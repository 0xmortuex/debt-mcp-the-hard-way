# debt-mcp, the hard way

Build a small version of [debt-mcp](https://github.com/0xmortuex/debt-mcp) from scratch: an MCP server that
finds `TODO` / `FIXME` markers in a repository and tells you **how old each one is and who added it**, using
real `git blame`.

By the end you will have written, in about 500 lines of dependency-free Python:

- a comment tokenizer that does not report `"TODO"` inside strings or URLs,
- a marker parser (`TODO(alice):`, `FIXME[JIRA-9]`, `#123`) with a strict word rule,
- a `git blame --porcelain` reader,
- exact age and author attribution, including uncommitted and untracked lines,
- "stale in a busy file vs stale in a dead file" analysis from `git log`,
- suppression counts (`# noqa`, `@ts-ignore`, ...), long functions and commented-out code,
- an MCP wrapper with a directory sandbox, tested over real stdio.

The real server does the same things with more languages and more care; the final chapter lists the gaps.

## Chapters

| # | Chapter | You learn |
|---|---|---|
| 1 | [Comments, not grep](01-comments-not-grep/README.md) | a one-pass tokenizer; why strings, URLs and `$#` break grep |
| 2 | [Marker parsing](02-marker-parsing/README.md) | the "first word of a comment" rule; annotations; the false-positive corpus |
| 3 | [git blame --porcelain](03-git-blame-porcelain/README.md) | the format, `-w -M -L`, uncommitted lines, running git safely |
| 4 | [Age and author](04-age-and-author/README.md) | scan + blame, exact ages with a pinned clock, scripted repos |
| 5 | [Stale: hot or dead](05-stale-hot-or-dead/README.md) | `git log` activity; why an old TODO in a busy file is the worst kind |
| 6 | [Suppression signals](06-suppression-signals/README.md) | other cheap debt signals, counted only inside real comments |
| 7 | [The MCP wrapper](07-the-mcp-wrapper/README.md) | tools, ToolError, a path sandbox, a stdio test |

Every chapter has prose, runnable code (in [`debtlite/`](debtlite)) and a `main.py` that checks its own claims
with `assert`.

## Run it

Needs Python 3.10+ and `git`.

```
pip install -r requirements.txt
python verify.py          # all chapters, exactly what CI runs
python verify.py 03 04    # some chapters
python 04-age-and-author/main.py
```

`verify.py` is the source of truth: if a chapter's code and its README disagree, CI fails. The tests build real
git repositories in a temp directory with fixed authors and dates (`GIT_AUTHOR_DATE` and friends), so ages are exact and
identical on every machine.

MIT licensed.
