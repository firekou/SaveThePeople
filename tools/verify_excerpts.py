#!/usr/bin/env python3
"""Check that every source_excerpt in data/resources/candidates/*.json appears
verbatim (whitespace-insensitive) in the live text of its source_url.
Exit 0 only if all pass. Usage: verify_excerpts.py [files...]"""
import glob, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fetch_text import fetch, norm

files = sys.argv[1:] or sorted(glob.glob("data/resources/candidates/*.json"))
cache, bad = {}, 0
for f in files:
    d = json.load(open(f))
    items = list(d.get("eligibility", [])) + list(d.get("exclusions_cumulation", []))
    if isinstance(d.get("household_calculation_basis"), dict):
        items.append(d["household_calculation_basis"])
    for item in items:
        ex, url = item.get("source_excerpt", ""), item.get("source_url") or d["source_url"]
        if not ex and item.get("value") == "未知":
            continue
        try:
            cache.setdefault(url, norm(fetch(url)))
        except Exception as e:
            print(f"FETCH-FAIL {f} {url} {e}"); bad += 1; continue
        if norm(ex) not in cache[url]:
            print(f"MISMATCH {f}: {ex[:40]}…"); bad += 1
print("OK" if not bad else f"{bad} problem(s)")
sys.exit(1 if bad else 0)
