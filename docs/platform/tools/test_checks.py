#!/usr/bin/env python3
"""檢查工具本身的反例測試（只使用標準函式庫）。

這些測試餵入「刻意違規」的資料，確認檢查工具會抓到。它們驗證的是**文件檢查工具**，
不是產品行為；產品授權行為測試（T-19、T-32～T-35、T-50、T-51）待 WP-08 實作後才存在。

用法：python3 docs/platform/tools/test_checks.py   （任何一項反例沒被抓到即 exit 1）
"""
import copy
import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_permissions as GP  # noqa: E402
import schema_lite as SL  # noqa: E402
import citation_check as CC  # noqa: E402
import prose_policy as PP  # noqa: E402

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


def test_prose_policy_counterexamples():
    j = (ROOT / "USER_JOURNEYS_AND_SCREENS.md").read_text(encoding="utf-8")
    e = (ROOT / "RESOURCE_AND_ELIGIBILITY_ENGINE.md").read_text(encoding="utf-8")
    a = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    dm = (ROOT / "DATA_MODEL_AND_STATE_MACHINES.md").read_text(encoding="utf-8")
    sm = (ROOT / "state_machines.json").read_text(encoding="utf-8")
    expect_clean("baseline P9 prose", PP.p9_problems(j, e, a))
    expect_clean("baseline recheck lifecycle prose", PP.recheck_lifecycle_problems(sm, dm, e))
    # F-03：把原本矛盾的文字放回去，必須被具體抓到
    expect("P9 restored 'view affected cases'", PP.p9_problems(j.replace("查看**資源層級影響摘要**", "查看受影響案件", 1), e, a), "P9 promises case-level content")
    expect("engine 8.2 restored per-case progress", PP.p9_problems(j, e.replace("**只顯示資源層級影響摘要**", "顯示每案處理進度", 1), a), "ENGINE §8.2 promises case-level content")
    expect("architecture returns affected case list", PP.p9_problems(j, e, a.replace("資源層級影響摘要（彙總件數；不含逐案 ID 或個案內容）", "受影響案件清單")), "ARCHITECTURE transitions API")
    expect("P9 summary wording removed", PP.p9_problems(j.replace("不含逐案", "含逐案", 1), e, a), "resource-level impact summary")
    # F-07：恢復「暫停保留」或移除任一離開轉換的清除說明
    expect("keep-on-suspend restored", PP.recheck_lifecycle_problems(sm, dm + "\nRV-09 暫停時保留供稽核", e), "kept when SUSPENDED")
    for tid in PP.RECHECK_EXIT_TRANSITIONS:
        d = json.loads(sm)
        for t in d["machines"]["resource_version"]["transitions"]:
            if t["id"] == tid:
                t["pre"] = t["pre"].replace("清除 `recheck_started_at`", "")
        expect(f"{tid} clear statement removed", PP.recheck_lifecycle_problems(json.dumps(d, ensure_ascii=False), dm, e), f"{tid} must state it clears")
    expect("must-be-empty row removed", PP.recheck_lifecycle_problems(sm, dm.replace("其他狀態必為空", ""), e), "other states must be empty")


def _mut(name, repls):
    """載入「被人為破壞」的參考實作：把原始碼指定片段替換後執行。片段找不到就是測試本身壞了。"""
    path = ROOT / "examples" / f"{name}.py"
    src = path.read_text(encoding="utf-8")
    for a, b in repls:
        COUNT[0] += 1
        if a not in src:
            FAILS.append(f"mutation anchor for {name} not found: {a[:50]!r}")
        src = src.replace(a, b)
    mod = types.ModuleType(f"{name}_mutant")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


def _examples():
    sys.path.insert(0, str(ROOT / "examples"))
    import ref_engine, ref_control  # noqa: E401
    return ref_engine, ref_control


def _in_school_result(E):
    res = E.load_json("synthetic_resources.json")
    hh = E.load_json("synthetic_households.json")["households"][0]
    scopes = {x["scope_key"]: x for x in res["household_scopes"]}
    c = {"criterion_id": "N02", "operator": "COUNT_MEMBERS_WHERE", "scope_key": "SCOPE-CO", "input_keys": ["person.age", "person.in_school"],
         "threshold": {"where": {"age_between": [0, 17], "in_school": False}, "min_count": 2}, "min_confirmation_for_fail": "C2"}
    return E.eval_criterion(c, hh, scopes, res["regions"])["result"]


def test_n02_mutation():
    """N-02：H1（0～17 歲、不在學）count=1 < 2 → FAIL_UNCONFIRMED（手算）；把 false 當未提供的舊寫法會得 PASS，必須被抓到。"""
    E, _ = _examples()
    COUNT[0] += 1
    if _in_school_result(E) != "FAIL_UNCONFIRMED":
        FAILS.append("N-02 baseline in_school=false should be FAIL_UNCONFIRMED")
    mut = _mut("ref_engine", [('if "in_school" in where else', 'if where.get("in_school") else'),
                              ('("in_school" not in where or sch["value"] is where["in_school"])', '(not where.get("in_school") or sch["value"])')])
    COUNT[0] += 1
    if _in_school_result(mut) != "PASS":
        FAILS.append("N-02 mutation (truthiness) was expected to change the result to PASS, proving the counterexample is sensitive")


