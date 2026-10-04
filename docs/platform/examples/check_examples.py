#!/usr/bin/env python3
"""規格驗證用參考檢查程式（非產品程式碼）。

以 ref_engine.py 實作 RESOURCE_AND_ELIGIBILITY_ENGINE.md／PRODUCT_REQUIREMENTS.md／DATA_MODEL_AND_STATE_MACHINES.md
中可被機械驗證的規則，並以手算的預期值比對。只使用 Python 標準函式庫。

用法：
  python3 docs/platform/examples/check_examples.py             # 執行全部檢查（任一失敗 exit 1）
  python3 docs/platform/examples/check_examples.py --write-md  # 由 expected_assessments.json 重新產生 expected_assessments.md

支援範圍與不支援範圍見 ref_engine.py 檔頭與 RESOURCE_AND_ELIGIBILITY_ENGINE.md §5.2；不支援者必須報錯（有測試）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ref_engine as R  # noqa: E402
import ref_control as RC  # noqa: E402

sys.path.insert(0, str(HERE.parent / "tools"))
import schema_lite as SL  # noqa: E402

FAILS = []
COUNT = 0


def check(name, got, want):
    global COUNT
    COUNT += 1
    if got != want:
        FAILS.append(f"{name}: want {want!r} got {got!r}")


def expect_error(name, fn, err_name):
    """err_name 為 None 時要求不拋錯。"""
    global COUNT
    COUNT += 1
    try:
        fn()
    except (R.UnsupportedError, R.ValidationError) as e:
        if err_name != type(e).__name__:
            FAILS.append(f"{name}: expected {err_name}, got {type(e).__name__}: {e}")
        return
    if err_name is not None:
        FAILS.append(f"{name}: expected {err_name}, but no error was raised")


DELETE = "__DELETE__"


def set_path(obj, dotted, value):
    parts = dotted.split(".")
    for p in parts[:-1]:
        obj = obj[p]
    if value == DELETE:
        obj.pop(parts[-1], None)  # 測試「缺少欄位」
    else:
        obj[parts[-1]] = value


# ---------------------------------------------------------------- 1. 目錄完整性
def test_catalog(res):
    scopes = {s["scope_key"]: s for s in res["household_scopes"]}
    source_ids = {s["id"] for s in res["sources"]}
    check("catalog is synthetic", res["is_synthetic"], True)
    keys = [r["resource_key"] for r in res["resources"]]
    check("resource keys unique", len(keys), len(set(keys)))
    for sk, sc in scopes.items():
        expect_error(f"catalog scope {sk} valid", lambda sc=sc: R.validate_scope(sc), None)
    for r in res["resources"]:
        k = r["resource_key"]
        for sid in r["version"]["source_ids"]:
            check(f"{k} source {sid} exists", sid in source_ids, True)
        expect_error(f"{k} rule valid", lambda r=r: R.validate_rule(r["rule"], scopes), None)
        check(f"{k} recommendation sees a valid rule", "RULE_INVALID" in R.recommendation_status(r, {s["id"]: s for s in res["sources"]}, "2026-10-03", scopes)["reasons"], False)
        for c in r["rule"]["criteria"]:
            check(f"{k}.{c['criterion_id']} min_confirmation_for_fail", c.get("min_confirmation_for_fail", "C2") in ("C2", "C3"), True)
        for ex in r["version"]["stacking_rules"].get("excludes", []):
            check(f"{k} stacking target exists", ex["resource_key"] in keys, True)


# ---------------------------------------------------------------- 2. 引擎單元案例
def test_engine_cases(cases):
    scopes = cases["recommendation_scopes"]
    for c in cases["combinator_cases"]:
        got = R.eval_node(c["tree"], c["results"])
        check(f"combinator {c['id']}", got, c["expected"])
    for m in cases["resource_mapping_cases"]:
        check(f"mapping {m['root']}", list(R.resource_result(m["root"])), [m["result"], m["unconfirmed"]])
    for c in cases["invalid_rule_cases"]:
        expect_error(f"invalid rule {c['id']}", lambda c=c: R.validate_rule(c["rule"], scopes), c["expect"])
    # F-02：口徑定義與條件結構（受控驗證；未知鍵與未支援能力一律報錯）
    for c in cases["scope_cases"]:
        expect_error(f"scope {c['id']}", lambda c=c: R.validate_scope(c["scope"]), c["expect"])
    for c in cases["criterion_shape_cases"]:
        expect_error(f"criterion shape {c['id']}", lambda c=c: R.validate_rule(c["rule"], scopes), c["expect"])


def _filler(i):
    return {"criterion_id": f"F{i}", "operator": "EQ", "input_keys": ["household.x"], "threshold": {"value": 1}, "source_ref": "S-1#1"}


def test_rule_validation_order_independence(cases):
    """F-01：非法條件出現在任何位置、與任何其他問題並存，推薦一律 NOT_RECOMMENDED＋RULE_INVALID。"""
    import copy
    sources = cases["recommendation_sources"]
    scopes = cases["recommendation_scopes"]
    as_of = cases["recommendation_as_of"]

    def rec(rule):
        res = copy.deepcopy(cases["recommendation_base"])
        res["rule"] = rule
        return R.recommendation_status(res, sources, as_of, scopes)

    for var in cases["illegal_criterion_variants"]:
        bad = dict(var["criterion"])
        bad["criterion_id"] = "X"
        outcomes = set()
        for n_before in range(0, 4):
            for n_after in range(0, 3):
                crits = [_filler(i) for i in range(n_before)] + [bad] + [_filler(10 + i) for i in range(n_after)]
                ids = [c["criterion_id"] for c in crits]
                all_rule = {"status": "PUBLISHED", "combinator": "ALL", "criteria": crits}
                nested = {"status": "PUBLISHED", "combinator": "CUSTOM", "criteria": crits,
                          "expression": {"op": "ALL", "children": [ids[0], {"op": "ANY", "children": ids[1:]}] if len(ids) > 1 else [ids[0]]}}
                for label, rule in (("ALL", all_rule), ("CUSTOM", nested)):
                    got = rec(rule)
                    outcomes.add((got["status"], tuple(got["reasons"])))
                    check(f"order-independence {var['id']} before={n_before} after={n_after} {label}",
                          got, {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]})
        check(f"order-independence {var['id']} single outcome", len(outcomes), 1)
    for var in cases["illegal_expression_variants"]:
        # 準則集合固定為 F1、F2、X；expression 變體各自違規（NOT／N_OF_M 節點、漏列準則、引用不存在的準則）
        crits = [_filler(1), _filler(2), dict(_filler(3), criterion_id="X")]
        rule = {"status": "PUBLISHED", "combinator": "CUSTOM", "criteria": crits, "expression": copy.deepcopy(var["expression"])}
        check(f"illegal expression {var['id']}", rec(rule), {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]})
    # 合法的 CUSTOM 巢狀表達式不得被誤擋
    ok_rule = {"status": "PUBLISHED", "combinator": "CUSTOM", "criteria": [_filler(1), _filler(2), dict(_filler(3), criterion_id="X")],
               "expression": {"op": "ALL", "children": ["F1", {"op": "ANY", "children": ["F2", "X"]}]}}
    check("legal nested CUSTOM stays FORMAL", rec(ok_rule), {"status": "FORMAL", "reasons": []})


def test_recommendation(cases):
    import copy
    for c in cases["recommendation_cases"]:
        res = copy.deepcopy(cases["recommendation_base"])
        for dotted, v in c["override"].items():
            set_path(res, dotted, v)
        sources = {k: dict(v) for k, v in cases["recommendation_sources"].items()}
        for sid, st in c.get("source_status", {}).items():
            sources[sid]["status"] = st
        got = R.recommendation_status(res, sources, cases["recommendation_as_of"], cases["recommendation_scopes"])
        check(f"recommendation {c['id']}", got, c["expected"])
    # 沒有完整口徑表就不可呼叫（不得以空表略過口徑驗證）
    base = copy.deepcopy(cases["recommendation_base"])
    try:
        R.recommendation_status(base, cases["recommendation_sources"], cases["recommendation_as_of"], None)
        FAILS.append("recommendation_status without scopes must raise TypeError")
    except TypeError:
        pass


# ---------------------------------------------------------------- 3. 家庭評估
def test_households(res, hhs, exp):
    scopes = {s["scope_key"]: s for s in res["household_scopes"]}
    sources = {s["id"]: s for s in res["sources"]}
    as_of = exp["evaluation_date"]
    check("households synthetic", hhs["is_synthetic"], True)
    for hh in hhs["households"]:
        for r in res["resources"]:
            key = r["resource_key"]
            tag = f"{hh['id']}/{key}"
            want = exp["expected"].get(hh["id"], {}).get(key)
            if want is None:
                FAILS.append(f"{tag}: missing expectation")
                continue
            got = R.evaluate(r, hh, scopes, res["regions"], sources, as_of)
            check(f"{tag} recommendation", got["recommendation"], want["recommendation"])
            check(f"{tag} result", got.get("result"), want.get("result"))
            if "result" not in want:
                continue
            check(f"{tag} criteria", got.get("criteria"), want["criteria"])
            check(f"{tag} unconfirmed", got.get("unconfirmed"), want.get("unconfirmed"))
            check(f"{tag} flags", got.get("flags"), want.get("flags"))
            check(f"{tag} known_failures", got.get("known_failures"), want.get("known_failures"))
            for cid, dv in want.get("derived", {}).items():
                check(f"{tag} derived {cid}", got.get("derived", {}).get(cid), dv)
            if "missing_inputs" in want:
                check(f"{tag} missing_inputs", got.get("missing_inputs"), want["missing_inputs"])
            # 不變條件：資料不足永遠不會被顯示為不符合（基線：資料不足不得排除）
            if want["result"] == "LIKELY_INELIGIBLE":
                check(f"{tag} ineligible has no UNKNOWN", "UNKNOWN" in got["criteria"].values(), False)
            if "UNKNOWN" in got["criteria"].values():
                check(f"{tag} UNKNOWN never ineligible", got["result"], "INSUFFICIENT_DATA")
    # 每個「正式推薦」或「人工查核」的資源，在每個家庭都有結果
    check("coverage", sorted(exp["expected"]), sorted(h["id"] for h in hhs["households"]))
    # 不支援的輸入必須報錯，不得默默略過
    import copy
    bad = copy.deepcopy(hhs["households"][0])
    bad["facts"]["household.movable_property_per_capita"] = {"value": {"min": 0, "max": 100000}, "confirmation_level": "C1"}
    live = next(r for r in res["resources"] if r["resource_key"] == "TW-DEMO-LIVING-001")
    expect_error("range input unsupported", lambda: R.evaluate(live, bad, scopes, res["regions"], sources, as_of), "UnsupportedError")
    # 規則 criteria 引用未定義 scope → 推薦層即 NOT_RECOMMENDED（RULE_INVALID），評估不會產生結果
    broken = copy.deepcopy(live)
    broken["rule"]["criteria"][1]["scope_key"] = "SCOPE-NOPE"
    got = R.evaluate(broken, hhs["households"][0], scopes, res["regions"], sources, as_of)
    check("unknown scope -> NOT_RECOMMENDED", got, {"recommendation": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]}})
    # F-02 回歸：GPT 實測——在 SCOPE-CO 加入 age_between，舊版 runner 仍把 35、66 歲成員計入且不報錯
    sc = copy.deepcopy(scopes)
    sc["SCOPE-CO"]["member_inclusion"]["age_between"] = [0, 17]
    expect_error("F-02 scope_members rejects unsupported age_between", lambda: R.scope_members(hhs["households"][0], sc["SCOPE-CO"]), "UnsupportedError")
    edu = next(r for r in res["resources"] if r["resource_key"] == "TW-DEMO-EDU-003")
    got = R.evaluate(edu, hhs["households"][0], sc, res["regions"], sources, as_of)
    check("F-02 evaluate with unsupported scope -> NOT_RECOMMENDED", got["recommendation"], {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]})
    sc2 = copy.deepcopy(scopes)
    sc2["SCOPE-CO"]["member_inclusion"]["hair_color"] = "x"
    expect_error("F-02 scope_members rejects unknown key", lambda: R.scope_members(hhs["households"][0], sc2["SCOPE-CO"]), "ValidationError")
    # F-01 回歸（GPT 三個實測）：以真實 LIVING-001 為底
    sources_ok = {s["id"]: s for s in res["sources"]}
    a = copy.deepcopy(live); a["rule"]["criteria"][2]["min_confirmation_for_fail"] = "C1"
    check("F-01a later criterion C1", R.recommendation_status(a, sources_ok, as_of, scopes), {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]})
    b = copy.deepcopy(live); b["rule"]["combinator"] = "CUSTOM"; b["rule"]["expression"] = {"op": "NOT", "children": ["C1", "C2", "C3"]}
    check("F-01b CUSTOM NOT", R.recommendation_status(b, sources_ok, as_of, scopes), {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]})
    c = copy.deepcopy(live); del c["rule"]["status"]
    check("F-01c rule.status removed", R.recommendation_status(c, sources_ok, as_of, scopes), {"status": "NOT_RECOMMENDED", "reasons": ["RULE_STATUS_MISSING"]})


def test_unknown_member_not_dropped(res, hhs):
    """T-31：成員口徑事實未知時，不得排除該成員後繼續計算。"""
    scopes = {s["scope_key"]: s for s in res["household_scopes"]}
    h5 = next(h for h in hhs["households"] if h["id"] == "H5")
    members, missing, _ = R.scope_members(h5, scopes["SCOPE-CO"])
    check("H5 SCOPE-CO reports missing, not a smaller family", missing, ["H5-P3:person.co_residing"])
    members, missing, _ = R.scope_members(h5, scopes["SCOPE-L1"])
    check("H5 SCOPE-L1 unaffected", [m["id"] for m in members], ["H5-P1", "H5-P2", "H5-P3"])
    check("H5 SCOPE-L1 no missing", missing, [])


# ---------------------------------------------------------------- 4. 其他不變條件
def test_outcomes(cases):
    for sc in cases["outcome_scenarios"]:
        for i, q in enumerate(sc["queries"]):
            got = R.count_outcomes(sc["events"], sc["outcomes"], q["window"][0], q["window"][1], q["known_at"])
            check(f"outcome {sc['id']} q{i}", got, q["expected"])
    for sc in cases["outcome_invalid_events"]:
        expect_error(f"outcome invalid {sc['id']}", lambda sc=sc: R.count_outcomes(sc["events"], sc["outcomes"], "2026-10-01", "2026-10-31", "2026-11-30"), sc["expect"])


def legacy_ap06_blocks(existing, app_id):
    """R1 版 AP-06 前置條件的舊行為（保留作為回歸對照）：同家庭、同資源、同給付期間只要有非「不核准／撤回／失效」的申請，
    **包括申請本身與已核准的原件**，就一律擋下。這會擋掉合法的 SUPPLEMENTARY（原件必須是 APPROVED），也會把申請自己當成重複。"""
    app = next(a for a in existing if a["id"] == app_id)
    return any(a["household"] == app["household"] and a["resource"] == app["resource"] and a["period"] == app["period"]
               and a["status"] not in R.BLOCKING_EXCLUDED for a in existing)


def test_applications(cases):
    for c in cases["application_cases"]:
        ok, why = R.application_create_allowed(c["existing"], c["new"])
        check(f"application {c['id']}", [ok, why], c["expected"])
    # F-06：送件前（AP-06）防重複依 kind 分別定義，並排除申請本身
    for c in cases["application_ready_cases"]:
        got = R.application_ready_check(c["existing"], c["app_id"])
        check(f"application ready {c['id']}", list(got), c["expected"])
    for c in cases["application_lifecycle_cases"]:
        ok, why = R.application_create_allowed(c["existing"], c["new"])
        if "expected_create" in c:
            check(f"lifecycle {c['id']} create", [ok, why], c["expected_create"])
            continue
        check(f"lifecycle {c['id']} create", [ok, why], [True, "ok"])
        apps = c["existing"] + [dict(c["new"], status="CANDIDATE")]
        M = R.load_machines()["application"]
        trans = {(f, t["to"][0]): t["id"] for t in M["transitions"] for f in t["from"] if len(t["to"]) == 1}
        for frm, to in zip(c["path"], c["path"][1:]):
            check(f"lifecycle {c['id']} legal {frm}->{to}", (frm, to) in trans, True)
            apps[-1]["status"] = to
            if to == "READY_TO_SUBMIT":
                check(f"lifecycle {c['id']} AP-06 ready", list(R.application_ready_check(apps, apps[-1]["id"])), c["expected_ready"])
                # 回歸：R1 版前置條件會把這件合法的補充申請擋下
                check(f"lifecycle {c['id']} legacy rule would have blocked it", legacy_ap06_blocks(apps, apps[-1]["id"]), True)
    # T-46：同一 Idempotency-Key 的並發請求只會有一個執行；不同 key 但同 ORIGINAL 鍵者被唯一約束擋下
    shape = lambda i: {"status_code": 201, "resource_ref": {"type": "Application", "id": i}, "shape_version": 1}
    store = R.IdempotencyStore()
    check("idem first", store.begin("u1", "k1", "h1")[0], "PROCEED")
    check("idem concurrent same key", store.begin("u1", "k1", "h1")[0], "REJECT_409_IN_PROGRESS")
    store.complete("u1", "k1", shape("a1"))
    check("idem replay", store.begin("u1", "k1", "h1"), ("REPLAY", shape("a1")))
    check("idem different body", store.begin("u1", "k1", "h2")[0], "REJECT_422")
    check("idem other actor independent", store.begin("u2", "k1", "h1")[0], "PROCEED")
    existing = []
    new = {"kind": "ORIGINAL", "household": "H1", "resource": "R1", "period": "2026"}
    ok1, _ = R.application_create_allowed(existing, new)
    if ok1:
        existing.append({"id": "a1", "kind": "ORIGINAL", "status": "CANDIDATE", **{k: new[k] for k in ("household", "resource", "period")}})
    ok2, why2 = R.application_create_allowed(existing, new)
    check("T-46 two different-key requests create one application", [ok1, ok2, why2], [True, False, "ORIGINAL_EXISTS_CANDIDATE"])


def test_idempotency_replay(cases):
    """F-05：IdempotencyRecord 只存回應形狀；重播時以「當下」權限、同意與刪除狀態重新取得內容。"""
    shape = {"status_code": 201, "resource_ref": {"type": "Application", "id": "a1"}, "shape_version": 1}
    for bad in ({"id": "a1"}, {**shape, "body": {"household": "H1", "income": 12345}}, {**shape, "resource_ref": {"type": "Application", "id": "a1", "name": "x"}},
                {"status_code": 201, "resource_ref": {"type": "Application", "id": "a1"}}):
        store = R.IdempotencyStore()
        store.begin("u1", "k", "h")
        expect_error(f"idempotency response with content rejected {sorted(bad)}", lambda store=store, bad=bad: store.complete("u1", "k", bad), "ValidationError")
    for c in cases["replay_cases"]:
        store = R.IdempotencyStore()
        store.begin("u1", "k", "h")
        store.complete("u1", "k", shape)
        w = c["world"]

        def resolver(actor, ref, w=w):
            if w["deleted"]:
                return "GONE", None
            if not w["consent_valid"] or not w["permitted"]:
                return "FORBIDDEN", None
            return "OK", w["current"]

        check(f"replay {c['id']}", list(store.replay("u1", "k", "h", resolver)), c["expected"])
    # 重播不會繞過「不同內容 422／處理中 409」
    store = R.IdempotencyStore()
    store.begin("u1", "k", "h")
    check("replay while in progress", store.replay("u1", "k", "h", lambda a, r: ("OK", {}))[0], "REJECT_409_IN_PROGRESS")
    store.complete("u1", "k", shape)
    check("replay with different body", store.replay("u1", "k", "other", lambda a, r: ("OK", {}))[0], "REJECT_422")


def test_schemas(res, cases, ctrl):
    """結構驗證（schemas/*.schema.json；只驗結構、型別、必要欄位、列舉與未知鍵，不含跨欄位語意）。"""
    for r in res["resources"]:
        k = r["resource_key"]
        check(f"schema resource_version {k}", SL.validate(r["version"], SL.load_schema("resource_version")), [])
        check(f"schema eligibility_rule {k}", SL.validate(r["rule"], SL.load_schema("eligibility_rule")), [])
    for sc in res["household_scopes"]:
        check(f"schema household_scope {sc['scope_key']}", SL.validate(sc, SL.load_schema("household_scope")), [])
    for k, sc in cases["recommendation_scopes"].items():
        sc = dict(sc, label_plain="x")
        check(f"schema household_scope (cases) {k}", SL.validate(sc, SL.load_schema("household_scope")), [])
    for scen in ctrl["scenarios"]:
        for i, st in enumerate(scen["steps"]):
            if st.get("op") == "control":
                check(f"schema control_record {scen['id']}[{i}]", SL.validate(st["rec"], SL.load_schema("control_record")), [])


def test_callbacks(cases):
    for c in cases["callback_scenarios"]:
        state, applied, late = R.apply_notification_events(c["events"])
        check(f"callback {c['id']}", {"state": state, "applied": applied, "late_failure": late}, c["expected"])


def test_state_machines():
    M = R.load_machines()
    ok = lambda m, cur, tid, actor: R.transition_allowed(M, m, cur, tid, actor)[0]
    # T-43 非法轉換
    check("AP-08 R3 submit", ok("application", "READY_TO_SUBMIT", "AP-08", "R3"), True)
    check("AP-08 wrong state", ok("application", "PREPARING_DOCS", "AP-08", "R3"), False)
    check("AP-08 wrong actor", ok("application", "READY_TO_SUBMIT", "AP-08", "R5"), False)
    check("no direct PREPARING→APPROVED", any(t["to"] == ["APPROVED"] and "PREPARING_DOCS" in t["from"] for t in M["application"]["transitions"]), False)
    check("outcome correction R4 only", [ok("outcome", "RECEIVED", "OC-08", a) for a in ("R3", "R4")], [False, True])
    check("application correction not by R3", ok("application", "SUBMITTED", "AP-19", "R3"), False)
    # T-44 內部補件逾期不推定外部失效
    to_lapsed = [t for t in M["application"]["transitions"] if t["to"] == ["LAPSED"]]
    check("LAPSED only via AP-14", [t["id"] for t in to_lapsed], ["AP-14"])
    check("LAPSED never by SYSTEM", any("SYSTEM" in t["actors"] for t in to_lapsed), False)
    check("SUBMITTED→UNDER_REVIEW no SYSTEM", any("SYSTEM" in t["actors"] for t in M["application"]["transitions"] if t["id"] == "AP-09"), False)
    check("AP-14 requires R4", "R4" in next(t for t in to_lapsed)["actors"] and "機關" in to_lapsed[0]["pre"], True)
    # DENIED 之後只有更正
    check("DENIED outgoing are corrections", {t["kind"] for t in M["application"]["transitions"] if "DENIED" in t["from"]}, {"correction"})
    # 補抽查複核、轉介結束／取消／重試、未取得後恢復、通知重試
    check("AS-06 sample audit exists", ok("assessment", "EVALUATED", "AS-06", "R4"), True)
    check("AS-07 additional review exists", ok("assessment", "REVIEWED", "AS-07", "R4"), True)
    check("RF-10 retry", ok("referral", "NO_RESPONSE", "RF-10", "R3"), True)
    check("RF-14 closed after accepted", ok("referral", "ACCEPTED", "RF-14", "R6"), True)
    check("RF-17 cancel after sent", ok("referral", "SENT", "RF-17", "R3"), True)
    check("OC-06 recover after not received", ok("outcome", "NOT_RECEIVED", "OC-06", "R3"), True)
    check("OC-07 partial after not received", ok("outcome", "NOT_RECEIVED", "OC-07", "R3"), True)
    check("NF-08 retry", ok("notification", "FAILED", "NF-08", "SYSTEM"), True)
    check("NF no regression DELIVERED→ACCEPTED", any(t for t in M["notification"]["transitions"] if "DELIVERED" in t["from"] and t["to"] == ["ACCEPTED_BY_PROVIDER"]), False)
    check("Notification DELIVERED→FAILED absent (late_failure flag instead)", any("DELIVERED" in t["from"] and t["to"] == ["FAILED"] for t in M["notification"]["transitions"]), False)


def _dig(obj, dotted):
    for part in dotted.split("."):
        obj = obj[part]
    return obj


def run_control_scenario(initial, sc):
    """執行一個控制紀錄情境（純邏輯模擬）。回傳 (最後一次 recover 結果, 觀察到的狀態碼清單, 目前主庫狀態)。"""
    import copy
    st = RC.new_state(initial)
    log, wit = RC.ControlLog(), RC.Witness()
    snaps, https, recovered, before_reapply = {}, [], None, None
    for step in sc["steps"]:
        op = step["op"]
        if op == "snapshot":
            snaps[step["name"]] = copy.deepcopy(st)
        elif op == "control":
            if step.get("log_fail"):
                log.fail_next = 1
            code, why, st = RC.request_control(st, log, wit, step["rec"], db_fail=step.get("db_fail", False))
            https.append(code)
            if "expect_http" in step:
                check(f"{sc['id']} http", code, step["expect_http"])
        elif op == "lose_log_tail":
            del log.entries[len(log.entries) - step["n"]:]
        elif op == "corrupt_log":
            e = log.entries[step["index"]]
            e["rec"] = dict(e["rec"], tampered=True)
        elif op == "drop_log_entry":
            del log.entries[step["index"]]
        elif op == "recover":
            recovered = RC.recover(snaps[step["from"]], log, wit, skip_reapply=step.get("skip_reapply", False))
        elif op == "reapply_again":
            before_reapply = copy.deepcopy(recovered["state"]) if before_reapply is None else before_reapply
            RC.reapply_all(recovered["state"], log.entries, from_seq=0)
        elif op == "check_state":
            for path, want in step["expect"].items():
                check(f"{sc['id']} state {path}", _dig(st, path), want)
        else:
            raise ValueError(op)
    if before_reapply is not None:
        recovered["unchanged"] = before_reapply == recovered["state"]
    return recovered, https, st


def test_control(ctrl):
    """F-04：撤回、停止處理與刪除的控制紀錄（先寫後提交、還原水位、冪等重套、REDACT／HARD_DELETE 驗證）。純邏輯模擬。"""
    for sc in ctrl["scenarios"]:
        rec, https, st = run_control_scenario(ctrl["initial_state"], sc)
        exp = sc["expect"]
        if rec is None:
            continue
        for k in ("quarantined", "reason", "mismatches", "watermark"):
            if k in exp:
                check(f"{sc['id']} {k}", rec[k], exp[k])
        for path, want in exp.get("state", {}).items():
            check(f"{sc['id']} recovered {path}", _dig(rec["state"], path), want)
        for purpose, want in exp.get("access", {}).items():
            check(f"{sc['id']} access {purpose}", RC.access_allowed(rec["state"], "c1", purpose), want)
        if exp.get("state_unchanged_by_reapply"):
            check(f"{sc['id']} reapply idempotent", rec["unchanged"], True)


# ---------------------------------------------------------------- 5. Markdown 由 JSON 產生
SYMBOL = {"LIKELY_ELIGIBLE": "✅ 可能符合", "INSUFFICIENT_DATA": "❔ 資料不足"}


def cell(w):
    rec = w["recommendation"]
    if rec["status"] == "NOT_RECOMMENDED":
        return "— 不推薦：" + "、".join(rec["reasons"])
    res = w["result"]
    if res == "LIKELY_INELIGIBLE":
        text = "⛔ 可能不符合（已確認）" if w.get("unconfirmed") is False else "⚠️ 可能不符合（依自述，未確認）"
    else:
        text = SYMBOL[res]
    flags = w.get("flags", [])
    extra = []
    if "KNOWN_MISMATCH_PRESENT" in flags:
        kf = "、".join(w.get("known_failures", []))
        extra.append(f"已知不符：{kf}")
    if "HUMAN_CHECK" in flags:
        extra.append("👤人工確認")
    if "CONFIRM_SELF_REPORT" in flags and res != "LIKELY_INELIGIBLE":
        extra.append("📝需確認自述")
    if "CAPACITY_FULL" in flags:
        extra.append("🈵額滿")
    if "ALREADY_RECEIVING" in flags:
        extra.append("🔁已在使用（計續辦）")
    if rec["status"] == "MANUAL_CHECK_ONLY":
        text = "🔎人工查核項（" + "、".join(rec["reasons"]) + "）：" + text
    return text + ("；" + "；".join(extra) if extra else "")


NOTES = """重點說明：
- **H1 的口徑差異（T-03）**：祖母實際同住但不同戶籍。生活扶助依「同戶籍的本人、配偶、子女、父母」計 3 人（祖母年金不計入）；兒少生活補助與午餐補助依「實際共同生活」計 4 人並計入年金。畫面必須分別顯示兩種算法。
- **H2（T-01）**：沒有任何資源顯示為不符合，全部是資料不足並列出缺漏。
- **H3（T-02、T-06）**：地區與收入都是自述（C1），因此結果是「可能不符合（依自述，未確認）」並附確認路徑，而不是排除；自述永遠不能產生「已確認」的不符合。
- **H4（T-05）**：併領排除依已查看的核定書（C2）判定為「已確認」不符合；生活扶助本身標示「已在使用中」，未來取得只能計為續辦，不算新增。
- **H5（T-31）**：祖母是否共同生活未知時，依「實際共同生活」口徑的條件整體為資料不足，不得把祖母排除後繼續計算；「同戶籍」口徑的生活扶助不受影響。
- **H6（T-26）**：居住地由文件確認為乙區（已確認不符），但收入未知 → 資料不足優先，資源整體顯示資料不足，並保留「已知不符：C1」。這是目前採用的規則；改為「已確認不符優先」是待負責人決定的提案（D-312），未啟用。
- **H7（T-27）**：自述不符加上資料不足 → 資料不足，並保留已知不符與「需確認自述」。
- **物資箱 FOOD-005**：生效期間未知（私有資源），依基線不進正式推薦，只列為「人工查核項」，僅協助員／社工可見（T-23）；放寬為正式推薦是待決提案（D-311）。
- **RENT-006** 已過期且申請期間已截止：任何家庭都不推薦（T-04、T-22）。"""


def render_md(exp, res):
    names = {r["resource_key"]: r["canonical_name"].replace("【合成】", "") for r in res["resources"]}
    order = [r["resource_key"] for r in res["resources"]]
    head = ["家庭"] + [k.replace("TW-DEMO-", "") for k in order]
    lines = [
        "# 合成案例預期評估結果",
        "**全部為合成資料。** 本檔由 `python3 docs/platform/examples/check_examples.py --write-md` 依 [expected_assessments.json](expected_assessments.json) 產生，請勿手改。預期值由規格作者依規則手算（不是複製 runner 輸出），檢查程式會比對 runner 結果與預期值是否一致，並檢查本檔與 JSON 同步。",
        f"評估日：{exp['evaluation_date']}。圖例：✅ 可能符合｜❔ 資料不足｜⚠️ 可能不符合（依自述，未確認；永遠附確認路徑，不是排除）｜⛔ 可能不符合（已確認：輸入確認程度 C2 以上）｜🔎 僅供人工查核，不進正式推薦｜👤 需人工確認｜📝 需確認自述｜🈵 額滿｜🔁 已在使用中。",
        "",
        "| " + " | ".join(head) + " |",
        "|" + "---|" * len(head),
    ]
    for hid, per in exp["expected"].items():
        lines.append("| " + hid + " | " + " | ".join(cell(per[k]) for k in order) + " |")
    lines += ["", "資源：" + "；".join(f"{k.replace('TW-DEMO-', '')}＝{names[k]}" for k in order), "", NOTES, ""]
    return "\n".join(lines)


def test_md(exp, res, write):
    path = HERE / "expected_assessments.md"
    new = render_md(exp, res)
    if write:
        path.write_text(new, encoding="utf-8")
        print("wrote", path.name)
        return
    check("expected_assessments.md in sync with JSON", path.read_text(encoding="utf-8"), new)


def run_test(fn, *args):
    """單一測試函式崩潰時記錄為失敗並繼續執行其他測試（不讓一個崩潰遮蔽其他失敗）。"""
    try:
        fn(*args)
    except Exception as e:  # noqa: BLE001
        FAILS.append(f"{fn.__name__} crashed: {type(e).__name__}: {e}")


def main():
    write = "--write-md" in sys.argv
    res = R.load_json("synthetic_resources.json")
    hhs = R.load_json("synthetic_households.json")
    exp = R.load_json("expected_assessments.json")
    cases = R.load_json("engine_cases.json")
    ctrl = R.load_json("control_cases.json")
    if write:
        test_md(exp, res, True)
        return
    run_test(test_catalog, res)
    run_test(test_engine_cases, cases)
    run_test(test_rule_validation_order_independence, cases)
    run_test(test_recommendation, cases)
    run_test(test_households, res, hhs, exp)
    run_test(test_unknown_member_not_dropped, res, hhs)
    run_test(test_outcomes, cases)
    run_test(test_applications, cases)
    run_test(test_idempotency_replay, cases)
    run_test(test_callbacks, cases)
    run_test(test_state_machines)
    run_test(test_control, ctrl)
    run_test(test_schemas, res, cases, ctrl)
    run_test(test_md, exp, res, False)
    if FAILS:
        print(f"FAILED ({len(FAILS)} of {COUNT} checks):")
        for f in FAILS:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {COUNT} checks passed")


if __name__ == "__main__":
    main()
