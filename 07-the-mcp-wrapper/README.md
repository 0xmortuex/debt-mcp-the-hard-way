# 7. The MCP wrapper

[`debtlite/server.py`](debtlite/server.py) exposes two tools, `list_todos` and `stale_todos`, with the
`MCPServer` class from the `mcp>=2` SDK. The analysis is already written; this chapter is about the boundary.

## Tools are an API for a model

```python
@mcp.tool()
def list_todos(repo: str | None = None, older_than_days: int = 0, limit: int = 50) -> dict[str, Any]:
    """List TODO/FIXME/HACK/XXX/BUG comments oldest first with author and age in days (git blame)."""
```

The docstring is the description the model sees, the signature is the schema. Good descriptions say what you get back and
what the parameters mean; defaults mean a model can call the tool with `{}` and succeed. `limit` exists because
a repo can have 5,000 markers and a model's context cannot.

## Errors the model can act on

With `mcp>=2`, the client sees the message of a `ToolError` and nothing else; any other exception becomes a
generic "Error executing tool". So expected failures are converted at the boundary:

```python
except RuntimeError as e:
    raise ToolError(str(e)) from e
```

"git ls-files failed: fatal: not a git repository" tells the model (and the user) what to fix. A bug in your own code should
*not* be converted: it should stay loud.

## The sandbox

The model chooses arguments, so arguments are untrusted. `_resolve` joins the requested `repo` onto the allowed root,
resolves symlinks and `..` with `os.path.realpath`, and refuses anything that is not inside:

```python
if target != ROOT and not target.startswith(ROOT + os.sep):
    raise ToolError(...)
```

The `+ os.sep` matters: without it `/work/proj-secrets` would pass a prefix test against `/work/proj`.
Everything the server reads comes from a directory the *user* named when they configured it.

## Testing over real stdio

`main.py` starts the server as a subprocess (`python -m debtlite.server`), speaks MCP to it with the SDK's client, and
checks: the tool list, exact ages from the scripted repo (clock pinned with `DEBTLITE_NOW`), the `older_than_days`
filter, `limit`, the sandbox rejecting `..`, and the readable error outside a git repository. Testing the wrapper
with direct function calls would miss schema, serialisation and error-visibility bugs; those only show up over the wire.

## Run it

```
python 07-the-mcp-wrapper/main.py
```

(The "Tool ... failed" lines it prints are the server logging the two errors the test provoked on purpose.)

## What the real debt-mcp adds

`debtlite` is about 500 lines; the real server is the same architecture with more of everything:

- 27 language families (raw strings, regex literals, nested comments, Lua long brackets, Ruby `=begin`, C# verbatim strings...).
- A `--dir` option (repeatable) and symlink/submodule/binary/minified/lockfile handling.
- Shallow-clone warnings, mailmap, parallel blame, caps for huge repositories.
- `todo_history` (blame with copy detection plus `git log -S` to find when the *text* first appeared) and
  `hotspot_debt` (debt multiplied by churn from `git log --numstat`).
- A test suite that asserts the repository is byte-identical after every tool runs.

Where to go next: read `scan.py` in debt-mcp, then pick a language you use and add a false-positive case to the
corpus that breaks it.
