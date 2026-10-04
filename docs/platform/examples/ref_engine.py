"""規格驗證用參考實作（非產品程式碼，只用 Python 標準函式庫）。

依 RESOURCE_AND_ELIGIBILITY_ENGINE.md §0、§5～§7 實作一個「最小但嚴格」的子集，用來證明規格可被一致實作：
- 遇到不支援的運算子、組合、輸入格式一律拋出 UnsupportedError／ValidationError，不默默略過；
- 不支援（規格上有、runner 未實作）：AGE_BETWEEN、DATE_WITHIN、區間值輸入、NOT／N_OF_M 組合。
"""
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parent

LEVEL = {"C0": 0, "C1": 1, "C2": 2, "C3": 3}
SUPPORTED_OPERATORS = {
    "EQ", "NEQ", "LT", "LTE", "GT", "GTE", "BETWEEN", "IN", "NOT_IN", "EXISTS",
    "REGION_IN", "COUNT_MEMBERS_WHERE", "NOT_RECEIVING", "HUMAN_JUDGMENT",
}
UNSUPPORTED_OPERATORS = {"AGE_BETWEEN", "DATE_WITHIN"}
SUPPORTED_COMBINATORS = {"ALL", "ANY", "CUSTOM"}
KNOWN_NODE_OPS = {"ALL", "ANY"}
SUPPORTED_HUMAN_TRIGGERS = {"value_within_5_percent_of_threshold"}
RESULTS = ("PASS", "FAIL", "FAIL_UNCONFIRMED", "UNKNOWN", "HUMAN")


class UnsupportedError(Exception):
    """規格允許或預見、但此 runner／引擎不支援的語意。"""


class ValidationError(Exception):
    """規則、資料或輸入不合法，必須拒絕。"""


def load_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 規則驗證與組合
def _node_ids(node, out):
    if isinstance(node, str):
        out.append(node)
        return
    if not isinstance(node, dict) or "op" not in node:
        raise ValidationError(f"bad expression node: {node!r}")
    if node["op"] not in KNOWN_NODE_OPS:
        raise UnsupportedError(f"unsupported combinator node op: {node['op']}")
    children = node.get("children")
    if not children:
        raise ValidationError("expression node has no children")
    for c in children:
        _node_ids(c, out)


def rule_tree(rule):
    """回傳正規化的樹狀表達式。"""
    comb = rule.get("combinator")
    ids = [c["criterion_id"] for c in rule["criteria"]]
    if comb in ("ALL", "ANY"):
        if "expression" in rule:
            raise ValidationError("expression only allowed with CUSTOM")
        return {"op": comb, "children": ids}
    if comb == "CUSTOM":
        if "expression" not in rule:
            raise ValidationError("CUSTOM requires expression")
        return rule["expression"]
    raise UnsupportedError(f"unsupported combinator: {comb!r}")


def validate_rule(rule, scopes=None):
    scopes = scopes or {}
    if rule.get("combinator") not in SUPPORTED_COMBINATORS:
        raise UnsupportedError(f"unsupported combinator: {rule.get('combinator')!r}")
    ids = []
    for c in rule["criteria"]:
        cid = c.get("criterion_id")
        if not cid or cid in ids:
            raise ValidationError(f"missing or duplicate criterion_id {cid!r}")
        ids.append(cid)
        op = c.get("operator")
        if op in UNSUPPORTED_OPERATORS:
            raise UnsupportedError(f"{cid}: operator {op} is not supported by this runner")
        if op not in SUPPORTED_OPERATORS:
            raise ValidationError(f"{cid}: unknown operator {op!r}")
        if not c.get("source_ref"):
            raise ValidationError(f"{cid}: source_ref required")
        if c.get("min_confirmation_for_fail", "C2") not in ("C2", "C3"):
            raise ValidationError(f"{cid}: min_confirmation_for_fail must be C2 or C3 (self-report can never confirm a failure)")
        for h in c.get("requires_human_when", []):
            if h not in SUPPORTED_HUMAN_TRIGGERS:
                raise UnsupportedError(f"{cid}: unsupported requires_human_when {h!r}")
        if c.get("scope_key") and c["scope_key"] not in scopes:
            raise ValidationError(f"{cid}: unknown scope {c['scope_key']}")
    tree = rule_tree(rule)
    used = []
    _node_ids(tree, used)
    if sorted(used) != sorted(ids):
        raise ValidationError(f"expression must reference every criterion exactly once: used={sorted(used)} defined={sorted(ids)}")
    return tree


