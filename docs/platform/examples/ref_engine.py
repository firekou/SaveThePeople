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
NODE_KEYS = {"op", "children"}  # expression 節點只允許這兩個鍵；任何其他鍵（含 not、空字串鍵）一律拒絕
SUPPORTED_HUMAN_TRIGGERS = {"value_within_5_percent_of_threshold"}
RESULTS = ("PASS", "FAIL", "FAIL_UNCONFIRMED", "UNKNOWN", "HUMAN")


class UnsupportedError(Exception):
    """規格允許或預見、但此 runner／引擎不支援的語意。"""


class ValidationError(Exception):
    """規則、資料或輸入不合法，必須拒絕。"""


def load_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 規則與口徑驗證（F-01、F-02）
# 設計：先「收集」所有問題（不在第一個問題就中止），再決定拋出哪一種錯誤。
# 因此非法條件出現在哪個位置、前面是否有其他問題，都不影響「拒絕」這個結果。
# 規格上有、但此 runner 不支援者列在 UNSUPPORTED_*；未知的鍵一律視為 ValidationError，絕不略過。
RELATION_VALUES = {"SELF", "SPOUSE", "PARTNER", "CHILD", "PARENT", "GRANDPARENT", "GRANDCHILD", "SIBLING", "OTHER_RELATIVE", "NON_RELATIVE"}
YES_NO = {"YES", "NO"}
SCOPE_TOP_KEYS = {"scope_key", "label_plain", "member_inclusion", "income_definition", "property_definition", "source_ref"}
INCLUSION_SUPPORTED = {"relation_in", "same_household_registration", "co_residing"}
INCLUSION_UNSUPPORTED = {"age_between", "in_school", "military_service", "exclusions"}  # 規格 §2.6 提到年齡、就學、服役
INCOME_KEYS_SUPPORTED = {"items", "period"}
INCOME_KEYS_UNSUPPORTED = {"include_imputed_income", "imputed_income"}
INCOME_ITEMS_SUPPORTED = {"monthly_earned_income", "monthly_pension"}
INCOME_PERIODS_SUPPORTED = {"MONTHLY_AVERAGE"}
INCOME_PERIODS_UNSUPPORTED = {"ANNUAL", "ANNUAL_AVERAGE"}
WHERE_SUPPORTED = {"age_between", "in_school"}
WHERE_UNSUPPORTED = {"relation_in", "co_residing", "same_household_registration"}
CRITERION_KEYS = {"criterion_id", "label_plain", "operator", "input_keys", "threshold", "source_ref", "scope_key",
                  "min_confirmation_for_fail", "requires_human_when", "discretionary", "on_missing", "explain_template"}
RULE_KEYS = {"rule_version", "combinator", "criteria", "expression", "status", "test_cases", "authoring_origin", "authored_by", "reviewed_by"}
RULE_STATUSES = {"DRAFT", "IN_REVIEW", "PUBLISHED", "RETIRED"}
NUMERIC_OPS = {"LT", "LTE", "GT", "GTE"}
COMPARE_OPS = NUMERIC_OPS | {"EQ", "NEQ", "BETWEEN", "IN", "NOT_IN"}


