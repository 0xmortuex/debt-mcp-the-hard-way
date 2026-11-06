# 5. Stale: hot or dead

An old TODO is a fact. What you *do* about it depends on where it lives.

- **Hot**: the file keeps changing. People walk past this marker every week and nobody fixed it. Fix it or delete it.
- **Cooling**: a little recent activity.
- **Dead**: the file has not been touched in months. The marker is probably a forgotten note. Deleting or ignoring
  it is cheap; do not spend a sprint on it.

## Measuring activity

[`debtlite/stale.py`](debtlite/stale.py) asks git how many commits touched each file in a window:

```
git log --since=<epoch> --no-renames --name-only --format=@@%H
```

`--name-only` prints the changed paths after each commit; the `@@<sha>` header lines are skipped, and every other non-empty line is
one file in one commit. A `Counter` does the rest.

Details:

- `--since=<epoch>` takes a Unix timestamp. We compute it from the injected `now`, so the test is deterministic
  (a relative `--since=90.days.ago` would use the real clock).
- `--no-renames` keeps every path a plain file name; a rename shows as delete plus add rather than `{a => b}`.
- A file that is not in the counter was not touched: zero commits means dead.

Then each *old enough* marker is put in a bucket:

```python
"hot" if n >= min_commits else "cooling" if n else "dead"
```

The test repo has `hot.py` (two commits in the last 90 days), `cool.py` (one), `dead.py` (none) and `young.py` (a
7-day-old marker that must not appear at all, because it is not stale yet).

## Run it

```
python 05-stale-hot-or-dead/main.py
```

## Break it

- Change the window from 90 to 400 days: `dead.py` becomes `hot.py`'s neighbour. The thresholds are policy; expose them as tool parameters.
- Count lines changed instead of commits (`--numstat`). The real server's `hotspot_debt` does, and multiplies it with the debt count.
