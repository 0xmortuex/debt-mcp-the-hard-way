"""Run every chapter's main.py for real, the way CI does.

Each chapter builds scripted git repositories and checks its own results with
assert, so a chapter whose code drifts from what its README claims fails here.

Usage: python verify.py            # all chapters
       python verify.py 03 05      # just these
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main(argv: list[str]) -> int:
    if shutil.which("git") is None:
        print("git not found on PATH - install git first")
        return 2
    chapters = sorted(d for d in glob.glob(os.path.join(ROOT, "[0-9][0-9]-*")) if os.path.isdir(d))
    if argv:
        chapters = [c for c in chapters if os.path.basename(c)[:2] in argv]
    # Windows CI consoles are cp1252; force UTF-8 for the children and ignore the machine's git config.
    env = dict(os.environ, PYTHONIOENCODING="utf-8", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    failed = []
    for ch in chapters:
        name = os.path.basename(ch)
        p = subprocess.run([sys.executable, os.path.join(ch, "main.py")], env=env, capture_output=True, timeout=300)
        out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
        status = "ok" if p.returncode == 0 else "FAILED"
        print(f"{name}: {status}")
        if p.returncode:
            failed.append(name)
            print(out)
    print(f"\n{len(chapters) - len(failed)}/{len(chapters)} chapters verified")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