def _in(v, allowed):
    """v 必須是字串且在 allowed 內；非字串（含不可雜湊的 list／dict）一律視為不在內，不拋 TypeError。"""
    return isinstance(v, str) and v in allowed


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def scope_problems(scope):
    """口徑定義（HouseholdScopeDefinition）的結構問題；回傳 [(錯誤類別, 訊息)]。"""
    P = []
    if not isinstance(scope, dict):
        return [(ValidationError, "scope must be an object")]
    key = scope.get("scope_key", "?")
    for k in scope:
        if k not in SCOPE_TOP_KEYS:
            P.append((ValidationError, f"{key}: unknown scope key {k!r}"))
    if not scope.get("source_ref"):
        P.append((ValidationError, f"{key}: source_ref required"))
    if "property_definition" in scope:
        P.append((UnsupportedError, f"{key}: property_definition is not supported by this runner"))
    inc = scope.get("member_inclusion")
    if not isinstance(inc, dict) or not inc:
        P.append((ValidationError, f"{key}: member_inclusion must be a non-empty object (an empty scope would silently include everyone)"))
    else:
        for k, v in inc.items():
            if k in INCLUSION_UNSUPPORTED:
                P.append((UnsupportedError, f"{key}: member_inclusion.{k} is not supported by this runner"))
            elif k not in INCLUSION_SUPPORTED:
                P.append((ValidationError, f"{key}: unknown member_inclusion key {k!r}"))
            elif k == "relation_in":
                if not isinstance(v, list) or not v or not all(isinstance(x, str) and x in RELATION_VALUES for x in v):
                    P.append((ValidationError, f"{key}: relation_in must be a non-empty list of relation values"))
            elif not _in(v, YES_NO):
                P.append((ValidationError, f"{key}: {k} must be \"YES\" or \"NO\""))
    inc_def = scope.get("income_definition")
    if not isinstance(inc_def, dict):
        P.append((ValidationError, f"{key}: income_definition must be an object"))
    else:
        for k in inc_def:
            if k in INCOME_KEYS_UNSUPPORTED:
                P.append((UnsupportedError, f"{key}: income_definition.{k} is not supported by this runner"))
            elif k not in INCOME_KEYS_SUPPORTED:
                P.append((ValidationError, f"{key}: unknown income_definition key {k!r}"))
        items = inc_def.get("items")
        if not isinstance(items, list) or not items or not all(isinstance(x, str) and x in INCOME_ITEMS_SUPPORTED for x in items):
            P.append((ValidationError, f"{key}: income_definition.items must be a non-empty list from {sorted(INCOME_ITEMS_SUPPORTED)}"))
        period = inc_def.get("period")
        if _in(period, INCOME_PERIODS_UNSUPPORTED):
            P.append((UnsupportedError, f"{key}: income period {period} is not supported by this runner"))
        elif not _in(period, INCOME_PERIODS_SUPPORTED):
            P.append((ValidationError, f"{key}: income_definition.period must be one of {sorted(INCOME_PERIODS_SUPPORTED)}"))
    return P


def where_problems(cid, threshold):
    P = []
    where = threshold.get("where")
    if not isinstance(where, dict) or not where:
        return [(ValidationError, f"{cid}: COUNT_MEMBERS_WHERE needs threshold.where")]
    for k, v in where.items():
        if k in WHERE_UNSUPPORTED:
            P.append((UnsupportedError, f"{cid}: where.{k} is not supported by this runner"))
        elif k not in WHERE_SUPPORTED:
            P.append((ValidationError, f"{cid}: unknown where key {k!r}"))
        elif k == "age_between":
            if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in v) and 0 <= v[0] <= v[1]):
                P.append((ValidationError, f"{cid}: where.age_between must be [lo, hi] integers with 0 <= lo <= hi"))
        elif k == "in_school" and not isinstance(v, bool):
            P.append((ValidationError, f"{cid}: where.in_school must be a boolean"))
    if "age_between" not in where:
        P.append((ValidationError, f"{cid}: where.age_between is required by this runner"))
    mc = threshold.get("min_count")
    if not (isinstance(mc, int) and not isinstance(mc, bool) and mc >= 1):
        P.append((ValidationError, f"{cid}: threshold.min_count must be an integer >= 1"))
    for k in threshold:
        if k not in ("where", "min_count"):
            P.append((ValidationError, f"{cid}: unknown threshold key {k!r} for COUNT_MEMBERS_WHERE"))
    return P