def _control_run(RC, witness_mode):
    initial = json.loads((ROOT / "examples" / "control_cases.json").read_text(encoding="utf-8"))["initial_state"]
    st, log = RC.new_state(initial), RC.ControlLog()
    wit = RC.Witness()
    if witness_mode == "unflushed":
        wit.__class__ = type("U", (RC.Witness,), {"report": lambda self, seq: None})
    rec = {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": ["REMINDERS", "REFERRAL_SHARE"]}
    code, why, st2 = RC.request_control(st, log, wit, rec, db_fail=True)
    return code, len(log.entries), st2["notifications"]["n1"]["status"], log, wit, initial


def test_n03_mutation():
    """N-03：見證未確認（含只排入定期更新）→ 503、控制紀錄不寫、主庫不動；移除該防護的破壞版本必須被抓到。"""
    _, RC = _examples()
    COUNT[0] += 1
    got = _control_run(RC, "unflushed")[:3]
    if got != (503, 0, "SCHEDULED"):
        FAILS.append(f"N-03 baseline unflushed witness: want (503, 0, SCHEDULED) got {got}")
    mut = _mut("ref_control", [('    if acked is not True:\n        return 503, "WITNESS_UNCONFIRMED", st\n', '')])
    COUNT[0] += 1
    got = _control_run(mut, "unflushed")[:3]
    if got == (503, 0, "SCHEDULED"):
        FAILS.append("N-03 mutation (witness ack ignored) was not caught")
    # 還原時見證雜湊比對：整段重寫但重算鏈，只有見證雜湊能抓到
    for label, RCm, want_quarantined in (("baseline", RC, True), ("mutation", _mut("ref_control", [('log.entries[seq - 1]["hash"] != h', 'False')]), False)):
        initial = json.loads((ROOT / "examples" / "control_cases.json").read_text(encoding="utf-8"))["initial_state"]
        st, log, wit = RCm.new_state(initial), RCm.ControlLog(), RCm.Witness()
        RCm.request_control(st, log, wit, {"type": "HARD_DELETE", "table": "objects", "id": "doc1"})
        e = log.entries[0]
        e["payload"] = dict(e["payload"], reason="INCIDENT")
        prev = "0" * 64
        for x in log.entries:
            x["prev_hash"] = prev
            x["hash"] = RCm._hash(prev, RCm._body(x))
            prev = x["hash"]
        out = RCm.recover(initial, log, wit)
        COUNT[0] += 1
        if out["quarantined"] is not want_quarantined:
            FAILS.append(f"N-03 rewritten-chain {label}: want quarantined={want_quarantined} got {out['quarantined']} ({out['reason']})")
    # 還原時見證不可用不得放行
    initial = json.loads((ROOT / "examples" / "control_cases.json").read_text(encoding="utf-8"))["initial_state"]
    st, log, wit = RC.new_state(initial), RC.ControlLog(), RC.Witness()
    RC.request_control(st, log, wit, {"type": "HARD_DELETE", "table": "objects", "id": "doc1"})
    wit.available = False
    COUNT[0] += 1
    if RC.recover(initial, log, wit)["reason"] != "WITNESS_UNAVAILABLE":
        FAILS.append("N-03 unavailable witness must keep quarantine")


def test_n04_counterexamples():
    d, m = base()
    expect_clean("baseline N-04", GP.policy_problems(d, m))
    api = next(a for a in d["api"] if a["endpoint"].endswith("/verify"))
    # verify：結構化排除、note 只能由結構衍生
    x = copy.deepcopy(d)
    for a in x["api"]:
        if a["endpoint"].endswith("/verify"):
            a["note"] = "R4 可驗證自己登錄的成果；責任人也可驗證"
    expect("verify note overridden", GP.policy_problems(x, m), "note must equal the text derived from verifier_must_not_be")
    for dropped in GP.VERIFIER_REQUIRED:
        x = copy.deepcopy(d)
        for a in x["api"]:
            if a["endpoint"].endswith("/verify"):
                a["verifier_must_not_be"] = [k for k in a["verifier_must_not_be"] if k != dropped]
                a["note"] = GP.verify_note(a)
        expect(f"verify exclusion {dropped} dropped", GP.policy_problems(x, m), "verifier_must_not_be must be exactly")
    x = copy.deepcopy(d)
    for a in x["api"]:
        if a["endpoint"].endswith("/verify"):
            del a["verifier_must_not_be"]
    expect("verify exclusion removed", GP.policy_problems(x, m), "verifier_must_not_be must be exactly")
    rec = {"registrant": "U-REG", "case_owner": "U-OWN", "case_owner_delegates": ["U-DEL"]}
    for who, want in (("U-REG", (False, "VERIFIER_IS_REGISTRANT")), ("U-OWN", (False, "VERIFIER_IS_CASE_OWNER")),
                      ("U-DEL", (False, "VERIFIER_IS_CASE_OWNER_DELEGATE")), ("U-SECOND", (True, "ok"))):
        COUNT[0] += 1
        if GP.verifier_allowed(api, who, rec) != want:
            FAILS.append(f"verifier_allowed({who}): want {want} got {GP.verifier_allowed(api, who, rec)}")
    # 資源轉換：R4 不得有 RV-14（矩陣、狀態機、頁面、API 文字一致）
    x = copy.deepcopy(d)
    x["matrix"]["resource_internal"]["R4"][0]["transition_limits"] = ["RV-09", "RV-10", "RV-14"]
    expect("R4 limits widened to RV-14", GP.policy_problems(x, m), "lists RV-14 but the state machine does not allow R4")
    y = copy.deepcopy(m)
    for t in y["resource_version"]["transitions"]:
        if t["id"] == "RV-14":
            t["actors"] = ["R4", "R5", "R7"]
    expect("state machine gives RV-14 to R4", GP.policy_problems(d, y), "lets R4 perform RV-14")
    x = copy.deepcopy(d)
    for pg in x["pages"]:
        if pg["page"] == "P9":
            pg["sections"][0]["note"] = "R5 可編輯與發布（發布人≠查核人）；R4、R7 僅可暫停／停用；R9 唯讀；個案內容一律不可見"
    expect("P9 old wording restored", GP.policy_problems(x, m), "page P9")
    x = copy.deepcopy(d)
    for a in x["api"]:
        if a["endpoint"] == "POST /api/admin/versions/{id}/transitions":
            a["note"] = "R4、R7 僅限暫停／停用轉換"
    expect("transitions API old wording restored", GP.policy_problems(x, m), "transitions")
    x = copy.deepcopy(d)
    del x["matrix"]["resource_internal"]["R4"][0]["transition_limits"]
    expect("R4 edit right without structured limits", GP.policy_problems(x, m), "edit right needs structured transition_limits")


def test_n05_schema_counterexamples():
    sc = SL.load_schema("control_record")
    payload = sc["definitions"]["payload"]
    ok = {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": ["REMINDERS"]}
    envelope = {"seq": 1, "prev_hash": "0" * 64, "hash": "a" * 64, "recorded_at": "2026-01-01T00:00:01Z", "payload": ok}
    COUNT[0] += 1
    if SL.validate(envelope, sc) or SL.validate(ok, payload, sc):
        FAILS.append("N-05 legal envelope/payload rejected")
    bad = {
        "missing consent_id": {"type": "CONSENT_REVOKE", "purposes": ["REMINDERS"]},
        "empty purposes": {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": []},
        "blank purpose": {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": [""]},
        "purposes wrong type": {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": "REMINDERS"},
        "retention_hold wrong type": {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": ["REMINDERS"], "retention_hold": "yes"},
        "unknown key": {"type": "CONSENT_REVOKE", "consent_id": "c1", "purposes": ["REMINDERS"], "person_name": "x"},
        "legacy consent key": {"type": "CONSENT_REVOKE", "consent": "c1", "purposes": ["REMINDERS"]},
        "bad reason": {"type": "HARD_DELETE", "table": "facts", "id": "f1", "reason": "BECAUSE"},
        "HARD_DELETE without id": {"type": "HARD_DELETE", "table": "facts"},
        "HARD_DELETE with fields": {"type": "HARD_DELETE", "table": "facts", "id": "f1", "fields": ["value"]},
        "REDACT without fields": {"type": "REDACT", "table": "facts", "id": "f1"},
        "REDACT empty fields": {"type": "REDACT", "table": "facts", "id": "f1", "fields": []},
        "REDACT with purposes": {"type": "REDACT", "table": "facts", "id": "f1", "fields": ["value"], "purposes": ["X"]},
        "APPLIED without ref": {"type": "APPLIED"},
        "APPLIED ref zero": {"type": "APPLIED", "ref": 0},
        "APPLIED with table": {"type": "APPLIED", "ref": 1, "table": "facts"},
        "unknown type": {"type": "SOMETHING"},
        "type only": {"type": "CONSENT_REVOKE"},
    }
    for label, p in bad.items():
        COUNT[0] += 1
        if not SL.validate(p, payload, sc):
            FAILS.append(f"N-05 payload not rejected: {label}")
    for label, mutate in (("no seq", lambda e: e.pop("seq")), ("seq 0", lambda e: e.update(seq=0)), ("short hash", lambda e: e.update(hash="abc")),
                          ("bad time", lambda e: e.update(recorded_at="yesterday")), ("flat payload fields", lambda e: e.update(type="CONSENT_REVOKE")),
                          ("no payload", lambda e: e.pop("payload"))):
        x = copy.deepcopy(envelope)
        mutate(x)
        COUNT[0] += 1
        if not SL.validate(x, sc):
            FAILS.append(f"N-05 envelope not rejected: {label}")


def main():
    for t in (test_permission_counterexamples, test_doc_inventory_counterexample, test_schema_counterexamples, test_citation_counterexamples, test_prose_policy_counterexamples, test_n02_mutation, test_n03_mutation, test_n04_counterexamples, test_n05_schema_counterexamples):
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
