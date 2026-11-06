"""A scripted git repository with exact authors and dates, shared by every chapter.

Dates and identities are set through environment variables, so the history is
identical on every machine and the chapters can assert exact ages.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import datetime, timezone


def epoch(iso: str) -> int:
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp())


class TestRepo:
    __test__ = False  # not a pytest class

    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.path)
        self.git("init", "-q")
        # Independent of the machine's identity, autocrlf and default branch.
        for k, v in (("user.name", "init"), ("user.email", "init@example.com"), ("core.autocrlf", "false")):
            self.git("config", k, v)

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        full = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        full.update(env or {})
        p = subprocess.run(["git", "-c", "init.defaultBranch=main", *args], cwd=self.path, env=full, capture_output=True)
        if p.returncode:
            raise RuntimeError(p.stderr.decode("utf-8", "replace"))
        return p.stdout.decode("utf-8", "replace")

    def write(self, rel: str, content: str) -> None:
        full = os.path.join(self.path, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:  # bytes: no newline translation on Windows
            fh.write(content.encode("utf-8"))

    def commit(self, msg: str, name: str, email: str, when: str) -> None:
        self.git("add", "-A")
        stamp = when + "+0000"
        self.git(
            "commit", "-q", "-m", msg,
            env={
                "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": stamp,
                "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": stamp,
            },
        )  # fmt: skip

    def close(self) -> None:
        self.tmp.cleanup()


def story() -> TestRepo:
    """The history used by chapters 3-7.

    2023-01-10 alice: app.py with a TODO(alice) and a HACK; util.js with FIXME[JIRA-9]
    2023-06-15 bob:   adds a BUG line to app.py
    2024-03-01 carol: inserts imports ABOVE alice's TODO (the line moves, the author must not change)
    """
    r = TestRepo()
    r.write("app.py", "import os\n\n# TODO(alice): early marker\nx = 1\n# HACK: quick fix\ny = 2\n")
    r.write("util.js", "// FIXME[JIRA-9] broken on safari\nfunction f() {}\n")
    r.commit("initial", "Alice A", "alice@example.com", "2023-01-10T12:00:00")
    r.write("app.py", "import os\n\n# TODO(alice): early marker\nx = 1\n# HACK: quick fix\ny = 2\n# BUG: off by one\nz = 3\n")
    r.commit("bob adds a bug", "Bob B", "bob@example.com", "2023-06-15T08:30:00")
    r.write(
        "app.py",
        "import os\nimport sys\nimport re\n\n# TODO(alice): early marker\nx = 1\n# HACK: quick fix\ny = 2\n"
        "# BUG: off by one\nz = 3\ns = 'TODO: in a string'\n",
    )
    r.commit("carol shifts lines", "Carol C", "carol@example.com", "2024-03-01T00:00:00")
    return r
