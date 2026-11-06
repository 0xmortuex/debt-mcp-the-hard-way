"""Chapter 5: old markers in busy files vs dead files."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import stale as st  # noqa: E402
from debtlite.testrepo import TestRepo, epoch  # noqa: E402

NOW = epoch("2024-06-01T00:00:00")

repo = TestRepo()
try:
    for name in ("hot.py", "cool.py", "dead.py"):
        repo.write(name, f"# TODO: old marker in {name}\nx = 0\n")
    repo.write("young.py", "x = 0\n")
    repo.commit("init", "Alice A", "a@example.com", "2023-01-01T00:00:00")
    repo.write("hot.py", "# TODO: old marker in hot.py\nx = 1\n")
    repo.commit("h1", "Bob B", "b@example.com", "2024-04-20T00:00:00")
    repo.write("hot.py", "# TODO: old marker in hot.py\nx = 2\n")
    repo.write("cool.py", "# TODO: old marker in cool.py\nx = 1\n")
    repo.commit("h2", "Bob B", "b@example.com", "2024-05-10T00:00:00")
    repo.write("young.py", "x = 1\n# TODO: fresh\n")
    repo.commit("young", "Bob B", "b@example.com", "2024-05-25T00:00:00")

    buckets = st.stale(repo.path, NOW, older_than_days=180, window_days=90, min_commits=2)
    summary = {k: [i.path for i in v] for k, v in buckets.items()}
    print(summary)
    assert summary == {"hot": ["hot.py"], "cooling": ["cool.py"], "dead": ["dead.py"]}
    # young.py's TODO is only 7 days old: not stale at all
    assert all("young.py" not in v for v in summary.values())
finally:
    repo.close()

print("chapter 5 ok: hot / cooling / dead")