def criterion_problems(c, scopes):
    P = []
    if not isinstance(c, dict):
        return [(ValidationError, "criterion must be an object")]
    cid = c.get("criterion_id")
    if not isinstance(cid, str) or not cid:
        P.append((ValidationError, f"missing criterion_id in {c!r}"))
        cid = "?"
    for k in c:
        if k not in CRITERION_KEYS:
            P.append((ValidationError, f"{cid}: unknown criterion key {k!r}"))
    op = c.get("operator")
    if _in(op, UNSUPPORTED_OPERATORS):
        P.append((UnsupportedError, f"{cid}: operator {op} is not supported by this runner"))
        return P
    if not _in(op, SUPPORTED_OPERATORS):
        P.append((ValidationError, f"{cid}: unknown operator {op!r}"))
        return P
    if not c.get("source_ref"):
        P.append((ValidationError, f"{cid}: source_ref required"))
    if not _in(c.get("min_confirmation_for_fail", "C2"), ("C2", "C3")):
        P.append((ValidationError, f"{cid}: min_confirmation_for_fail must be C2 or C3 (self-report can never confirm a failure)"))
    rh = c.get("requires_human_when", [])
    if not isinstance(rh, list):
        P.append((ValidationError, f"{cid}: requires_human_when must be a list"))
    else:
        for h in rh:
            if not _in(h, SUPPORTED_HUMAN_TRIGGERS):
                P.append((UnsupportedError, f"{cid}: unsupported requires_human_when {h!r}"))
        if rh and op not in NUMERIC_OPS:
            P.append((ValidationError, f"{cid}: requires_human_when needs a numeric comparison operator"))
    if "discretionary" in c and not isinstance(c["discretionary"], bool):
        P.append((ValidationError, f"{cid}: discretionary must be a boolean"))
    if c.get("on_missing", "INSUFFICIENT") != "INSUFFICIENT":
        P.append((UnsupportedError, f"{cid}: on_missing other than INSUFFICIENT is not supported"))
    sk = c.get("scope_key")
    if sk is not None:
        if not _in(sk, scopes):
            P.append((ValidationError, f"{cid}: unknown scope {sk!r}"))
    ik = c.get("input_keys")
    th = c.get("threshold")
    if op == "HUMAN_JUDGMENT":
        return P
    if not isinstance(ik, list) or not all(isinstance(x, str) for x in ik):
        P.append((ValidationError, f"{cid}: input_keys must be a list of strings"))
        ik = []
    if not isinstance(th, dict):
        P.append((ValidationError, f"{cid}: threshold must be an object"))
        return P
    if op == "COUNT_MEMBERS_WHERE":
        if not sk:
            P.append((ValidationError, f"{cid}: COUNT_MEMBERS_WHERE requires scope_key"))
        P += where_problems(cid, th)
        return P
    if "value" not in th:
        P.append((ValidationError, f"{cid}: threshold.value required"))
        return P
    v = th["value"]
    if op == "REGION_IN":
        if ik != ["household.region_code"]:
            P.append((ValidationError, f"{cid}: REGION_IN input_keys must be [\"household.region_code\"]"))
        if not (isinstance(v, list) and v and all(isinstance(x, str) for x in v)):
            P.append((ValidationError, f"{cid}: REGION_IN threshold.value must be a non-empty list of region codes"))
        return P
    if op == "NOT_RECEIVING":
        if ik != ["household.receiving_resources"]:
            P.append((ValidationError, f"{cid}: NOT_RECEIVING input_keys must be [\"household.receiving_resources\"]"))
        if not (isinstance(v, list) and v and all(isinstance(x, str) for x in v)):
            P.append((ValidationError, f"{cid}: NOT_RECEIVING threshold.value must be a non-empty list of resource keys"))
        return P
    # 一般比較運算子
    if len(ik) != 1:
        P.append((ValidationError, f"{cid}: {op} needs exactly one input key"))
    else:
        k = ik[0]
        if k == "derived.income_per_capita":
            if not sk:
                P.append((ValidationError, f"{cid}: derived.income_per_capita requires scope_key"))
        elif k.startswith("person."):
            P.append((UnsupportedError, f"{cid}: per-member input {k} cannot be compared directly in this runner"))
        elif not k.startswith("household."):
            P.append((ValidationError, f"{cid}: unknown input key namespace {k!r}"))
    if op in NUMERIC_OPS and not _num(v):
        P.append((ValidationError, f"{cid}: {op} threshold.value must be a number"))
    elif op in ("EQ", "NEQ") and not (isinstance(v, (str, bool)) or _num(v)):
        P.append((ValidationError, f"{cid}: {op} threshold.value must be a scalar"))
    elif op == "BETWEEN" and not (isinstance(v, list) and len(v) == 2 and all(_num(x) for x in v) and v[0] <= v[1]):
        P.append((ValidationError, f"{cid}: BETWEEN threshold.value must be [lo, hi] numbers with lo <= hi"))
    elif op in ("IN", "NOT_IN") and not (isinstance(v, list) and v):
        P.append((ValidationError, f"{cid}: {op} threshold.value must be a non-empty list"))
    return P


