"""文件敘述層級的政策檢查（只使用標準函式庫）。

結構化的權限矩陣（permissions.json）擋不到「文字承諾」。這裡對兩個已知矛盾做具體檢查：
 - F-03：R5 的資源維護頁 P9 不得承諾逐案內容（逐案清單、每案處理進度）；只能是資源層級影響摘要。
 - F-07：recheck_started_at 只存在於 NEEDS_RECHECK；離開該狀態的轉換（RV-08／09／12／13）都要寫明清除。
這是文件檢查，不證明任何產品行為。
"""
import json
import re

P9_FORBIDDEN = ("查看受影響案件", "每案處理進度", "受影響案件清單", "逐案清單")
RECHECK_EXIT_TRANSITIONS = ("RV-08", "RV-09", "RV-12", "RV-13")


def _section(text, start_pat, end_pat):
    m = re.search(start_pat, text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    e = re.search(end_pat, rest, re.M)
    return rest[:e.start()] if e else rest


def p9_problems(journeys, engine, arch):
    P = []
    p9 = _section(journeys, r"^### P9 ", r"^### ")
    if p9 is None:
        return ["P9 section not found in USER_JOURNEYS"]
    for bad in P9_FORBIDDEN:
        if bad in p9:
            P.append(f"P9 promises case-level content ({bad!r}) but R5 must not see case content")
    if "資源層級影響摘要" not in p9 or "不含逐案" not in p9:
        P.append("P9 must state it shows only a resource-level impact summary without per-case content")
    s82 = _section(engine, r"^### 8\.2 ", r"^## ")
    if s82 is None:
        P.append("ENGINE §8.2 not found")
    else:
        for bad in P9_FORBIDDEN:
            if bad in s82:
                P.append(f"ENGINE §8.2 promises case-level content in P9 ({bad!r})")
        if "資源層級影響摘要" not in s82:
            P.append("ENGINE §8.2 must say P9 shows only a resource-level impact summary")
    for line in arch.splitlines():
        if "/api/admin/versions/{id}/transitions" in line:
            for bad in P9_FORBIDDEN:
                if bad in line:
                    P.append(f"ARCHITECTURE transitions API returns case-level content ({bad!r}) to admin roles")
            if "資源層級影響摘要" not in line:
                P.append("ARCHITECTURE transitions API must return a resource-level impact summary")
    return P


def recheck_lifecycle_problems(machines_json_text, data_model, engine):
    P = []
    sm = json.loads(machines_json_text)["machines"]["resource_version"]
    by_id = {t["id"]: t for t in sm["transitions"]}
    for tid in RECHECK_EXIT_TRANSITIONS:
        t = by_id.get(tid)
        if t is None or "清除 `recheck_started_at`" not in t["pre"]:
            P.append(f"{tid} must state it clears recheck_started_at on leaving NEEDS_RECHECK")
    t7 = by_id.get("RV-07")
    if t7 is None or "recheck_started_at" not in t7["pre"]:
        P.append("RV-07 must write recheck_started_at")
    if "RV-09 暫停時保留" in data_model or "暫停時保留" in data_model:
        P.append("DATA_MODEL still says recheck_started_at is kept when SUSPENDED (contradicts 'other states must be empty')")
    if "其他狀態必為空" not in data_model:
        P.append("DATA_MODEL must keep 'other states must be empty' for recheck_started_at")
    if "VERSION_INVALID" not in data_model or "狀態×欄位" not in data_model:
        P.append("DATA_MODEL must define the state x field rejection (VERSION_INVALID)")
    if "RV-08、RV-09、RV-12、RV-13" not in engine:
        P.append("ENGINE §8.0 must list all clearing transitions")
    return P
