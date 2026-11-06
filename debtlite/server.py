"""Chapter 7: wrap the analyses as MCP tools."""

from __future__ import annotations

import os
import time
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import attribution as at
from . import stale as st

mcp = MCPServer("debtlite", instructions="Find TODO/FIXME markers and say how old they are and who added them.")
ROOT = os.path.realpath(os.environ.get("DEBTLITE_DIR", os.getcwd()))
NOW = int(os.environ["DEBTLITE_NOW"]) if "DEBTLITE_NOW" in os.environ else None  # tests pin the clock


def _resolve(repo: str | None) -> str:
    """The sandbox: whatever the model asks for must stay inside ROOT."""
    target = os.path.realpath(os.path.join(ROOT, repo or "."))
    if target != ROOT and not target.startswith(ROOT + os.sep):
        raise ToolError(f"{repo!r} is outside the allowed directory {ROOT}")
    return target


def _item(it: at.Item, now: int) -> dict[str, Any]:
    return {
        "where": f"{it.path}:{it.marker.line}",
        "marker": it.marker.marker,
        "text": it.marker.text,
        "tickets": it.marker.tickets,
        "author": it.author,
        "age_days": it.age_days(now),
    }


@mcp.tool()
def list_todos(repo: str | None = None, older_than_days: int = 0, limit: int = 50) -> dict[str, Any]:
    """List TODO/FIXME/HACK/XXX/BUG comments oldest first with author and age in days (git blame)."""
    root = _resolve(repo)
    try:
        items = at.oldest_first(at.attribute(root, at.scan(root)))
    except RuntimeError as e:  # expected failure -> a message the model can act on
        raise ToolError(str(e)) from e
    now = NOW or int(time.time())
    if older_than_days:
        items = [i for i in items if (i.age_days(now) or 0) >= older_than_days]
    return {"matched": len(items), "items": [_item(i, now) for i in items[:limit]]}


@mcp.tool()
def stale_todos(repo: str | None = None, older_than_days: int = 180, window_days: int = 90) -> dict[str, Any]:
    """Old markers split into hot (file still edited), cooling, and dead (file untouched)."""
    root = _resolve(repo)
    now = NOW or int(time.time())
    try:
        b = st.stale(root, now, older_than_days, window_days)
    except RuntimeError as e:
        raise ToolError(str(e)) from e
    return {k: [_item(i, now) for i in v] for k, v in b.items()}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
