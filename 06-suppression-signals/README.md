# 6. Suppression signals

Not all debt is written as TODO. Every `# noqa`, `# type: ignore` or `// @ts-ignore` says "the tool found a
problem and I told it to be quiet". Counting them by directory shows where the type system or the linter has
been switched off. [`debtlite/signals.py`](debtlite/signals.py) has three cheap signals, none of which needs git.

## 1. Suppressions, counted in comments only

```python
count_suppressions(text, lang)   # {"noqa": 1, "type: ignore": 1, ...}
```

It reuses the chapter 1 tokenizer, so the string `s = '# noqa'` is not a suppression. This is the payoff for
having a real comment scanner: every signal built on top of it inherits the false-positive protection.

## 2. Long files and functions

`long_file` counts newlines. `longest_function` is deliberately naive: for Python, a function runs from its `def` to the
next non-blank line indented no deeper than the `def`. It is a *line counter*, not a parser, and good enough to
say "this function is 400 lines". (The real server also does brace languages by counting braces on a copy of
the source where strings and comments have been blanked out, so a `}` in a string cannot end a function.)

## 3. Commented-out code

A run of three or more consecutive comment lines, where at least 60% look like code (end with `;` or `{`, start with
`def`/`class`/`return`, contain an assignment or a call). Prose such as "This explains the scheduler." does not match.
It is a heuristic and the output says so; the run length and the ratio are the two knobs.

## Run it

```
python 06-suppression-signals/main.py
```

## Break it

- Make `count_suppressions` scan raw lines instead of comment text and watch the string case fail.
- Lower the commented-out ratio to 0.2 and run it on your own repo: how much prose gets flagged?