def _expr_problems(node, out_ids, P, depth=0):
    if isinstance(node, str):
        out_ids.append(node)
        return
    if not isinstance(node, dict) or "op" not in node:
        P.append((ValidationError, f"bad expression node: {node!r}"))
        return
    for k in node if _in(node["op"], KNOWN_NODE_OPS) else ():  # 不支援的 op（如 N_OF_M 的 n）只報 Unsupported，不混報鍵錯誤
        if not isinstance(k, str) or k not in NODE_KEYS:
            # 未知鍵所表達的限制若被忽略，就會在使用者看不到的情況下改變結果，所以逐節點、遞迴拒絕。
            P.append((ValidationError, f"unknown expression node key {k!r} (allowed: op, children)"))
    if not _in(node["op"], KNOWN_NODE_OPS):
        P.append((UnsupportedError, f"unsupported combinator node op: {node['op']!r}"))
    children = node.get("children")
    if not isinstance(children, list) or not children:
        P.append((ValidationError, "expression node needs a non-empty children list"))
        return
    for ch in children:
        _expr_problems(ch, out_ids, P, depth + 1)


def rule_problems(rule, scopes):
    """收集一份規則的全部問題。scopes 必須是完整的口徑表（不可為空表來「略過」口徑驗證）。"""
    P = []
    if not isinstance(rule, dict):
        return [(ValidationError, "rule must be an object")]
    for k in rule:
        if k not in RULE_KEYS:
            P.append((ValidationError, f"unknown rule key {k!r}"))
    comb = rule.get("combinator")
    if not _in(comb, SUPPORTED_COMBINATORS):
        P.append((UnsupportedError, f"unsupported combinator: {comb!r}"))
    crits = rule.get("criteria")
    ids = []
    if not isinstance(crits, list) or not crits:
        P.append((ValidationError, "criteria must be a non-empty list"))
        crits = []
    for c in crits:
        P += criterion_problems(c, scopes)
        cid = c.get("criterion_id") if isinstance(c, dict) else None
        if isinstance(cid, str) and cid:
            if cid in ids:
                P.append((ValidationError, f"duplicate criterion_id {cid!r}"))
            ids.append(cid)
    used_scopes = {c["scope_key"] for c in crits if isinstance(c, dict) and _in(c.get("scope_key"), scopes)}
    for sk in sorted(used_scopes):
        for cls, msg in scope_problems(scopes[sk]):
            P.append((cls, f"scope {sk}: {msg}"))
    if comb in ("ALL", "ANY"):
        if "expression" in rule:
            P.append((ValidationError, "expression is only allowed with CUSTOM"))
    elif comb == "CUSTOM":
        if "expression" not in rule:
            P.append((ValidationError, "CUSTOM requires expression"))
        else:
            used = []
            _expr_problems(rule["expression"], used, P)
            if sorted(used) != sorted(ids):
                P.append((ValidationError, f"expression must reference every criterion exactly once: used={sorted(used)} defined={sorted(ids)}"))
    return P


def raise_first(problems):
    """有任何 ValidationError 時拋 ValidationError；否則有 UnsupportedError 才拋 UnsupportedError。"""
    if not problems:
        return
    val = [m for c, m in problems if c is ValidationError]
    if val:
        raise ValidationError("; ".join(val))
    raise UnsupportedError("; ".join(m for _, m in problems))


