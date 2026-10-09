#!/usr/bin/env python3
"""檢查工具本身的反例測試（只使用標準函式庫）。

這些測試餵入「刻意違規」的資料，確認檢查工具會抓到。它們驗證的是**文件檢查工具**，
不是產品行為；產品授權行為測試（T-19、T-32～T-35、T-50、T-51）待 WP-08 實作後才存在。

用法：python3 docs/platform/tools/test_checks.py   （任何一項反例沒被抓到即 exit 1）
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_permissions as GP  # noqa: E402
import schema_lite as SL  # noqa: E402
import citation_check as CC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FAILS = []
COUNT = [0]


def expect(label, problems, needle):
    COUNT[0] += 1
    if not any(needle in p for p in problems):
        FAILS.append(f"{label}: expected a problem containing {needle!r}; got {problems[:3]}")


def expect_clean(label, problems):
    COUNT[0] += 1
    if problems:
        FAILS.append(f"{label}: expected no problems; got {problems[:3]}")


def base():
    return GP.load(), json.loads((ROOT / "state_machines.json").read_text(encoding="utf-8"))["machines"]


def test_permission_counterexamples():
    d, m = base()
    expect_clean("baseline permissions", GP.policy_problems(d, m))

    # F-03 具體矛盾 1：P11 把轉介清單給 R5
    x = copy.deepcopy(d)
    for p in x["pages"]:
        if p["page"] == "P11":
            for s in p["sections"]:
                if s["class"] == "referral":
                    s["grants"].append("R5·INT")
    expect("P11 referral list granted to R5", GP.policy_problems(x, m), "R5 must not see case referrals")

    # 把容量資料與轉介清單混回同一區段（舊 P11 寫法）
    x = copy.deepcopy(d)
    x["pages"] = [dict(p) for p in x["pages"]]
    for p in x["pages"]:
        if p["page"] == "P11":
            p["sections"] = [{"label": "混合", "class": "referral", "action": "V",
                              "grants": ["R3·ASG", "R4·SITE-REV", "R5·INT", "R6·REF"], "note": ""}]
    probs = GP.policy_problems(x, m)
    expect("P11 mixed section", probs, "R5 must not see case referrals")
    expect("P11 mixed section (matrix)", probs, "not covered by the matrix")

    # 2：驗證 API 允許「另一位 R3」但矩陣只給 ASG
    x = copy.deepcopy(d)
    x["matrix"]["outcome_event"]["R3"] = [e for e in x["matrix"]["outcome_event"]["R3"] if e["scope"] != "VERIFY"]
    expect("verify API vs matrix without VERIFY", GP.policy_problems(x, m), "is not covered by the matrix")

    # 驗證 API 授權給責任人範圍（ASG）
    x = copy.deepcopy(d)
    for a in x["api"]:
        if a["endpoint"].endswith("/verify"):
            a["grants"].append("R3·ASG")
    expect("verify granted to ASG", GP.policy_problems(x, m), "must not be granted to the case owner scope")

    # VERIFY 擴大成一般個案讀取
    x = copy.deepcopy(d)
    for e in x["matrix"]["outcome_event"]["R3"]:
        if e["scope"] == "VERIFY":
            e["actions"] = "VE"
    expect("VERIFY widened to edit", GP.policy_problems(x, m), "VERIFY is only R3")
    x = copy.deepcopy(d)
    x["matrix"]["case_profile"]["R3"].append({"actions": "V", "scope": "VERIFY", "note": ""})
    expect("VERIFY on case_profile", GP.policy_problems(x, m), "VERIFY is only R3")

    # R7 一般個案讀取
    x = copy.deepcopy(d)
    x["matrix"]["case_profile"]["R7"] = [{"actions": "V", "scope": "ASG", "note": ""}]
    expect("R7 general case read", GP.policy_problems(x, m), "R7 has no general case access")
    x = copy.deepcopy(d)
    x["matrix"]["document_file"]["R7"] = [{"actions": "V", "scope": "BG", "note": ""}]
    expect("R7 document_file", GP.policy_problems(x, m), "R7 must not access document_file")

    # R9 寫入個案資料
    x = copy.deepcopy(d)
    x["matrix"]["application"]["R9"] = [{"actions": "VE", "scope": "SAMPLE", "note": ""}]
    expect("R9 edit on reviewed data", GP.policy_problems(x, m), "R9 is read-only")
    x = copy.deepcopy(d)
    x["matrix"]["case_profile"]["R9"] = [{"actions": "V", "scope": "ASG", "note": ""}]
    expect("R9 non-SAMPLE case access", GP.policy_problems(x, m), "R9 case access only via SAMPLE")

    # R6 超出 REF
    x = copy.deepcopy(d)
    x["matrix"]["safety_flags"]["R6"] = [{"actions": "V", "scope": "REF", "note": ""}]
    expect("R6 safety_flags", GP.policy_problems(x, m), "R6 may not access safety_flags")
    x = copy.deepcopy(d)
    x["matrix"]["case_profile"]["R6"] = [{"actions": "V", "scope": "ASG", "note": ""}]
    expect("R6 case scope not REF", GP.policy_problems(x, m), "role R6 may not hold scope ASG")

    # R8 超出 AGG
    x = copy.deepcopy(d)
    x["matrix"]["case_profile"]["R8"] = [{"actions": "V", "scope": "ASG", "note": ""}]
    expect("R8 case access", GP.policy_problems(x, m), "role R8 may not hold scope ASG")
    x = copy.deepcopy(d)
    x["matrix"]["aggregate_report"]["R8"] = [{"actions": "VE", "scope": "AGG", "note": ""}]
    expect("R8 edit", GP.policy_problems(x, m), "R8 is aggregate-only")

    # R5 看個案資料
    x = copy.deepcopy(d)
    x["matrix"]["referral"]["R5"] = [{"actions": "V", "scope": "ASG", "note": ""}]
    expect("R5 case data", GP.policy_problems(x, m), "R5 must not access case data")

    # API 授權超出矩陣（舊 R1 撤回、R3 文件）
    x = copy.deepcopy(d)
    x["matrix"]["consent"]["R1"] = [{"actions": "V", "scope": "OWN", "note": ""}]
    expect("revoke API beyond matrix", GP.policy_problems(x, m), "POST /api/consents/{id}/revoke")

    # 狀態機操作者在 API 無授權
    x = copy.deepcopy(d)
    x["api"] = [a for a in x["api"] if a["endpoint"] != "POST /api/assessments/{id}/retry"]
    expect("AS-03 actor without API", GP.policy_problems(x, m), "machine assessment/AS-03")


def test_doc_inventory_counterexample():
    d, _ = base()
    x = copy.deepcopy(d)
    x["api"] = [a for a in x["api"] if a["endpoint"] != "GET /api/capacity"]
    expect("API row missing in JSON", GP.doc_problems(x), "GET /api/capacity")
    x = copy.deepcopy(d)
    x["pages"] = [p for p in x["pages"] if p["page"] != "P11"]
    expect("page missing in JSON", GP.doc_problems(x), "P11")


def _res():
    return json.loads((ROOT / "examples" / "synthetic_resources.json").read_text(encoding="utf-8"))


def test_schema_counterexamples():
    res = _res()
    ver, rule = res["resources"][0]["version"], res["resources"][0]["rule"]
    sv, sr = SL.load_schema("resource_version"), SL.load_schema("eligibility_rule")
    expect_clean("baseline version", SL.validate(ver, sv))
    expect_clean("baseline rule", SL.validate(rule, sr))
    for req in ("effective_unknown", "status", "source_ids", "application_window", "verification_level"):
        x = copy.deepcopy(ver)
        del x[req]
        expect(f"version missing {req}", SL.validate(x, sv), f"missing required '{req}'")
    x = copy.deepcopy(ver); x["effective_unknown"] = "false"
    expect("effective_unknown wrong type", SL.validate(x, sv), "effective_unknown")
    x = copy.deepcopy(ver); x["surprise"] = 1
    expect("version unknown key", SL.validate(x, sv), "unknown key 'surprise'")
    x = copy.deepcopy(ver); x["status"] = "LIVE"
    expect("version bad enum", SL.validate(x, sv), "not in enum")
    x = copy.deepcopy(ver); x["recheck_started_at"] = "last week"
    expect("recheck_started_at bad date", SL.validate(x, sv), "recheck_started_at")
    x = copy.deepcopy(rule); del x["status"]
    expect("rule missing status", SL.validate(x, sr), "missing required 'status'")
    x = copy.deepcopy(rule); x["criteria"][0]["colour"] = "red"
    expect("criterion unknown key", SL.validate(x, sr), "unknown key 'colour'")
    x = copy.deepcopy(rule); x["combinator"] = "CUSTOM"; x["expression"] = {"op": "NOT", "children": ["C1"]}
    expect("expression bad op", SL.validate(x, sr), "oneOf")
    x = copy.deepcopy(rule); x["combinator"] = "CUSTOM"; x["expression"] = {"op": "ALL"}
    expect("expression without children", SL.validate(x, sr), "oneOf")
    # 結構驗證器不得默默忽略它不懂的 schema 關鍵字
    COUNT[0] += 1
    try:
        SL.validate({}, {"type": "object", "patternProperties": {}})
        FAILS.append("schema_lite silently ignored an unsupported keyword")
    except ValueError:
        pass
    # IdempotencyRecord 只存形狀；控制紀錄不得含個人內容欄位
    si, sc = SL.load_schema("idempotency_response"), SL.load_schema("control_record")
    expect_clean("idempotency shape ok", SL.validate({"status_code": 201, "resource_ref": {"type": "Application", "id": "a1"}, "shape_version": 1}, si))
    expect("idempotency stores body", SL.validate({"status_code": 201, "resource_ref": {"type": "Application", "id": "a1"}, "shape_version": 1, "body": {"name": "x"}}, si), "unknown key 'body'")
    expect("idempotency missing ref", SL.validate({"status_code": 201, "shape_version": 1}, si), "missing required 'resource_ref'")
    expect("control record with person data", SL.validate({"type": "HARD_DELETE", "table": "facts", "id": "f1", "person_name": "x"}, sc), "unknown key 'person_name'")
    # 這些 schema 只涵蓋結構：跨欄位規則（effective_unknown 與 effective_to 不一致）結構驗證器不會抓到，必須由引擎驗證處理
    x = copy.deepcopy(ver); x["effective_unknown"] = True
    expect_clean("schema alone does not catch cross-field inconsistency (documented limitation)", SL.validate(x, sv))


def test_citation_counterexamples():
    bad_pr07 = "| PR-07 | 停滯天數門檻 | 21 天 | 暫行（待與據點約定） | D-309 | §7.5 |"
    good_pr07 = bad_pr07.replace("D-309", "D-310")
    expect("PR-07 cites D-309", [m for _, m in CC.citation_problems("PRODUCT_REQUIREMENTS.md", bad_pr07)], "D-309 cited")
    expect_clean("PR-07 cites D-310", CC.citation_problems("PRODUCT_REQUIREMENTS.md", good_pr07))
    bad_d106 = "| D-106 | 排序不以金額為主；權重見引擎文件 §6.4 | 符合服務模型 | 低 |"
    expect("D-106 cites engine 6.4", [m for _, m in CC.citation_problems("DECISIONS_AND_UNKNOWNS.md", bad_d106)], "§6.4 cited")
    expect_clean("D-106 cites engine 6.6", CC.citation_problems("DECISIONS_AND_UNKNOWNS.md", bad_d106.replace("§6.4", "§6.6")))
    expect("OPS section mismatch", [m for _, m in CC.citation_problems("X.md", "備份流程見 OPERATIONS §2.4。")], "§2.4 cited")
    expect("decision id with unrelated topic", [m for _, m in CC.citation_problems("X.md", "備份還原流程依 D-205 辦理")], "D-205 cited")
    # 決策定義列本身不算引用
    expect_clean("definition row is not a citation", CC.citation_problems("DECISIONS_AND_UNKNOWNS.md", "| D-309 | 預算上限與經費來源優先順序 | 政府 | 提案 |"))
    # 目前文件不得有任何引用語境問題
    allp = []
    for f in sorted(ROOT.glob("*.md")):
        allp += [f"{f.name}:{n} {m}" for n, m in CC.citation_problems(f.name, f.read_text(encoding="utf-8"))]
    expect_clean("current docs have no citation-context problems", allp)


def main():
    for t in (test_permission_counterexamples, test_doc_inventory_counterexample, test_schema_counterexamples, test_citation_counterexamples):
        try:
            t()
        except Exception as e:  # 工具壞掉也要算失敗
            FAILS.append(f"{t.__name__} crashed: {e!r}")
    if FAILS:
        print(f"test_checks FAILED ({len(FAILS)} of {COUNT[0]})")
        for f in FAILS:
            print(" -", f)
        sys.exit(1)
    print(f"OK: test_checks {COUNT[0]} counterexample checks passed")


if __name__ == "__main__":
    main()