def eval_node(node, results):
    """ALL／ANY 節點語意，見 RESOURCE_AND_ELIGIBILITY_ENGINE.md §6.2。"""
    if isinstance(node, str):
        return results[node]
    vals = [eval_node(c, results) for c in node["children"]]
    s = set(vals)
    if node["op"] == "ALL":
        for r in ("UNKNOWN", "FAIL", "FAIL_UNCONFIRMED", "HUMAN"):
            if r in s:
                return r
        return "PASS"
    if node["op"] == "ANY":
        if "PASS" in s:
            return "PASS"
        if "UNKNOWN" in s:
            return "UNKNOWN"
        if "HUMAN" in s:
            return "HUMAN"
        if s == {"FAIL"}:
            return "FAIL"
        return "FAIL_UNCONFIRMED"
    raise UnsupportedError(node["op"])


def resource_result(root, has_human_flag=False):
    """根節點結果 → 資源層級結果，見 §6.3。"""
    table = {
        "PASS": ("LIKELY_ELIGIBLE", None),
        "HUMAN": ("LIKELY_ELIGIBLE", None),
        "UNKNOWN": ("INSUFFICIENT_DATA", None),
        "FAIL_UNCONFIRMED": ("LIKELY_INELIGIBLE", True),
        "FAIL": ("LIKELY_INELIGIBLE", False),
    }
    return table[root]


# ------------------------------------------------------------------ 事實與口徑
def _fact(facts, key):
    f = facts.get(key)
    if f is None or f.get("unknown") or f.get("declined"):
        return None
    v = f["value"]
    if isinstance(v, dict) and ("min" in v or "max" in v):
        raise UnsupportedError(f"range value for {key} is not supported by this runner")
    return f


def region_matches(code, allowed, regions):
    while code:
        if code in allowed:
            return True
        code = regions.get(code, {}).get("parent")
    return False


def scope_members(hh, scope):
    """回傳 (計入成員, 缺漏輸入清單, 判斷所用輸入的最低確認程度)。

    任一成員的判斷事實未知 → 不排除該成員，改回報缺漏（整個條件為 UNKNOWN）。
    """
    inc = scope["member_inclusion"]
    if not hh.get("persons"):
        return [], [f"{hh['id']}:household.members"], 0
    included, missing, conf = [], [], 3
    for p in hh["persons"]:
        keep = True
        unknown = False
        if "relation_in" in inc:
            conf = min(conf, LEVEL[p["relation"]["confirmation_level"]])
            rel = p["relation"]["value"]
            if rel == "UNKNOWN":
                unknown = True
            elif rel not in inc["relation_in"]:
                keep = False
        for attr in ("same_household_registration", "co_residing"):
            if attr in inc:
                f = _fact(p["facts"], f"person.{attr}")
                if f is None:
                    unknown = True
                    missing.append(f"{p['id']}:person.{attr}")
                else:
                    conf = min(conf, _conf(f))
                    if f["value"] != inc[attr]:
                        keep = False
        if unknown and "relation_in" in inc and p["relation"]["value"] == "UNKNOWN":
            missing.append(f"{p['id']}:relation")
        if unknown:
            continue
        if keep:
            included.append(p)
    return included, sorted(set(missing)), conf


def _conf(f):
    return LEVEL[f["confirmation_level"]]


def _min_conf_label(n):
    return f"C{n}"