def rule_tree(rule):
    """回傳正規化的樹狀表達式（假設規則已通過驗證）。"""
    comb = rule["combinator"]
    if comb in ("ALL", "ANY"):
        return {"op": comb, "children": [c["criterion_id"] for c in rule["criteria"]]}
    return rule["expression"]


def validate_rule(rule, scopes):
    """完整驗證規則＋它引用的口徑；scopes 為必要參數。回傳樹狀表達式。"""
    if scopes is None:
        raise TypeError("validate_rule requires the full scopes mapping")
    raise_first(rule_problems(rule, scopes))
    return rule_tree(rule)


def validate_scope(scope):
    raise_first(scope_problems(scope))


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
    validate_scope(scope)  # 未知或不支援的口徑鍵一律報錯，不略過
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
VERSION_REQUIRED = ("status", "verification_level", "source_ids", "application_window", "effective_from", "effective_to", "effective_unknown")
VERSION_STATUSES = {"CANDIDATE", "DRAFT", "IN_REVIEW", "PUBLISHED", "NEEDS_RECHECK", "SUSPENDED", "SUPERSEDED", "EXPIRED", "RETIRED"}
RECHECK_GRACE_DAYS = 14  # OP-08（暫行）


def recheck_days(recheck_started_at, as_of):
    """重查寬限已過天數＝as_of 日期 − 進入 NEEDS_RECHECK 的日期（日曆天，Asia/Taipei；此處以 ISO 日期字串表示）。"""
    if not isinstance(recheck_started_at, str):
        return None
    try:
        d0 = date.fromisoformat(recheck_started_at)
    except ValueError:
        return None
    d1 = date.fromisoformat(as_of[:10])
    return (d1 - d0).days


def recommendation_status(res, sources_by_id, as_of, scopes):
    """RESOURCE_AND_ELIGIBILITY_ENGINE.md §0.2。回傳 {'status','reasons'}。

    scopes 必須是完整口徑表：規則一律完整驗證（含它引用的口徑），驗證未完成或失敗＝RULE_INVALID，
    不會因為「口徑查不到」而略過後續條件或 CUSTOM expression。
    """
    if scopes is None:
        raise TypeError("recommendation_status requires the full scopes mapping")
    v = res["version"]
    hard, soft = [], []
    rule = res.get("rule")
    if not isinstance(rule, dict):
        hard.append("RULE_MISSING")
    else:
        st = rule.get("status")
        if st is None:
            hard.append("RULE_STATUS_MISSING")
        elif not _in(st, RULE_STATUSES):
            hard.append("RULE_INVALID")
        elif st != "PUBLISHED":
            hard.append("RULE_NOT_PUBLISHED")
        if rule_problems(rule, scopes) and "RULE_INVALID" not in hard:
            hard.append("RULE_INVALID")
    missing = [k for k in VERSION_REQUIRED if k not in v]
    if missing or not _in(v.get("status"), VERSION_STATUSES) or not isinstance(v.get("source_ids"), list) or not v.get("source_ids") \
            or not isinstance(v.get("effective_unknown"), bool) or not isinstance(v.get("application_window"), dict):
        hard.append("VERSION_INVALID")
        return {"status": "NOT_RECOMMENDED", "reasons": hard}
    if v["effective_unknown"] != (v["effective_to"] is None):
        hard.append("VERSION_INVALID")  # effective_unknown 必須與 effective_to 是否為空一致（CHECK 約束）
        return {"status": "NOT_RECOMMENDED", "reasons": hard}
    status = v["status"]
    if status != "NEEDS_RECHECK" and v.get("recheck_started_at") is not None:
        # DATA_MODEL §2.4.1：recheck_started_at 只在 NEEDS_RECHECK 存在；離開該狀態（RV-08／09／12／13）即清除，
        # 歷史留在 AuditEvent。其他狀態帶著起算日是不合法的狀態×欄位組合。
        hard.append("VERSION_INVALID")
        return {"status": "NOT_RECOMMENDED", "reasons": hard}
    risk = res.get("risk_tier", "MEDIUM")
    if status == "PUBLISHED":
        pass
    elif status == "NEEDS_RECHECK":
        started = v.get("recheck_started_at")
        days = None
        if not started:
            hard.append("RECHECK_START_MISSING")
        else:
            days = recheck_days(started, as_of)
            if days is None or days < 0:
                hard.append("RECHECK_START_INVALID")
                days = None
        if risk == "HIGH":
            hard.append("RECHECK_HIGH_RISK")
        elif days is not None and days > RECHECK_GRACE_DAYS:
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
    if v["effective_unknown"]:
        soft.append("PERIOD_UNKNOWN")
    if eff_from and as_of < eff_from:
        hard.append("NOT_YET_EFFECTIVE")
    if eff_to and as_of > eff_to:
        hard.append("PERIOD_ENDED")
    win = v["application_window"]
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
    rec = recommendation_status(res, sources_by_id, as_of, scopes)
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


