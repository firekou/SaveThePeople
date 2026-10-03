#!/usr/bin/env python3
"""規格驗證用的參考檢查程式（非產品程式碼）。

依 RESOURCE_AND_ELIGIBILITY_ENGINE.md §5–§7 的最小子集，以合成資源與家庭計算
初篩結果，並與 expected_assessments.json 比對。只使用 Python 標準函式庫。

用法：python3 docs/platform/examples/check_examples.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
LEVEL = {"C0": 0, "C1": 1, "C2": 2, "C3": 3}
PERSON_ATTR_CONFIRMATION = "C1"  # 年齡、就學、同住等成員屬性視為自述


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def region_matches(code, allowed, regions):
    while code:
        if code in allowed:
            return True
        code = regions.get(code, {}).get("parent")
    return False


def scope_members(household, scope):
    inc = scope["member_inclusion"]
    out = []
    for p in household["persons"]:
        if "relation_in" in inc and p["relation_to_primary"] not in inc["relation_in"]:
            continue
        if "same_household_registration" in inc and p["same_household_registration"] != inc["same_household_registration"]:
            continue
        if "co_residing" in inc and p["co_residing"] != inc["co_residing"]:
            continue
        out.append(p)
    return out


def income_per_capita(household, scope):
    members = scope_members(household, scope)
    if not members:
        return None, "C0", 0
    total, conf = 0, 3
    for p in members:
        for item in scope["income_definition"]["items"]:
            v = p.get(item)
            if v is None or v.get("unknown"):
                return None, "C0", len(members)
            total += v["value"]
            conf = min(conf, LEVEL[v["confirmation_level"]])
    return total / len(members), f"C{conf}", len(members)


def compare(op, value, threshold):
    if op == "LTE":
        return value <= threshold
    if op == "IN":
        return value in threshold
    raise ValueError(op)


def eval_criterion(c, hh, scopes, regions):
    """回傳 (結果, 是否需人工, 衍生值)。"""
    op = c["operator"]
    min_fail = LEVEL[c.get("min_confirmation_for_fail", "C2")]
    if op == "HUMAN_JUDGMENT":
        return "HUMAN", True, None

    def fail_or_unconfirmed(conf):
        return "FAIL" if LEVEL[conf] >= min_fail else "FAIL_UNCONFIRMED"

    facts = hh["facts"]
    if op == "REGION_IN":
        f = facts.get("household.region_code", {})
        if f.get("unknown"):
            return "UNKNOWN", False, None
        ok = region_matches(f["value"], c["threshold"]["value"], regions)
        return ("PASS" if ok else fail_or_unconfirmed(f["confirmation_level"])), False, None
    if op == "NOT_RECEIVING":
        f = facts.get("household.receiving_resources", {})
        if f.get("unknown"):
            return "UNKNOWN", False, None
        hit = set(f["value"]) & set(c["threshold"]["value"])
        return ("PASS" if not hit else fail_or_unconfirmed(f["confirmation_level"])), False, None
    if op == "COUNT_MEMBERS_WHERE":
        members = scope_members(hh, scopes[c["scope_key"]])
        if not members:
            return "UNKNOWN", False, None
        where = c["threshold"]["where"]
        lo, hi = where["age_between"]
        n = sum(1 for p in members
                if lo <= p["age"] <= hi and (not where.get("in_school") or p["in_school"]))
        ok = n >= c["threshold"]["min_count"]
        return ("PASS" if ok else fail_or_unconfirmed(PERSON_ATTR_CONFIRMATION)), False, {"count": n}
    if op in ("LTE", "IN"):
        key = c["input_keys"][0]
        derived = None
        if key == "derived.income_per_capita":
            value, conf, n = income_per_capita(hh, scopes[c["scope_key"]])
            if value is None:
                return "UNKNOWN", False, None
            derived = {"members": n, "income_per_capita": round(value)}
        else:
            f = facts.get(key, {})
            if f.get("unknown") or "value" not in f:
                return "UNKNOWN", False, None
            value, conf = f["value"], f["confirmation_level"]
        threshold = c["threshold"]["value"]
        ok = compare(op, value, threshold)
        human = False
        if "value_within_5_percent_of_threshold" in c.get("requires_human_when", []):
            human = abs(value - threshold) <= threshold * 0.05
        return ("PASS" if ok else fail_or_unconfirmed(conf)), human, derived
    raise ValueError(op)


def evaluate(resource, hh, scopes, regions):
    crit = {}
    derived = {}
    human = False
    for c in resource["rule"]["criteria"]:
        r, h, d = eval_criterion(c, hh, scopes, regions)
        crit[c["criterion_id"]] = r
        human = human or h or r == "HUMAN"
        if d and "income_per_capita" in d:
            derived[c["criterion_id"]] = d
    vals = set(crit.values())
    out = {"criteria": crit}
    if "FAIL" in vals:
        out.update(result="LIKELY_INELIGIBLE", unconfirmed=False)
    elif "FAIL_UNCONFIRMED" in vals:
        out.update(result="LIKELY_INELIGIBLE", unconfirmed=True)
    elif "UNKNOWN" in vals:
        out["result"] = "INSUFFICIENT_DATA"
    else:
        out["result"] = "LIKELY_ELIGIBLE"
    flags = []
    if human:
        flags.append("HUMAN_CHECK")
    if resource["version"].get("capacity_status") == "FULL":
        flags.append("CAPACITY_FULL")
    receiving = hh["facts"].get("household.receiving_resources", {}).get("value") or []
    if resource["resource_key"] in receiving:
        flags.append("ALREADY_RECEIVING")
    if flags:
        out["flags"] = flags
    if derived:
        out["derived"] = derived
    return out


def recommendable(resource, evaluation_date):
    v = resource["version"]
    if v["status"] != "PUBLISHED" or v["verification_level"] not in ("V2", "V3"):
        return False
    return not (v.get("effective_to") and v["effective_to"] < evaluation_date)


def main():
    res = load("synthetic_resources.json")
    hhs = load("synthetic_households.json")
    exp = load("expected_assessments.json")
    assert res["is_synthetic"] and hhs["is_synthetic"], "examples must be synthetic"
    scopes = {s["scope_key"]: s for s in res["household_scopes"]}
    source_ids = {s["id"] for s in res["sources"]}
    errors = []

    # 參照完整性：每個資源有來源、每個條件有 source_ref、scope 存在
    for r in res["resources"]:
        for sid in r["version"]["source_ids"]:
            if sid not in source_ids:
                errors.append(f"{r['resource_key']}: unknown source {sid}")
        for c in r["rule"]["criteria"]:
            if not c.get("source_ref"):
                errors.append(f"{r['resource_key']}.{c['criterion_id']}: missing source_ref")
            if c.get("scope_key") and c["scope_key"] not in scopes:
                errors.append(f"{r['resource_key']}.{c['criterion_id']}: unknown scope {c['scope_key']}")

    date = exp["evaluation_date"]
    for hh in hhs["households"]:
        for r in res["resources"]:
            key = r["resource_key"]
            if not recommendable(r, date):
                if key in exp["expected"].get(hh["id"], {}):
                    errors.append(f"{hh['id']}/{key}: non-recommendable resource has expectation")
                continue
            got = evaluate(r, hh, scopes, res["regions"])
            want = exp["expected"][hh["id"]][key]
            for field in ("result", "criteria", "flags", "derived"):
                if field == "derived" and field not in want:
                    continue  # 只在預期值列出計算過程時比對
                if want.get(field) != got.get(field):
                    errors.append(f"{hh['id']}/{key} {field}: want {want.get(field)} got {got.get(field)}")
            if "unconfirmed" in want and want["unconfirmed"] != got.get("unconfirmed"):
                errors.append(f"{hh['id']}/{key} unconfirmed: want {want['unconfirmed']} got {got.get('unconfirmed')}")
            print(f"{hh['id']} {key:20s} {got['result']:18s} {got['criteria']} {got.get('flags', '')}")

    if errors:
        print("\nFAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("\nOK: all synthetic expectations match")


if __name__ == "__main__":
    main()