def eval_criterion(c, hh, scopes, regions):
    """回傳 dict：result、derived、missing、human_trigger、min_conf。"""
    op = c["operator"]
    out = {"result": None, "derived": None, "missing": [], "human_trigger": False}
    min_fail = LEVEL[c.get("min_confirmation_for_fail", "C2")]

    def fail_kind(conf):
        return "FAIL" if conf >= min_fail else "FAIL_UNCONFIRMED"

    if op == "HUMAN_JUDGMENT":
        out["result"] = "HUMAN"
        return out
    facts = hh["facts"]
    if op == "REGION_IN":
        f = _fact(facts, "household.region_code")
        if f is None:
            out.update(result="UNKNOWN", missing=[f"{hh['id']}:household.region_code"])
            return out
        ok = region_matches(f["value"], c["threshold"]["value"], regions)
        out["result"] = "PASS" if ok else fail_kind(_conf(f))
        return out
    if op == "NOT_RECEIVING":
        f = _fact(facts, "household.receiving_resources")
        if f is None:
            out.update(result="UNKNOWN", missing=[f"{hh['id']}:household.receiving_resources"])
            return out
        hit = set(f["value"]) & set(c["threshold"]["value"])
        out["result"] = "PASS" if not hit else fail_kind(_conf(f))
        return out
    if op == "COUNT_MEMBERS_WHERE":
        members, missing, scope_conf = scope_members(hh, scopes[c["scope_key"]])
        if missing:
            out.update(result="UNKNOWN", missing=missing)
            return out
        where = c["threshold"]["where"]
        lo, hi = where["age_between"]
        count, conf, miss = 0, scope_conf, []
        for p in members:
            age = _fact(p["facts"], "person.age")
            sch = _fact(p["facts"], "person.in_school") if where.get("in_school") else {"value": True, "confirmation_level": "C3"}
            if age is None:
                miss.append(f"{p['id']}:person.age")
                continue
            if sch is None:
                miss.append(f"{p['id']}:person.in_school")
                continue
            conf = min(conf, _conf(age), _conf(sch))
            if lo <= age["value"] <= hi and (not where.get("in_school") or sch["value"]):
                count += 1
        if miss:
            out.update(result="UNKNOWN", missing=sorted(miss))
            return out
        out["derived"] = {"count": count}
        out["result"] = "PASS" if count >= c["threshold"]["min_count"] else fail_kind(conf)
        return out
    key = c["input_keys"][0]
    if key == "derived.income_per_capita":
        scope = scopes[c["scope_key"]]
        members, missing, scope_conf = scope_members(hh, scope)
        if missing:
            out.update(result="UNKNOWN", missing=missing)
            return out
        total, conf, miss = 0, scope_conf, []
        for p in members:
            for item in scope["income_definition"]["items"]:
                f = _fact(p["facts"], f"person.{item}")
                if f is None:
                    miss.append(f"{p['id']}:person.{item}")
                    continue
                total += f["value"]
                conf = min(conf, _conf(f))
        if miss:
            out.update(result="UNKNOWN", missing=sorted(miss))
            return out
        value = total / len(members)
        out["derived"] = {"members": len(members), "income_per_capita": round(value)}
    else:
        f = _fact(facts, key)
        if f is None:
            out.update(result="UNKNOWN", missing=[f"{hh['id']}:{key}"])
            return out
        value, conf = f["value"], _conf(f)
    thr = c["threshold"]["value"]
    if op == "EXISTS":
        out["result"] = "PASS"
        return out
    ok = {
        "LTE": lambda: value <= thr, "LT": lambda: value < thr, "GT": lambda: value > thr,
        "GTE": lambda: value >= thr, "EQ": lambda: value == thr, "NEQ": lambda: value != thr,
        "BETWEEN": lambda: thr[0] <= value <= thr[1], "IN": lambda: value in thr,
        "NOT_IN": lambda: value not in thr,
    }[op]()
    out["result"] = "PASS" if ok else fail_kind(conf)
    if "value_within_5_percent_of_threshold" in c.get("requires_human_when", []) and isinstance(thr, (int, float)):
        out["human_trigger"] = abs(value - thr) <= thr * 0.05
    return out


