# 2. Marker parsing

Chapter 1 gives us comment lines. Now: which of them are *markers*?

## One rule that removes almost every false positive

> A marker counts only as the **first word** of a comment line.

```python
# TODO: fix this            -> marker
# see the TODO list         -> prose, not a marker
# TODOS are tracked in jira -> prose
```

[`debtlite/markers.py`](debtlite/markers.py) first skips the decoration that can precede the word (`///`, ` * `,
`# `, `-- `), then requires the marker at that position, followed by something that is not a word character:

```python
re.compile("(TODO|FIXME|...)(?![A-Za-z0-9_])")
```

`(?![A-Za-z0-9_])` is the word boundary. `TODOS` and `TODO_LIST` fail it; `TODO:` and `TODO(` pass. Matching is
case-sensitive on purpose: `todo` in lower case is almost always an ordinary word.

## Annotations

After the marker there may be an annotation in brackets, and the real world uses both styles:

| Text | marker | author | tickets |
|---|---|---|---|
| `TODO(alice): handle EOF` | TODO | alice | |
| `FIXME[JIRA-9] broken` | FIXME | | JIRA-9 |
| `TODO(bob, #123): both` | TODO | bob | #123 |
| `HACK see #45 and PROJ-7` | HACK | | #45, PROJ-7 |

Each comma-separated part of the bracket is a ticket if it matches the ticket pattern
(`ABC-123` or `#123`), otherwise it is an author. The ticket pattern is also run over the rest of the text, so
`# TODO: see #45` counts as ticketed. This split into *ticketed* and *orphan* markers is one of the most
useful numbers in the final summary.

## The false-positive corpus

`main.py` has a list of nasty inputs that must produce nothing. Keep one of these for every false positive you meet
in the wild: it is cheap insurance, and it is how the real server's tests are organised. Note that identifiers like
`todos_list = []` never even reach the parser: chapter 1 already decided they are not comments.

## Run it

```
python 02-marker-parsing/main.py
```

## Break it

- Remove the `(?![A-Za-z0-9_])` lookahead: `# TODOS are tracked in jira` becomes a TODO.
- Allow the marker anywhere in the comment: "see the TODO list" starts failing the corpus.
