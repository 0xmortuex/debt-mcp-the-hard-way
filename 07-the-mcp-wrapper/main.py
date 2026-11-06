"""Chapter 7: launch the real MCP server over stdio and use it."""

import json
import os
import sys

import anyio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from debtlite.testrepo import epoch, story  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def run(repo_path: str) -> None:
    env = dict(os.environ, DEBTLITE_DIR=repo_path, DEBTLITE_NOW=str(epoch("2024-06-01T00:00:00")), PYTHONPATH=ROOT)
    params = StdioServerParameters(command=sys.executable, args=["-m", "debtlite.server"], env=env)
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        assert names == {"list_todos", "stale_todos"}, names

        res = await session.call_tool("list_todos", {})
        assert not res.is_error
        data = json.loads(res.content[0].text)
        assert data["matched"] == 4
        first = data["items"][0]
        assert (first["where"], first["author"], first["age_days"]) == ("app.py:5", "Alice A", 507), first

        res = await session.call_tool("list_todos", {"older_than_days": 400, "limit": 1})
        data = json.loads(res.content[0].text)
        assert data["matched"] == 3 and len(data["items"]) == 1

        # the sandbox: the model cannot wander outside the allowed directory
        res = await session.call_tool("list_todos", {"repo": ".."})
        assert res.is_error and "outside the allowed directory" in res.content[0].text

        res = await session.call_tool("stale_todos", {})
        data = json.loads(res.content[0].text)
        assert [i["where"] for i in data["dead"]] == ["app.py:5", "app.py:7", "util.js:1", "app.py:9"], data


repo = story()
try:
    anyio.run(run, repo.path)
finally:
    repo.close()

# Outside a git repository the failure must be readable, not a traceback.
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as plain:
    open(os.path.join(plain, "a.py"), "w", encoding="utf-8").write("# TODO: x\n")

    async def not_a_repo() -> None:
        env = dict(os.environ, DEBTLITE_DIR=plain, PYTHONPATH=ROOT)
        params = StdioServerParameters(command=sys.executable, args=["-m", "debtlite.server"], env=env)
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            res = await session.call_tool("list_todos", {})
            assert res.is_error and "git" in res.content[0].text, res.content

    anyio.run(not_a_repo)

print("chapter 7 ok: MCP tools, sandbox and errors work over stdio")
