# 4. Age and author

[`debtlite/attribution.py`](debtlite/attribution.py) joins the pieces:

1. `gitblame.list_files` - which files to look at.
2. `tokenizer.lang_for` + `tokenizer.comments` - the comment lines of each.
3. `markers.parse` - which of those are markers.
4. `gitblame.blame_lines` - who and when, for exactly those lines.

```python
items = at.oldest_first(at.attribute(root, at.scan(root)))
```

## Decisions worth noting

**Scan first, blame second.** Blame is the expensive step (one git process per file). Scanning finds the marker
lines in pure Python; only files that have markers are blamed, and only on those lines.

**Untracked files stay "uncommitted".** A file git has never seen has no history; asking blame would fail. The item keeps
`author="uncommitted"` and `age_days=None`, and `oldest_first` sorts these last. Never guess an age.

**Binary and odd files.** `read_text` skips files with a NUL byte in the first 8 KB, and decodes everything else
as UTF-8 with replacement characters. A Latin-1 file is scanned instead of crashing the whole run.

**A pinned clock.** `age_days(now)` takes `now` as a parameter. The tests use `2024-06-01T00:00:00Z`, so
"Alice's TODO is 507 days old" is a fact you can assert, not "about a year". Without that, a test written today fails next week.

## Exact ages

The scripted history in [`debtlite/testrepo.py`](debtlite/testrepo.py):

| When | Who | What |
|---|---|---|
| 2023-01-10 12:00 | Alice A | `app.py` with `TODO(alice)` and `HACK`; `util.js` with `FIXME[JIRA-9]` |
| 2023-06-15 08:30 | Bob B | adds a `BUG` line |
| 2024-03-01 00:00 | Carol C | adds two imports *above* alice's TODO |

At `2024-06-01` the oldest three are 507 days old and all Alice's, even though carol touched the file last. The `BUG`
is 351 days old and Bob's. The string `'TODO: in a string'` that carol added is not reported.

The identity and dates come from `GIT_AUTHOR_NAME`, `GIT_AUTHOR_DATE` and friends, and the test repo sets
`user.name`, `user.email`, `core.autocrlf` and the default branch explicitly. A test that depends on the
machine's git configuration passes locally and fails in CI.

## Run it

```
python 04-age-and-author/main.py
```

## Break it

- Make `attribute` blame the whole file for every item instead of `-L` lines: correct but slower; time it on a big repo.
- Have carol re-indent alice's line without `-w` in `blame_lines` and see the author change.
