"""Chapter 4: scan + blame = how old, and who."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import attribution as at  # noqa: E402
from debtlite.testrepo import epoch, story  # noqa: E402

NOW = epoch("2024-06-01T00:00:00")  # a pinned clock: ages are exact, not "about a year"

repo = story()
try:
    items = at.oldest_first(at.attribute(repo.path, at.scan(repo.path)))
    got = [(i.path, i.marker.line, i.marker.marker, i.author, i.age_days(NOW)) for i in items]
    print("\n".join(map(str, got)))
    assert got == [
        ("app.py", 5, "TODO", "Alice A", 507),   # 2023-01-10 12:00 -> 2024-06-01
        ("app.py", 7, "HACK", "Alice A", 507),
        ("util.js", 1, "FIXME", "Alice A", 507),
        ("app.py", 9, "BUG", "Bob B", 351),      # 2023-06-15 08:30
    ], got
    # the 'TODO' inside the string literal on app.py line 11 is NOT reported
    assert not any(i.marker.line == 11 for i in items)
    assert [i.marker.tickets for i in items if i.path == "util.js"] == [["JIRA-9"]]

    # a brand-new file has no history: "uncommitted", sorted last, no age
    repo.write("fresh.py", "# TODO: untracked\n")
    items = at.oldest_first(at.attribute(repo.path, at.scan(repo.path)))
    assert items[-1].path == "fresh.py" and items[-1].author == "uncommitted" and items[-1].age_days(NOW) is None
finally:
    repo.close()

print("chapter 4 ok: exact ages and authors")
