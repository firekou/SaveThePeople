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


def set_path(obj, dotted, value):
    parts = dotted.split(".")
    for p in parts[:-1]:
        obj = obj[p]
    obj[parts[-1]] = value


# ---------------------------------------------------------------- 1. 目錄完整性
def test_catalog(res):
    scopes = {s["scope_key"]: s for s in res["household_scopes"]}
    source_ids = {s["id"] for s in res["sources"]}
    check("catalog is synthetic", res["is_synthetic"], True)
    keys = [r["resource_key"] for r in res["resources"]]
    check("resource keys unique", len(keys), len(set(keys)))
    for r in res["resources"]:
        k = r["resource_key"]
        for sid in r["version"]["source_ids"]:
            check(f"{k} source {sid} exists", sid in source_ids, True)
        expect_error(f"{k} rule valid", lambda r=r: R.validate_rule(r["rule"], scopes), None)
        for c in r["rule"]["criteria"]:
            check(f"{k}.{c['criterion_id']} min_confirmation_for_fail", c.get("min_confirmation_for_fail", "C2") in ("C2", "C3"), True)
        for ex in r["version"]["stacking_rules"].get("excludes", []):
            check(f"{k} stacking target exists", ex["resource_key"] in keys, True)


# ---------------------------------------------------------------- 2. 引擎單元案例
def test_engine_cases(cases):
    for c in cases["combinator_cases"]:
        got = R.eval_node(c["tree"], c["results"])
        check(f"combinator {c['id']}", got, c["expected"])
    for m in cases["resource_mapping_cases"]:
        check(f"mapping {m['root']}", list(R.resource_result(m["root"])), [m["result"], m["unconfirmed"]])
    for c in cases["invalid_rule_cases"]:
        expect_error(f"invalid rule {c['id']}", lambda c=c: R.validate_rule(c["rule"], {}), c["expect"])


def test_recommendation(cases):
    for c in cases["recommendation_cases"]:
        import copy
        res = copy.deepcopy(cases["recommendation_base"])
        for dotted, v in c["override"].items():
            set_path(res, dotted, v)
        sources = {k: dict(v) for k, v in cases["recommendation_sources"].items()}
        for sid, st in c.get("source_status", {}).items():
            sources[sid]["status"] = st
        got = R.recommendation_status(res, sources, cases["recommendation_as_of"])
        check(f"recommendation {c['id']}", got, c["expected"])


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
    # 規則 criteria 引用未定義 scope → 拒絕
    broken = copy.deepcopy(live)
    broken["rule"]["criteria"][1]["scope_key"] = "SCOPE-NOPE"
    expect_error("unknown scope rejected", lambda: R.evaluate(broken, hhs["households"][0], scopes, res["regions"], sources, as_of), "ValidationError")


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


def test_applications(cases):
    for c in cases["application_cases"]:
        ok, why = R.application_create_allowed(c["existing"], c["new"])
        check(f"application {c['id']}", [ok, why], c["expected"])
    # T-46：同一 Idempotency-Key 的並發請求只會有一個執行；不同 key 但同 ORIGINAL 鍵者被唯一約束擋下
    store = R.IdempotencyStore()
    check("idem first", store.begin("u1", "k1", "h1")[0], "PROCEED")
    check("idem concurrent same key", store.begin("u1", "k1", "h1")[0], "REJECT_409_IN_PROGRESS")
    store.complete("u1", "k1", {"id": "a1"})
    check("idem replay", store.begin("u1", "k1", "h1"), ("REPLAY", {"id": "a1"}))
    check("idem different body", store.begin("u1", "k1", "h2")[0], "REJECT_422")
    check("idem other actor independent", store.begin("u2", "k1", "h1")[0], "PROCEED")
    existing = []
    new = {"kind": "ORIGINAL", "household": "H1", "resource": "R1", "period": "2026"}
    ok1, _ = R.application_create_allowed(existing, new)
    if ok1:
        existing.append({"id": "a1", "kind": "ORIGINAL", "status": "CANDIDATE", **{k: new[k] for k in ("household", "resource", "period")}})
    ok2, why2 = R.application_create_allowed(existing, new)
    check("T-46 two different-key requests create one application", [ok1, ok2, why2], [True, False, "ORIGINAL_EXISTS_CANDIDATE"])


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


def main():
    write = "--write-md" in sys.argv
    res = R.load_json("synthetic_resources.json")
    hhs = R.load_json("synthetic_households.json")
    exp = R.load_json("expected_assessments.json")
    cases = R.load_json("engine_cases.json")
    if write:
        test_md(exp, res, True)
        return
    test_catalog(res)
    test_engine_cases(cases)
    test_recommendation(cases)
    test_households(res, hhs, exp)
    test_unknown_member_not_dropped(res, hhs)
    test_outcomes(cases)
    test_applications(cases)
    test_callbacks(cases)
    test_state_machines()
    test_md(exp, res, False)
    if FAILS:
        print(f"FAILED ({len(FAILS)} of {COUNT} checks):")
        for f in FAILS:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {COUNT} checks passed")


if __name__ == "__main__":
    main()