def apply_version_transition(machines, version, tid, actor, trigger_date=None):
    """ResourceVersion 轉換的欄位效果（DATA_MODEL §2.4.1 狀態×欄位生命週期）。回傳新的 version（不改原物件）。

    recheck_started_at 只存在於 NEEDS_RECHECK：進入（RV-07）寫入 trigger_date（每次重新進入都是新的起算日），
    離開（RV-08／09／12／13）一律清除，歷史留在 AuditEvent。非法轉換、缺或格式不合的 trigger_date 都拒絕。
    """
    ok, why = transition_allowed(machines, "resource_version", version["status"], tid, actor)
    if not ok:
        raise ValidationError(f"{tid}: {why}")
    t = next(x for x in machines["resource_version"]["transitions"] if x["id"] == tid)
    new = dict(version)
    new["status"] = t["to"][0]
    if new["status"] == "NEEDS_RECHECK":
        try:
            ok_date = isinstance(trigger_date, str) and date.fromisoformat(trigger_date) is not None
        except ValueError:
            ok_date = False
        if not ok_date:
            raise ValidationError(f"{tid}: entering NEEDS_RECHECK requires an ISO-date trigger_date")
        new["recheck_started_at"] = trigger_date
    else:
        new["recheck_started_at"] = None
    return new


BLOCKING_EXCLUDED = {"DENIED", "WITHDRAWN", "LAPSED"}  # 非封鎖狀態：不核准、撤回、機關認定失效
KINDS = ("ORIGINAL", "REAPPLY", "APPEAL", "SUPPLEMENTARY")
RELATED_ALLOWED_FROM = {"REAPPLY": {"DENIED", "WITHDRAWN", "LAPSED"}, "APPEAL": {"DENIED", "LAPSED"}, "SUPPLEMENTARY": {"APPROVED"}}


def _blocking(a):
    return a["status"] not in BLOCKING_EXCLUDED


def _relation_checks(base, app, others):
    """關聯件（REAPPLY／APPEAL／SUPPLEMENTARY）的共同規則：建立時與送件前（AP-06）都用同一組檢查。

    others 必須已排除「目前這件申請本身」。回傳 (ok, 原因)。
    """
    kind = app["kind"]
    if kind not in RELATED_ALLOWED_FROM:
        raise ValidationError(f"unknown related kind {kind}")
    if not app.get("related") or not app.get("reason"):
        return False, "RELATION_REQUIRED"
    if base is None:
        return False, "RELATED_NOT_FOUND"
    if base["household"] != app["household"]:
        return False, "RELATION_MISMATCH_HOUSEHOLD"
    if base["resource"] != app["resource"]:
        return False, "RELATION_MISMATCH_RESOURCE"
    if base["period"] != app["period"]:
        return False, "RELATION_MISMATCH_PERIOD"
    if base["status"] not in RELATED_ALLOWED_FROM[kind]:
        return False, f"RELATED_STATE_INVALID_{base['status']}"
    if kind == "SUPPLEMENTARY" and not app.get("relation_approved_by"):
        return False, "R4_APPROVAL_REQUIRED"
    for a in others:
        if a["kind"] == kind and a.get("related") == app["related"] and _blocking(a):
            return False, "DUPLICATE_RELATED"
    return True, "ok"


