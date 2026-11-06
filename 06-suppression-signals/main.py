"""Chapter 6: suppressions, long files and commented-out code, with no git."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debtlite import signals as sg  # noqa: E402
from debtlite import tokenizer as tk  # noqa: E402

PY = tk.PYTHON
TS = tk.C_LIKE

# --- suppressions: counted in comments only ---------------------------------------
py = "import x  # noqa: F401\ny: int = 'a'  # type: ignore[assignment]\ns = '# noqa'\nz = 1  # pylint: disable=C0103\n"
assert dict(sg.count_suppressions(py, PY)) == {"noqa": 1, "type: ignore": 1, "pylint: disable": 1}  # the string does not count

ts = "// @ts-ignore\nlet a = 1;\n/* eslint-disable no-console */\nconst s = '// @ts-ignore';\n"
assert dict(sg.count_suppressions(ts, TS)) == {"@ts-ignore": 1, "eslint-disable": 1}

# --- long files and long functions --------------------------------------------------
big = "def huge():\n" + "    x = 1\n" * 120 + "\ndef small():\n    return 1\n"
assert sg.long_file(big, limit=100) == 124
assert sg.long_file("x = 1\n", limit=100) is None
assert sg.longest_function(big) == ("huge", 121)

# --- commented-out code vs prose -----------------------------------------------------
dead_code = "# def old():\n#     x = compute(1)\n#     return x\nreal = 1\n"
assert sg.commented_out_blocks(dead_code, PY) == [(1, 3)]
prose = "# This explains the scheduler.\n# It walks the queue in order.\n# Higher priority jobs run first.\n"
assert sg.commented_out_blocks(prose, PY) == []

print("chapter 6 ok: suppressions, long functions, commented-out code")
