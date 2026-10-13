#!/usr/bin/env python3
"""權限單一事實來源 permissions.json 的產生與政策檢查（只使用標準函式庫）。

用法：
  python3 docs/platform/tools/gen_permissions.py           # 重新產生文件中的權限區塊
  python3 docs/platform/tools/gen_permissions.py --check   # 檢查文件與 JSON 一致，且政策檢查全數通過（失敗 exit 1）

產生的區塊：
  1. PRODUCT_REQUIREMENTS.md §4.2 的權限矩陣（markers：permission_matrix）
  2. ARCHITECTURE.md §6 API 表的「權限」欄（以 endpoint 字串對應）
  3. USER_JOURNEYS_AND_SCREENS.md 每個頁面（### P<n>）的「- 權限：」行

政策檢查（policy_problems）是**文件政策檢查**：檢查矩陣、API、頁面、狀態機之間是否自洽、是否違反角色限制。
它不是產品的授權行為測試（那是 T-19、T-32～T-35、T-50、T-51，待 WP-08 實作後以產品驗證）。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERM = ROOT / "permissions.json"
SM = ROOT / "state_machines.json"
PRD = ROOT / "PRODUCT_REQUIREMENTS.md"
ARCH = ROOT / "ARCHITECTURE.md"
JOUR = ROOT / "USER_JOURNEYS_AND_SCREENS.md"

ROLES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"]
CASE_SCOPES_BY_ROLE = {
    "R1": {"OWN", "TOKEN"}, "R2": {"GRANT", "TOKEN", "SELF"}, "R3": {"ASG", "VERIFY"}, "R4": {"SITE-REV"},
    "R5": set(), "R6": {"REF"}, "R7": {"BG"}, "R8": {"AGG"}, "R9": {"SAMPLE"},
}
R6_CASE_CLASSES = {"case_profile", "case_sensitive", "consent", "application", "referral", "case_task", "outcome_event"}


def load():
    return json.loads(PERM.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 產生
def cell(entries):
    if not entries:
        return "—"
    parts = []
    for e in entries:
        t = f"{e['actions']}·{e['scope']}"
        if e.get("note"):
            t += f"（{e['note']}）"
        parts.append(t)
    return "；".join(parts)


def render_matrix(data):
    lines = ["| 資料類別 | " + " | ".join(ROLES) + " |", "|---|" + "---|" * len(ROLES)]
    for c in data["classes"]:
        row = [cell(data["matrix"][c["id"]].get(r, [])) for r in ROLES]
        lines.append(f"| {c['label']} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_grants(grants, note=""):
    t = "、".join(grants)
    return t + (f"（{note}）" if note else "")


def render_page_line(page):
    secs = page["sections"]
    if len(secs) == 1:
        s = secs[0]
        return "- 權限：" + render_grants(s["grants"], s["note"])
    return "- 權限：" + "；".join(f"{s['label']}：{render_grants(s['grants'], s['note'])}" for s in secs)


def sync(data):
    """回傳 {path: 新內容}。"""
    out = {}
    # PRD 矩陣
    prd = PRD.read_text(encoding="utf-8")
    pat = re.compile(r"<!-- BEGIN GENERATED:permission_matrix.*?<!-- END GENERATED:permission_matrix -->", re.S)
    if not pat.search(prd):
        raise SystemExit("PRODUCT_REQUIREMENTS.md 缺少 permission_matrix 標記")
    block = ("<!-- BEGIN GENERATED:permission_matrix (來源：permissions.json，請勿手改) -->\n" + render_matrix(data)
             + "\n<!-- END GENERATED:permission_matrix -->")
    prd = pat.sub(lambda _m: block, prd)
    pat2 = re.compile(r"<!-- BEGIN GENERATED:permission_scopes.*?<!-- END GENERATED:permission_scopes -->", re.S)
    if not pat2.search(prd):
        raise SystemExit("PRODUCT_REQUIREMENTS.md 缺少 permission_scopes 標記")
    sblock = ("<!-- BEGIN GENERATED:permission_scopes (來源：permissions.json，請勿手改) -->\n| 範圍代碼 | 意義 |\n|---|---|\n"
              + "\n".join(f"| {k} | {v} |" for k, v in data["scopes"].items()) + "\n<!-- END GENERATED:permission_scopes -->")
    out[PRD] = pat2.sub(lambda _m: sblock, prd)
    # ARCH API 權限欄
    arch = ARCH.read_text(encoding="utf-8").splitlines()
    api = {a["endpoint"]: a for a in data["api"]}
    external = set(data.get("api_external", {}))
    for i, line in enumerate(arch):
        if line.startswith("| `") and "/api/" in line:
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            ep = cols[0].strip("`")
            if ep in api and len(cols) == 6:
                cols[4] = render_grants(api[ep]["grants"], api[ep]["note"])
                arch[i] = "| " + " | ".join(cols[:0] + [("`" + ep + "`")] + cols[1:]) + " |"
            elif ep in external and len(cols) == 6:
                cols[4] = data["api_external"][ep]
                arch[i] = "| " + " | ".join(["`" + ep + "`"] + cols[1:]) + " |"
    out[ARCH] = "\n".join(arch) + "\n"
    # JOURNEYS 頁面
    jr = JOUR.read_text(encoding="utf-8").splitlines()
    pages = {p["page"]: p for p in data["pages"]}
    cur = None
    for i, line in enumerate(jr):
        m = re.match(r"^### (P\d+) ", line)
        if m:
            cur = m.group(1)
        elif line.startswith("### "):
            cur = None
        elif cur in pages and line.startswith("- 權限："):
            jr[i] = render_page_line(pages[cur])
    out[JOUR] = "\n".join(jr) + "\n"
    return out


def doc_inventory():
    """文件中實際存在的 API endpoint 與頁面，供與 JSON 比對。"""
    eps = []
    for line in ARCH.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `") and "/api/" in line:
            eps.append(line.strip("| ").split("|")[0].strip().strip("`"))
    pages = re.findall(r"^### (P\d+) ", JOUR.read_text(encoding="utf-8"), re.M)
    return eps, pages


# ------------------------------------------------------------------ 政策檢查
def grant_parts(g):
    role, _, scope = g.partition("·")
    return role, scope


def entry_allows(data, cls, role, scope, letters):
    for e in data["matrix"].get(cls, {}).get(role, []):
        if e["scope"] == scope and set(letters) <= set(e["actions"]):
            return True
    return False


def grant_ok(data, cls, grant, action):
    role, scope = grant_parts(grant)
    if role == "PUBLIC":
        kind = next(c["kind"] for c in data["classes"] if c["id"] == cls)
        if kind == "public" and scope == "ALL-PUB" and action == "V":
            return True
        return entry_allows(data, cls, "R1", scope, action) and scope == "TOKEN"
    return entry_allows(data, cls, role, scope, action)


VERIFIER_LABEL = {"registrant": "登錄人", "case_owner": "案件責任人", "case_owner_delegate": "代班責任人"}
VERIFIER_REQUIRED = ["registrant", "case_owner", "case_owner_delegate"]


def verify_note(api):
    """N-04：verify API 的 note 由結構化的 verifier_must_not_be 衍生，不接受自由文字覆蓋。"""
    return "驗證人≠" + "、≠".join(VERIFIER_LABEL[k] for k in api["verifier_must_not_be"]) + "；R3 不因此取得該案其他資料"


def verifier_allowed(api, verifier, record):
    """參考判斷：驗證人不得是登錄人、案件責任人或代班責任人。回傳 (是否允許, 原因)。

    record = {"registrant": id, "case_owner": id, "case_owner_delegates": [id, ...]}；verifier 為使用者 id。
    """
    for k in api["verifier_must_not_be"]:
        who = record.get("case_owner_delegates", []) if k == "case_owner_delegate" else [record.get(k)]
        if verifier in who:
            return False, f"VERIFIER_IS_{k.upper()}"
    return True, "ok"


def limit_phrase(limits, machine):
    """由狀態機轉換的目標狀態衍生「暫停」「停用」用語（SUSPENDED＝暫停、RETIRED＝停用）。"""
    verbs = []
    for tid in limits:
        t = next(x for x in machine["transitions"] if x["id"] == tid)
        to = [t["to"]] if isinstance(t["to"], str) else list(t["to"])
        v = "暫停" if to == ["SUSPENDED"] else "停用" if to == ["RETIRED"] else "?"
        if v not in verbs:
            verbs.append(v)
    verbs.sort(key={"暫停": 0, "停用": 1, "?": 2}.get)
    return "／".join(verbs) + "轉換 " + "、".join(limits)


def derived_resource_notes(data, machines):
    """N-04：R4／R7 在資源內部資料的限制文字（矩陣、API 權限欄、P9 頁面）一律由 transition_limits 衍生。"""
    m = machines["resource_version"]
    out = {}
    for role in ("R4", "R7"):
        for e in data["matrix"]["resource_internal"].get(role, []):
            if "transition_limits" in e:
                out[role] = limit_phrase(e["transition_limits"], m)
    return out


def policy_problems(data, machines=None):
    P = []
    kinds = {c["id"]: c["kind"] for c in data["classes"]}
    case_classes = {k for k, v in kinds.items() if v == "case"}
    scopes = set(data["scopes"])
    matrix = data["matrix"]
    for cls, per_role in matrix.items():
        if cls not in kinds:
            P.append(f"matrix: unknown class {cls}")
        for role, entries in per_role.items():
            if role not in ROLES:
                P.append(f"matrix {cls}: unknown role {role}")
            for e in entries:
                if e["scope"] not in scopes:
                    P.append(f"matrix {cls}.{role}: unknown scope {e['scope']}")
                if not set(e["actions"]) <= set("VESA"):
                    P.append(f"matrix {cls}.{role}: bad actions {e['actions']}")
    for cls, per_role in matrix.items():
        for role, entries in per_role.items():
            for e in entries:
                a, s = set(e["actions"]), e["scope"]
                tag = f"{cls}.{role}[{e['actions']}·{s}]"
                if s == "BG" and role != "R7":
                    P.append(f"{tag}: BG is only for R7")
                if s == "SAMPLE" and role != "R9":
                    P.append(f"{tag}: SAMPLE is only for R9 (cls={cls})") if not (cls == "review_note" and role == "R9") else None
                if s == "VERIFY":
                    if role != "R3" or cls != "outcome_event" or not a <= {"V", "A"}:
                        P.append(f"{tag}: VERIFY is only R3 on outcome_event with actions within V/A (it must not grant general case access)")
                if cls in case_classes:
                    if s not in CASE_SCOPES_BY_ROLE[role]:
                        P.append(f"{tag}: role {role} may not hold scope {s} on a case class")
                if role == "R5" and cls in case_classes:
                    P.append(f"{tag}: R5 must not access case data")
                if role == "R6":
                    if cls in case_classes and cls not in R6_CASE_CLASSES:
                        P.append(f"{tag}: R6 may not access {cls}")
                    if cls not in case_classes and s not in {"ALL-PUB", "OWN-RES", "OWN-ORG", "AGG"}:
                        P.append(f"{tag}: R6 scope on non-case class must be ALL-PUB/OWN-RES/OWN-ORG/AGG")
                if role == "R7":
                    if cls in case_classes and s != "BG":
                        P.append(f"{tag}: R7 has no general case access; only BG")
                    if cls in ("document_file", "safety_flags"):
                        P.append(f"{tag}: R7 must not access {cls} at all")
                    if cls in ("case_task",) and s != "BG":
                        P.append(f"{tag}: R7 case_task only via BG")
                if role == "R8":
                    if s not in {"AGG", "ALL-PUB"} or not a <= {"V", "S"}:
                        P.append(f"{tag}: R8 is aggregate-only, no edit")
                if role == "R9":
                    if a - {"V"} and cls != "review_note":
                        P.append(f"{tag}: R9 is read-only except review_note")
                    if cls in case_classes and s != "SAMPLE":
                        P.append(f"{tag}: R9 case access only via SAMPLE")
                    if cls in ("document_file", "safety_flags") and cls in case_classes:
                        P.append(f"{tag}: R9 must not access {cls}")
                if role in ("R1", "R2") and s not in {"OWN", "GRANT", "TOKEN", "ALL-PUB", "SELF"}:
                    P.append(f"{tag}: R1/R2 scope must be own/granted/token/public")
    # API 與頁面的授權必須被矩陣涵蓋
    api_eps = set()
    for a in data["api"]:
        api_eps.add(a["endpoint"])
        for g in a["grants"]:
            if not grant_ok(data, a["class"], g, a["action"]):
                P.append(f"api {a['endpoint']}: grant {g} (action {a['action']}) is not covered by the matrix for {a['class']}")
    for pg in data["pages"]:
        for s in pg["sections"]:
            for g in s["grants"]:
                if not grant_ok(data, s["class"], g, s["action"]):
                    P.append(f"page {pg['page']} [{s['label']}]: grant {g} (action {s['action']}) is not covered by the matrix for {s['class']}")
    # 驗證 API：不得讓責任人或登錄人自己驗證
    for a in data["api"]:
        if a["endpoint"].endswith("/verify"):
            if any(grant_parts(g)[1] == "ASG" for g in a["grants"]):
                P.append(f"api {a['endpoint']}: verification must not be granted to the case owner scope (ASG)")
            if "R3·VERIFY" not in a["grants"]:
                P.append(f"api {a['endpoint']}: peer R3 verification must use the VERIFY scope")
    # N-04：verify 的排除條件是結構化欄位，note 只能由它衍生
    for a in data["api"]:
        if a["endpoint"].endswith("/verify"):
            if a.get("verifier_must_not_be") != VERIFIER_REQUIRED:
                P.append(f"api {a['endpoint']}: verifier_must_not_be must be exactly {VERIFIER_REQUIRED}")
            elif a["note"] != verify_note(a):
                P.append(f"api {a['endpoint']}: note must equal the text derived from verifier_must_not_be ({verify_note(a)})")
    # N-04：R4／R7 的資源轉換限制必須結構化，並與狀態機轉換操作者完全一致；限制文字由結構衍生
    if machines is not None and "resource_version" in machines:
        rv = machines["resource_version"]
        derived = derived_resource_notes(data, machines)
        for role in ("R4", "R7"):
            ents = data["matrix"].get("resource_internal", {}).get(role, [])
            for e in ents:
                if "E" in e["actions"] and "transition_limits" not in e:
                    P.append(f"matrix resource_internal.{role}: edit right needs structured transition_limits")
                if "transition_limits" in e:
                    lim = set(e["transition_limits"])
                    by_machine = {t["id"] for t in rv["transitions"] if role in t["actors"]}
                    for tid in sorted(lim - by_machine):
                        P.append(f"matrix resource_internal.{role}: transition_limits lists {tid} but the state machine does not allow {role} to perform it")
                    for tid in sorted(by_machine - lim):
                        P.append(f"matrix resource_internal.{role}: state machine lets {role} perform {tid} but transition_limits omits it")
                    if e["note"] != "僅限" + derived[role] + "，不可編輯內容":
                        P.append(f"matrix resource_internal.{role}: note must equal the text derived from transition_limits")
        want_api = "；".join(f"{r} 僅限{derived[r]}" for r in ("R4", "R7") if r in derived)
        for a in data["api"]:
            if a["endpoint"] == "POST /api/admin/versions/{id}/transitions" and a["note"] != want_api:
                P.append(f"api {a['endpoint']}: note must equal the text derived from transition_limits ({want_api})")
        want_page = "R5 可編輯與發布（發布人≠查核人）；" + "；".join(f"{r} 僅可{derived[r]}" for r in ("R4", "R7") if r in derived) + "；R9 唯讀；個案內容一律不可見"
        for pg in data["pages"]:
            for sec in pg["sections"]:
                if sec["class"] == "resource_internal" and any(grant_parts(g)[0] in ("R4", "R7") for g in sec["grants"]) and sec["note"] != want_page:
                    P.append(f"page {pg['page']} [{sec['label']}]: note must equal the text derived from transition_limits ({want_page})")
    # 狀態機操作者必須在對應 API 與矩陣中有授權
    if machines is not None:
        for mid, m in machines.items():
            cls = data["machine_class"][mid]
            eps = data["machine_api"][mid]
            eps = eps if isinstance(eps, list) else [eps]
            roles_api = set()
            for ep in eps:
                a = next((x for x in data["api"] if x["endpoint"] == ep), None)
                if a is None:
                    P.append(f"machine {mid}: API {ep} not found in permissions.json")
                    continue
                roles_api |= {grant_parts(g)[0] for g in a["grants"]}
            for t in m["transitions"]:
                for actor in t["actors"]:
                    if actor == "SYSTEM":
                        continue
                    if actor not in roles_api:
                        P.append(f"machine {mid}/{t['id']}: actor {actor} has no grant on {eps}")
                    if not any(set(e["actions"]) & set("EA") for e in matrix.get(cls, {}).get(actor, [])):
                        P.append(f"machine {mid}/{t['id']}: actor {actor} has no edit/approve right on class {cls} in the matrix")
    # 具體本輪要抓的矛盾：R5 與個案轉介；R7 與案件任務
    for pg in data["pages"]:
        for s in pg["sections"]:
            if s["class"] == "referral" and any(grant_parts(g)[0] == "R5" for g in s["grants"]):
                P.append(f"page {pg['page']} [{s['label']}]: R5 must not see case referrals")
    return P


def doc_problems(data):
    P = []
    eps, pages = doc_inventory()
    api_json = {a["endpoint"] for a in data["api"]} | set(data.get("api_external", {}))
    for ep in eps:
        if ep not in api_json:
            P.append(f"ARCHITECTURE.md lists {ep} but permissions.json has no entry")
    for ep in api_json:
        if ep not in eps:
            P.append(f"permissions.json lists {ep} but ARCHITECTURE.md has no row")
    pj = {p["page"] for p in data["pages"]}
    for p in pages:
        if p not in pj:
            P.append(f"USER_JOURNEYS lists page {p} but permissions.json has no entry")
    for p in pj - set(pages):
        P.append(f"permissions.json lists page {p} but USER_JOURNEYS has no section")
    return P


def main():
    data = load()
    machines = json.loads(SM.read_text(encoding="utf-8"))["machines"]
    check = "--check" in sys.argv
    problems = policy_problems(data, machines) + doc_problems(data)
    if problems:
        print("permission policy check FAILED:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    new = sync(data)
    if check:
        stale = [p.name for p, t in new.items() if p.read_text(encoding="utf-8") != t]
        if stale:
            print("以下文件的權限區塊與 permissions.json 不一致（請執行 gen_permissions.py）：", ", ".join(stale))
            sys.exit(1)
        n_cells = sum(len(v) for v in data["matrix"].values())
        print(f"OK: permissions policy ({len(data['classes'])} classes, {n_cells} matrix cells, {len(data['api'])} API, {len(data['pages'])} pages), docs in sync")
    else:
        for p, t in new.items():
            p.write_text(t, encoding="utf-8")
        print("regenerated permission blocks")


if __name__ == "__main__":
    main()