def application_create_allowed(existing, new):
    """Application 建立規則（DATA_MODEL §2.13、§2.13.1）。existing 為既有申請清單（不含 new）。

    - ORIGINAL：同家庭、同資源、同給付期間，不論既有申請處於何種狀態，至多一件（全狀態唯一）。
    - REAPPLY／APPEAL／SUPPLEMENTARY：必須連結同家庭、同資源、同給付期間的原件，且原件狀態符合條件並附理由；
      SUPPLEMENTARY 另需 R4 核可（relation_approved_by）；同一原件同一種類同時只能有一件進行中。
    """
    if new["kind"] not in KINDS:
        raise ValidationError(f"unknown kind {new['kind']}")
    if new["kind"] == "ORIGINAL":
        for a in existing:
            if (a["kind"] == "ORIGINAL" and a["household"] == new["household"]
                    and a["resource"] == new["resource"] and a["period"] == new["period"]):
                return False, f"ORIGINAL_EXISTS_{a['status']}"
        return True, "ok"
    base = next((a for a in existing if a["id"] == new.get("related")), None)
    return _relation_checks(base, new, existing)


def application_ready_check(existing, app_id):
    """AP-06（PREPARING_DOCS→READY_TO_SUBMIT）的「送件前防重複」，依 kind 分別定義，並排除申請本身。

    existing 為所有申請（含 app_id 本身）；app_id 的那一件會被排除在「其他申請」之外。
    """
    app = next(a for a in existing if a["id"] == app_id)
    others = [a for a in existing if a["id"] != app_id]
    if app["kind"] == "ORIGINAL":
        for a in others:
            if (a["kind"] == "ORIGINAL" and a["household"] == app["household"]
                    and a["resource"] == app["resource"] and a["period"] == app["period"]):
                return False, f"ORIGINAL_DUPLICATE_{a['status']}"
        return True, "ok"
    base = next((a for a in others if a["id"] == app.get("related")), None)
    return _relation_checks(base, app, others)


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


RESPONSE_SHAPE_KEYS = {"status_code", "resource_ref", "shape_version"}


class IdempotencyStore:
    """Idempotency-Key 語意（ARCHITECTURE §6、§6.3；F-05）。

    - 相同 key＋相同請求內容→重播；相同 key＋不同內容→422；相同 key 仍在處理中→409。
    - **只存回應形狀**：{status_code, resource_ref{type,id}, shape_version}，不存任何內容；request_hash 為金鑰雜湊。
    - 重播時由 resolver 以「當下」的權限、同意與刪除狀態重新取得內容；已失去存取資格或已刪除則不回內容。
    """

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
        if set(response) != RESPONSE_SHAPE_KEYS or set(response["resource_ref"]) != {"type", "id"}:
            raise ValidationError(f"idempotency response must be exactly {sorted(RESPONSE_SHAPE_KEYS)} with resource_ref {{type,id}}: got {response!r}")
        rec = self.records[(actor, key)]
        rec.update(state="DONE", response=response)

    def replay(self, actor, key, request_hash, resolver):
        """重播：回傳 (http 狀態, 內容或 None)。resolver(actor, resource_ref) -> ("OK", 當下內容)｜("FORBIDDEN", None)｜("GONE", None)。"""
        decision, stored = self.begin(actor, key, request_hash)
        if decision != "REPLAY":
            return decision, None
        verdict, content = resolver(actor, stored["resource_ref"])
        if verdict == "OK":
            return stored["status_code"], content
        return {"FORBIDDEN": 403, "GONE": 410}[verdict], None
