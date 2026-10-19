#!/usr/bin/env python3
"""Check every source_excerpt in data/resources/candidates/*.json.

Static checks (no network): minimum length, no excerpt ending in "如下：" (a bare
lead-in carries no condition), no duplicate (same source_url + same excerpt) inside one
file (error). The same source_url + excerpt in two different files is printed as a
WARNING (shared provisions are sometimes legitimate; each must be justified in review).
Live check: the excerpt appears verbatim (whitespace-insensitive) in the text of its
source_url. Exit 0 only if everything passes.
Usage: verify_excerpts.py [--static] [files...]"""
import glob, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fetch_text import fetch, norm

MIN_LEN = 8  # normalized characters
args = [a for a in sys.argv[1:] if a != "--static"]
static_only = "--static" in sys.argv
files = args or sorted(glob.glob("data/resources/candidates/*.json"))
cache, bad, seen, warns = {}, 0, {}, []
def problem(msg):
    global bad; bad += 1; print(msg)
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    items = list(d.get("eligibility", [])) + list(d.get("exclusions_cumulation", []))
    if isinstance(d.get("household_calculation_basis"), dict):
        items.append(d["household_calculation_basis"])
    for item in items:
        ex, url = item.get("source_excerpt", ""), item.get("source_url") or d["source_url"]
        if not ex and item.get("value") == "未知":
            continue
        n = norm(ex)
        if len(n) < MIN_LEN:
            problem(f"TOO-SHORT {f}: {ex!r}")
        if ex.rstrip().endswith("如下："):
            problem(f"LEAD-IN-ONLY {f}: {ex[:40]!r}")
        key = (url, n)
        if key in seen:
            if seen[key] == f:
                problem(f"DUPLICATE-IN-FILE {f}: {ex[:40]!r}")
            else:
                warns.append(f"CROSS-FILE-DUPLICATE {f} and {seen[key]}: {ex[:40]!r}")
        seen[key] = f
        if static_only:
            continue
        try:
            cache.setdefault(url, norm(fetch(url)))
        except Exception as e:
            problem(f"FETCH-FAIL {f} {url} {e}"); continue
        if n not in cache[url]:
            problem(f"MISMATCH {f}: {ex[:40]}…")
for w in warns: print("WARN", w)
print(f"{len(warns)} cross-file duplicate warning(s)")
print("OK" if not bad else f"{bad} problem(s)")
sys.exit(1 if bad else 0)
