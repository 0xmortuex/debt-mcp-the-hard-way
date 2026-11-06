# 1. Comments, not grep

The obvious scanner is `grep -rn TODO`. It is wrong in three ways:

```python
x = "TODO: this is data"        # a string, not a comment
url = "http://example.com/#TODO"  # a URL
todos_list = []                 # an identifier
```

All three match `TODO`. Worse, comment syntax depends on context: `//` starts a comment in C, but inside
`"http://example.com"` it is part of a string; `#` starts a comment in shell, but `$#` is the argument count.
The only reliable fix is to walk the file once and keep track of *where you are*.

## The tokenizer

[`debtlite/tokenizer.py`](debtlite/tokenizer.py) is a loop over the characters of the file. At each position it
checks, in this order:

1. **Triple-quoted strings** (Python): skip to the closing triple. Everything inside is data.
2. **Block comments** (`/* ... */`, SQL too): record one entry *per physical line*, because the marker rules in
   chapter 2 work line by line.
3. **Line comments** (`//`, `#`, `--`): record the rest of the line. Shell and YAML add one rule: `#` only starts a
   comment after whitespace (`ws_before_line`), which is why `$#` is safe.
4. **Ordinary strings** (`"` and `'`): skip to the matching quote, honouring backslash escapes.

The order matters: comments are checked before strings, so an apostrophe *inside a comment* (`# don't`) never
opens a string.

Two small decisions keep it robust:

- **A quote with no partner on its line is just a character.** English apostrophes, Rust lifetimes (`'a`) and
  C++ digit separators (`1'000`) would otherwise swallow the rest of the file. The code scans to the end of the
  line for a closing quote and only skips the string if it finds one.
- **CRLF is normalised first** (`\r\n` to `\n`), so `\r` never leaks into comment text and line numbers match what
  git reports.

Languages are data, not code: a `Lang` is just the list of line openers, block pairs and triple quotes. Adding
Lua or Rust is a few lines. (The real server also handles raw strings, JavaScript regex literals, nested block
comments and more; see `scan.py` in debt-mcp.)

## Run it

```
python 01-comments-not-grep/main.py
```

`main.py` asserts that real comments are found in Python, C, SQL and shell, that eight look-alikes produce
nothing, and that CRLF, an apostrophe, an unterminated `/*` and a 200,000-character line do not break anything.

## Break it

- Delete the `ws_before_line` check and watch `echo $#` become a comment.
- Move step 4 (strings) above step 3 (line comments): `# don't` now opens a string that eats the next line.
- Remove the "no partner on its line" check and feed it `it's fine # real comment`.

## Limits

No heredocs, no JavaScript regex literals, no template literal interpolation. A tokenizer that handles every corner
of every language is a parser; this one is deliberately *conservative*: when unsure it treats a character as plain
text, which can cost a missed marker but should not invent one.
