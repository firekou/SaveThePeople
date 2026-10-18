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
    if not re.match(r"^(C-[0-9]{3}|L-[A-Za-z0-9]+-[0-9]{3}|P-[0-9]{3})$", str(d.get("resource_id", ""))): err(f, "bad id")
    for k in ("regions", "need_categories", "eligibility", "exclusions_cumulation", "documents", "uncertainty_notes"):
        if k in d and not isinstance(d[k], list): err(f, f"{k} must be an array")
    for k in ("name", "provider", "service_content", "validity_period", "application_deadline", "application_method", "contact", "version"):
        if k in d and not isinstance(d[k], str): err(f, f"{k} must be a string")
    if isinstance(d.get("documents"), list) and any(not isinstance(x, str) for x in d["documents"]): err(f, "documents items must be strings")
    if not isinstance(d.get("household_calculation_basis"), dict): err(f, "household_calculation_basis must be an object")
    if d.get("level") not in P["level"]["enum"]: err(f, "bad level")
    if d.get("status") not in ("候選", "暫停"): err(f, "status must be 候選 or 暫停 in this batch (已查核 requires P1-4 human check)")
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
