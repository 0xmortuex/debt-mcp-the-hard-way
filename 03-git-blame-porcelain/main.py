"""Chapter 3: parse `git blame --porcelain` on a real scripted repository."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import gitblame as gb  # noqa: E402
from debtlite.testrepo import epoch, story  # noqa: E402

repo = story()
try:
    # app.py at HEAD: line 5 is alice's TODO (carol inserted 2 lines above it), line 9 is bob's BUG
    b = gb.blame_lines(repo.path, "app.py", [5, 9])
    assert b[5].author == "Alice A" and b[5].time == epoch("2023-01-10T12:00:00"), b[5]
    assert b[9].author == "Bob B" and b[9].time == epoch("2023-06-15T08:30:00"), b[9]
    assert b[5].summary == "initial"
    print("line 5 ->", b[5].author, "(moved by carol, still alice's)")

    # an uncommitted edit shows up as the all-zero sha
    repo.write("app.py", open(os.path.join(repo.path, "app.py"), encoding="utf-8").read() + "# FIXME: unsaved\n")
    b2 = gb.blame_lines(repo.path, "app.py", [12])
    assert b2[12].author == "uncommitted" and b2[12].time is None

    # .gitignore is honoured and untracked files are listed
    repo.write(".gitignore", "secret.py\n")
    repo.write("secret.py", "# TODO: ignored\n")
    repo.write("fresh.py", "# TODO: untracked\n")
    files = gb.list_files(repo.path)
    assert "fresh.py" in files and "secret.py" not in files, files

    # git errors become a readable exception, not a crash
    try:
        gb.git(repo.path, "blame", "--porcelain", "--", "does-not-exist.py")
    except RuntimeError as e:
        assert "git blame failed" in str(e)
    else:
        raise AssertionError("expected a failure")
finally:
    repo.close()

print("chapter 3 ok: porcelain parsed, uncommitted and ignored files handled")