# ------------------------------------------------------------------ 正式推薦
def recommendation_status(res, sources_by_id, as_of):
    """RESOURCE_AND_ELIGIBILITY_ENGINE.md §0.2。回傳 {'status','reasons'}。"""
    v = res["version"]
    hard, soft = [], []
    rule = res.get("rule") or {}
    if rule.get("status", "PUBLISHED") != "PUBLISHED":
        hard.append("RULE_NOT_PUBLISHED")
    else:
        try:
            validate_rule(rule, {})  # 結構檢查；scope 另於評估時檢查
        except UnsupportedError:
            hard.append("RULE_INVALID")
        except ValidationError as e:
            if "unknown scope" not in str(e):
                hard.append("RULE_INVALID")
    status = v["status"]
    risk = res.get("risk_tier", "MEDIUM")
    if status == "PUBLISHED":
        pass
    elif status == "NEEDS_RECHECK":
        if risk == "HIGH":
            hard.append("RECHECK_HIGH_RISK")
        elif v.get("recheck_days", 0) > 14:
            hard.append("RECHECK_GRACE_EXCEEDED")
    else:
        hard.append(f"STATUS_{status}")
    if v["verification_level"] not in ("V2", "V3"):
        hard.append("VERIFICATION_TOO_LOW")
    if v.get("conflict_status", "NONE") == "OPEN":
        hard.append("SOURCE_CONFLICT")
    if any(sources_by_id[s].get("status", "ACTIVE") != "ACTIVE" for s in v["source_ids"]):
        hard.append("SOURCE_INVALID")
    eff_from, eff_to = v.get("effective_from"), v.get("effective_to")
    if v.get("effective_unknown") or eff_to is None:
        soft.append("PERIOD_UNKNOWN")
    if eff_from and as_of < eff_from:
        hard.append("NOT_YET_EFFECTIVE")
    if eff_to and as_of > eff_to:
        hard.append("PERIOD_ENDED")
    win = v.get("application_window", {"type": "UNKNOWN"})
    wt = win.get("type", "UNKNOWN")
    if wt == "UNKNOWN":
        soft.append("WINDOW_UNKNOWN")
    elif wt == "FIXED":
        ranges = win["ranges"]
        if not any(r["from"] <= as_of <= r["to"] for r in ranges):
            if as_of < min(r["from"] for r in ranges):
                hard.append("WINDOW_NOT_OPEN")
            else:
                hard.append("WINDOW_CLOSED")
    elif wt not in ("ROLLING", "WITHIN_MONTHS_OF_EVENT"):
        raise ValidationError(f"unknown application_window type {wt!r}")
    if hard:
        return {"status": "NOT_RECOMMENDED", "reasons": hard + soft}
    if soft:
        return {"status": "MANUAL_CHECK_ONLY", "reasons": soft}
    return {"status": "FORMAL", "reasons": []}


# ------------------------------------------------------------------ 評估
def evaluate(res, hh, scopes, regions, sources_by_id, as_of):
    rec = recommendation_status(res, sources_by_id, as_of)
    out = {"recommendation": rec}
    if rec["status"] == "NOT_RECOMMENDED":
        return out
    tree = validate_rule(res["rule"], scopes)
    crit, derived, missing, human = {}, {}, [], False
    for c in res["rule"]["criteria"]:
        r = eval_criterion(c, hh, scopes, regions)
        crit[c["criterion_id"]] = r["result"]
        missing += r["missing"]
        human = human or r["human_trigger"] or r["result"] == "HUMAN"
        if r["derived"] and "income_per_capita" in r["derived"]:
            derived[c["criterion_id"]] = r["derived"]
    root = eval_node(tree, crit)
    result, unconfirmed = resource_result(root)
    out.update(result=result, criteria=crit)
    if unconfirmed is not None:
        out["unconfirmed"] = unconfirmed
    known_failures = sorted(k for k, v in crit.items() if v in ("FAIL", "FAIL_UNCONFIRMED"))
    flags = set()
    if human:
        flags.add("HUMAN_CHECK")
    if "FAIL_UNCONFIRMED" in crit.values():
        flags.add("CONFIRM_SELF_REPORT")
    if result == "INSUFFICIENT_DATA":
        out["missing_inputs"] = sorted(set(missing))
        if known_failures:
            out["known_failures"] = known_failures
            flags.add("KNOWN_MISMATCH_PRESENT")
    cap = res["version"].get("capacity_status", "UNKNOWN")
    if cap == "FULL":
        flags.add("CAPACITY_FULL")
    elif cap == "UNKNOWN":
        flags.add("CAPACITY_UNCONFIRMED")
    receiving = (hh["facts"].get("household.receiving_resources", {}).get("value") or [])
    if res["resource_key"] in receiving:
        flags.add("ALREADY_RECEIVING")
    if flags:
        out["flags"] = sorted(flags)
    if derived:
        out["derived"] = derived
    return out


