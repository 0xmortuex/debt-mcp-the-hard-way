# 3. git blame --porcelain

To say how old a line is we ask git who last changed it. `git blame` has a format made for programs:

```
git blame --porcelain -w -M -L 5,5 -- app.py
```

```
b1af50055ec4... 1 5 1
author Alice A
author-mail <alice@example.com>
author-time 1673352000
author-tz +0000
summary initial
filename app.py
	# TODO(alice): early marker
```

## How to read it

- A **header** line: `<sha> <original line> <final line> [<group size>]`. The *final* line is the line number in
  the file as it is today, which is what the tokenizer reports.
- **Metadata** (author, author-time, summary ...) is printed only the *first time* a commit appears in the output.
  Later lines from the same commit have a header and no metadata. [`parse_porcelain`](debtlite/gitblame.py)
  therefore keeps a dict keyed by sha.
- The source line is prefixed with a **TAB**. That is how the parser knows an entry is complete.
- An all-zero sha means "not committed yet": the line was edited in the work tree. We report author
  `uncommitted` and no age.

## The flags

| Flag | Why |
|---|---|
| `-w` | Ignore whitespace-only changes. Re-indenting a line must not reset its age. |
| `-M` | Detect lines moved within a file. Moving a function is not writing a TODO. |
| `-L n,n` | Blame only the lines we need. A 5,000-line file with three TODOs costs three lines, not 5,000. |
| `--porcelain` | Stable, machine-readable output. |

`author-time` is when the change was *authored*, not committed. Rebases change commit time but keep author time,
so it is the better answer to "how old is this".

## Running git safely

[`git()`](debtlite/gitblame.py) is the only place that starts a process:

- **An argument list**, never a shell string. A file named `x; rm -rf ~` is just a file name.
- `--` before the path, so a file called `-oops` is not an option.
- `GIT_OPTIONAL_LOCKS=0`: some commands refresh the index; a read-only tool must not write into `.git`.
- Output decoded with `errors="replace"`: an author name in Latin-1 must not crash the tool.
- A failing git call raises one readable `RuntimeError` instead of a traceback or an empty result.

`list_files` uses `git ls-files --cached --others --exclude-standard`: tracked and untracked-but-not-ignored files, so
`.gitignore` is honoured for free (a plain directory walk would need its own ignore logic).

## Run it

```
python 03-git-blame-porcelain/main.py
```

It builds a repository with three authors over 14 months, where carol *inserts two lines above alice's TODO*.
The line number changes; the author must not.

## Break it

- Remove `-w`, then re-indent a function in the test repo and see the blame move to you.
- Remove the `commits[sha]` memory and parse a file where one commit wrote two lines.

## Not covered here

Shallow clones (everything older than the clone depth is blamed on the boundary commit, so ages are only lower
bounds: the real server warns), mailmap (git already applies it in blame output), and `-C` copy detection (the
real server's `todo_history` uses it to tell whether a line was copied from another file).
