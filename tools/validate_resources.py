#!/usr/bin/env python3
"""Minimal stdlib validator for data/resources/candidates/*.json against schema/resource.schema.json
(required keys, enums, patterns on top-level fields, https source URL, candidate-only status)."""
import glob, json, re, sys
schema = json.load(open("schema/resource.schema.json"))
req = schema["required"]; P = schema["properties"]
bad = 0
def err(f, m):
    global bad; bad += 1; print(f"{f}: {m}")
files = sorted(glob.glob("data/resources/candidates/*.json"))
ids = set()
for f in files:
    d = json.load(open(f))
    for k in req:
        if k not in d: err(f, f"missing {k}")
    if d.get("resource_id") in ids: err(f, "duplicate id")
    ids.add(d.get("resource_id"))
    if not re.match(P["resource_id"]["pattern"], d.get("resource_id", "")): err(f, "bad id")
    if d.get("level") not in P["level"]["enum"]: err(f, "bad level")
    if d.get("status") != "候選": err(f, "status must be 候選 in this batch")
    if d.get("capacity_confirmation") != "未確認": err(f, "capacity must be 未確認")
    if not re.match(P["last_checked_date"]["pattern"], d.get("last_checked_date", "")): err(f, "bad check date")
    if not str(d.get("source_url", "")).startswith("https://"): err(f, "source_url not https")
    for c in d.get("eligibility", []):
        for k in P["eligibility"]["items"]["required"]:
            if k not in c: err(f, f"eligibility {c.get('condition_id')} missing {k}")
        if c.get("value") == "已摘錄" and not c.get("source_excerpt"): err(f, "已摘錄 w/o excerpt")
    if not d.get("eligibility"): err(f, "no eligibility entries")
    for nc in d.get("need_categories", []):
        if nc not in P["need_categories"]["items"]["enum"]: err(f, f"bad need category {nc}")
print(f"{len(files)} files, " + ("OK" if not bad else f"{bad} problem(s)"))
sys.exit(1 if bad else 0)