# ------------------------------------------------------------------ 取得成果計數（PRD §7.2）
QUALIFYING = {"FIRST_RECEIPT", "FULL_RECEIPT", "PARTIAL_RECEIPT"}


def _active_events(events, known_at):
    seen = [e for e in events if e["recorded_on"] <= known_at]
    voided = {e["voids"] for e in seen if e["event_type"] == "CORRECTION"}
    return [e for e in seen if e["event_type"] != "CORRECTION" and e["id"] not in voided]


def _is_verified(e, known_at):
    v = e.get("verified_by")
    return bool(v) and e.get("verified_on", "9999") <= known_at and v not in (e["recorded_by"], e["case_owner"])


def count_outcomes(events, outcomes, start, end, known_at):
    """回傳新增取得家庭數（區間內首次已驗證取得）、累計家庭數、資源項次、待驗證家庭數。

    - 只認 OutcomeEvent；Outcome.receipt_status（ONGOING／ENDED 等）不影響已發生的取得。
    - 核准、送件、通知、DUPLICATE_PAYMENT_NOTED、PERIOD_CONFIRMED 都不計。
    - 更正事件作廢原事件；報表以 known_at 為資料截止，重算時可呈現更正後結果。
    """
    active = _active_events(events, known_at)
    verified_first_by_household, verified_first_by_outcome, pending = {}, {}, set()
    for e in sorted(active, key=lambda x: x["occurred_on"]):
        if e["event_type"] not in QUALIFYING or e["occurred_on"] > end:
            continue
        o = outcomes[e["outcome"]]
        if e.get("evidence_level") not in ("E1", "E2", "E3"):
            raise ValidationError(f"event {e['id']}: evidence_level E1～E3 required for {e['event_type']}")
        if not o["is_new_to_household"]:
            continue
        if _is_verified(e, known_at):
            verified_first_by_household.setdefault(o["household"], e["occurred_on"])
            verified_first_by_outcome.setdefault(e["outcome"], e["occurred_on"])
        else:
            pending.add(o["household"])
    new_in_window = sorted(h for h, d in verified_first_by_household.items() if start <= d <= end)
    cumulative = sorted(verified_first_by_household)
    items = sorted(o for o, d in verified_first_by_outcome.items() if start <= d <= end)
    return {
        "new_households_in_window": new_in_window,
        "cumulative_households": cumulative,
        "resource_items_in_window": items,
        "pending_verification_households": sorted(pending - set(cumulative)),
    }


# ------------------------------------------------------------------ 狀態機與其他不變條件
def load_machines():
    machines = json.loads((PLATFORM / "state_machines.json").read_text(encoding="utf-8"))["machines"]
    for m in machines.values():
        for t in m["transitions"]:
            if isinstance(t["to"], str):
                t["to"] = [t["to"]]
    return machines


def transition_allowed(machines, machine, current, tid, actor):
    m = machines[machine]
    t = next((x for x in m["transitions"] if x["id"] == tid), None)
    if t is None:
        return False, "unknown transition"
    if current not in t["from"]:
        return False, "wrong source state"
    if actor not in t["actors"]:
        return False, "actor not allowed"
    return True, "ok"


BLOCKING_EXCLUDED = {"DENIED", "WITHDRAWN", "LAPSED"}  # 非封鎖狀態：不核准、撤回、機關認定失效


def application_create_allowed(existing, new):
    """Application 建立規則（DATA_MODEL §2.13）。existing 為既有申請清單。

    - ORIGINAL：同家庭、同資源、同給付期間，不論既有申請處於何種狀態，至多一件（全狀態唯一）。
    - REAPPLY：連結原件，原件須為 DENIED／WITHDRAWN／LAPSED；APPEAL：原件須為 DENIED／LAPSED；
      SUPPLEMENTARY：原件須為 APPROVED 且 R4 核可。皆須理由；同一原件同一種類同時只能有一件進行中。
    """
    def blocking(a):
        return a["status"] not in BLOCKING_EXCLUDED

    if new["kind"] == "ORIGINAL":
        for a in existing:
            if (a["kind"] == "ORIGINAL" and a["household"] == new["household"]
                    and a["resource"] == new["resource"] and a["period"] == new["period"]):
                return False, f"ORIGINAL_EXISTS_{a['status']}"
        return True, "ok"
    if not new.get("related") or not new.get("reason"):
        return False, "RELATION_REQUIRED"
    base = next((a for a in existing if a["id"] == new["related"]), None)
    if base is None:
        return False, "RELATED_NOT_FOUND"
    allowed_from = {"REAPPLY": {"DENIED", "WITHDRAWN", "LAPSED"}, "APPEAL": {"DENIED", "LAPSED"},
                    "SUPPLEMENTARY": {"APPROVED"}}
    if new["kind"] not in allowed_from:
        raise ValidationError(f"unknown kind {new['kind']}")
    if base["status"] not in allowed_from[new["kind"]]:
        return False, f"RELATED_STATE_INVALID_{base['status']}"
    if new["kind"] == "SUPPLEMENTARY" and not new.get("approved_by_r4"):
        return False, "R4_APPROVAL_REQUIRED"
    for a in existing:
        if a["kind"] == new["kind"] and a.get("related") == new["related"] and blocking(a):
            return False, "DUPLICATE_RELATED"
    return True, "ok"


NOTIF_RANK = {"SCHEDULED": 0, "SENDING": 1, "ACCEPTED_BY_PROVIDER": 2, "DELIVERED": 3, "ACKNOWLEDGED": 4}


def apply_notification_events(events, initial="SENDING"):
    """依到達順序套用供應商回呼事件。回傳 (最終狀態, 每個事件是否 applied, late_failure)。"""
    state, seen, applied, late_failure = initial, set(), [], False
    for e in events:
        key = (e["provider"], e["provider_event_id"])
        if key in seen:
            applied.append(False)  # 重複事件
            continue
        seen.add(key)
        t = e["event_type"]
        if t in ("ACCEPTED_BY_PROVIDER", "DELIVERED"):
            if NOTIF_RANK[t] > NOTIF_RANK.get(state, -1) and state != "FAILED":
                state = t
                applied.append(True)
            else:
                applied.append(False)  # 亂序／過時，不回退
        elif t == "FAILED":
            if state in ("DELIVERED", "ACKNOWLEDGED"):
                late_failure = True
                applied.append(False)  # 不回退，建立人工任務
            else:
                state = "FAILED"
                applied.append(True)
        else:
            raise ValidationError(f"unknown event type {t}")
    return state, applied, late_failure


class IdempotencyStore:
    """Idempotency-Key 語意：相同 key＋相同請求回傳原結果；相同 key 不同內容拒絕；處理中回 409。"""

    def __init__(self):
        self.records = {}

    def begin(self, actor, key, request_hash):
        k = (actor, key)
        rec = self.records.get(k)
        if rec is None:
            self.records[k] = {"hash": request_hash, "state": "IN_PROGRESS", "response": None}
            return "PROCEED", None
        if rec["hash"] != request_hash:
            return "REJECT_422", None
        if rec["state"] == "IN_PROGRESS":
            return "REJECT_409_IN_PROGRESS", None
        return "REPLAY", rec["response"]

    def complete(self, actor, key, response):
        rec = self.records[(actor, key)]
        rec.update(state="DONE", response=response)
