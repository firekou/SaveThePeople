"""撤回／停止處理／刪除的「控制紀錄」參考模擬（非產品程式碼，只用標準函式庫；F-04）。

這是**純邏輯模擬**，不是資料庫、物件儲存或備份整合演練。它只用來驗證規格中的順序與判斷是否自洽：
  1. 先寫（write-ahead）：先把控制意圖附加到外部僅附加的控制紀錄（含雜湊鏈），收到確認後才改主庫；
  2. 主庫在單一交易內套用；失敗則回 202（已記錄、待套用），不回「完成」；
  3. 還原：驗證控制紀錄鏈完整、尾端不短於獨立見證的水位，否則維持隔離；再把備份水位之後的紀錄全部重新套用；
  4. 驗證：HARD_DELETE 驗證物件不存在；REDACT 驗證指定欄位已遮蔽（列仍在）；用途撤回驗證通知取消、分享停止、存取限制。
所有套用動作都是冪等的：重複套用結果相同。
"""
import copy
import hashlib
import json

MASK = "■■■"
CORE_PURPOSES = {"SCREENING", "CASE_MANAGEMENT"}


class LogUnavailable(Exception):
    pass


class DbCommitFailed(Exception):
    pass


def _hash(prev, payload):
    return hashlib.sha256((prev + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()


class ControlLog:
    """外部僅附加的控制紀錄（模擬：獨立帳號、物件鎖、雜湊鏈）。紀錄只含物件參照與用途，不含個人內容。"""

    def __init__(self):
        self.entries = []
        self.fail_next = 0

    def append(self, rec):
        if self.fail_next:
            self.fail_next -= 1
            raise LogUnavailable("control log unavailable")
        seq = len(self.entries) + 1
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        e = {"seq": seq, "rec": rec, "prev": prev}
        e["hash"] = _hash(prev, {"seq": seq, "rec": rec})
        self.entries.append(e)
        return seq

    def last_seq(self):
        return self.entries[-1]["seq"] if self.entries else 0

    def verify_chain(self):
        prev = "0" * 64
        for i, e in enumerate(self.entries, start=1):
            if e["seq"] != i:
                return False, f"SEQ_GAP_AT_{i}"
            if e["prev"] != prev or e["hash"] != _hash(prev, {"seq": e["seq"], "rec": e["rec"]}):
                return False, f"CHAIN_BROKEN_AT_{i}"
            prev = e["hash"]
        return True, "ok"


class Witness:
    """獨立見證（例如另一個監控服務的心跳）：只記錄「已確認的最大 seq」，用來偵測紀錄尾端遺失。"""

    def __init__(self):
        self.max_seq = 0

    def report(self, seq):
        self.max_seq = max(self.max_seq, seq)


def apply_record(st, rec):
    """冪等套用一筆控制紀錄到狀態 st（dict）。"""
    t = rec["type"]
    if t == "CONSENT_REVOKE":
        c = st["consents"][rec["consent"]]
        c["revoked"] = sorted(set(c["revoked"]) | set(rec["purposes"]))
        purposes = set(rec["purposes"])
        for n in st["notifications"].values():
            if n["consent"] == rec["consent"] and (n["purpose"] in purposes or "CONTACT" in purposes) \
                    and n["status"] in ("SCHEDULED", "RETRY_SCHEDULED"):
                n["status"] = "CANCELLED"
        if "REFERRAL_SHARE" in purposes:
            for rid, r in st["referrals"].items():
                if r["consent"] != rec["consent"]:
                    continue
                if r["status"] not in ("CANCELLED", "CLOSED"):
                    r["status"] = "CANCELLED"
                st["tasks"].setdefault(f"STOP_USE:{rid}", {"type": "STOP_USE_NOTICE", "referral": rid})
        if "DOCUMENT_STORAGE" in purposes:
            for o in st["objects"].values():
                if o["consent"] == rec["consent"]:
                    o["exists"] = False
        if purposes & CORE_PURPOSES:
            st["household"]["processing"] = "CLOSED"
        if rec.get("retention_hold"):
            st["household"]["restriction"] = "RETENTION_HOLD"
    elif t == "HARD_DELETE":
        st[rec["table"]][rec["id"]]["exists"] = False
    elif t == "REDACT":
        row = st[rec["table"]][rec["id"]]
        if row.get("exists", True):
            for f in rec["fields"]:
                row[f] = MASK
    elif t == "APPLIED":
        pass
    else:
        raise ValueError(f"unknown control record type {t}")


def access_allowed(st, consent_id, purpose):
    """存取限制：已撤回的用途一律不可使用。"""
    return purpose not in st["consents"][consent_id]["revoked"] and st["household"]["processing"] != "CLOSED"


def verify_controls(st, entries):
    """依控制紀錄逐筆驗證狀態；回傳不符合的清單。HARD_DELETE 驗證不存在；REDACT 驗證欄位已遮蔽。"""
    bad = []
    hard_deleted = {(e["rec"]["table"], e["rec"]["id"]) for e in entries if e["rec"]["type"] == "HARD_DELETE"}
    for e in entries:
        r = e["rec"]
        seq = e["seq"]
        if r["type"] == "CONSENT_REVOKE":
            c = st["consents"][r["consent"]]
            if not set(r["purposes"]) <= set(c["revoked"]):
                bad.append(f"seq{seq}:CONSENT_NOT_REVOKED")
            for p in r["purposes"]:
                if access_allowed(st, r["consent"], p):
                    bad.append(f"seq{seq}:ACCESS_NOT_RESTRICTED:{p}")
            purposes = set(r["purposes"])
            for nid, n in st["notifications"].items():
                if n["consent"] == r["consent"] and (n["purpose"] in purposes or "CONTACT" in purposes) \
                        and n["status"] in ("SCHEDULED", "RETRY_SCHEDULED"):
                    bad.append(f"seq{seq}:NOTIFICATION_NOT_CANCELLED:{nid}")
            if "REFERRAL_SHARE" in purposes:
                for rid, rf in st["referrals"].items():
                    if rf["consent"] == r["consent"]:
                        if rf["status"] not in ("CANCELLED", "CLOSED"):
                            bad.append(f"seq{seq}:SHARE_NOT_STOPPED:{rid}")
                        if f"STOP_USE:{rid}" not in st["tasks"]:
                            bad.append(f"seq{seq}:STOP_USE_TASK_MISSING:{rid}")
            if "DOCUMENT_STORAGE" in purposes:
                for oid, o in st["objects"].items():
                    if o["consent"] == r["consent"] and o["exists"]:
                        bad.append(f"seq{seq}:OBJECT_STILL_EXISTS:{oid}")
            if purposes & CORE_PURPOSES and st["household"]["processing"] != "CLOSED":
                bad.append(f"seq{seq}:PROCESSING_NOT_CLOSED")
            if r.get("retention_hold") and st["household"]["restriction"] != "RETENTION_HOLD":
                bad.append(f"seq{seq}:RETENTION_HOLD_MISSING")
        elif r["type"] == "HARD_DELETE":
            if st[r["table"]][r["id"]].get("exists", True):
                bad.append(f"seq{seq}:STILL_EXISTS:{r['table']}.{r['id']}")
        elif r["type"] == "REDACT":
            row = st[r["table"]][r["id"]]
            if row.get("exists", True):
                for f in r["fields"]:
                    if row.get(f) != MASK:
                        bad.append(f"seq{seq}:NOT_REDACTED:{r['table']}.{r['id']}.{f}")
            elif (r["table"], r["id"]) not in hard_deleted:
                bad.append(f"seq{seq}:REDACT_TARGET_MISSING_WITHOUT_HARD_DELETE:{r['table']}.{r['id']}")
    return bad


def new_state(initial):
    st = copy.deepcopy(initial)
    st.setdefault("applied_seq", 0)
    return st


def request_control(st, log, wit, rec, db_fail=False):
    """處理一個撤回／刪除請求。回傳 (http 狀態碼, 狀態說明, 新狀態)。

    順序：1) 先寫外部控制紀錄並取得確認；2) 主庫單一交易套用；3) 附加 APPLIED 標記（盡力而為，非必要）。
    只有 1)、2) 都成功才回 200「完成」；1) 成功但 2) 失敗回 202「已記錄、待套用」；1) 失敗回 503 且完全不改主庫。
    """
    try:
        seq = log.append(rec)
    except LogUnavailable:
        return 503, "NOT_RECORDED", st
    wit.report(seq)
    try:
        if db_fail:
            raise DbCommitFailed()
        tx = copy.deepcopy(st)
        apply_record(tx, rec)
        tx["applied_seq"] = seq
        st = tx
    except DbCommitFailed:
        return 202, "RECORDED_PENDING_APPLY", st
    try:
        s2 = log.append({"type": "APPLIED", "ref": seq})
        wit.report(s2)
    except LogUnavailable:
        pass
    return 200, "COMPLETE", st


def reapply_all(st, entries, from_seq=0):
    """把 seq > from_seq 的控制紀錄全部（冪等）重新套用。"""
    for e in entries:
        if e["seq"] > from_seq:
            apply_record(st, e["rec"])
            st["applied_seq"] = max(st["applied_seq"], e["seq"])
    return st


def recover(snapshot, log, wit, skip_reapply=False):
    """由備份還原後的處理。回傳 dict：quarantined、reason、watermark、mismatches、state。

    維持隔離（不恢復服務）的條件：控制紀錄鏈不完整；紀錄尾端短於獨立見證的水位；套用後驗證仍有不符合。
    """
    st = new_state(snapshot)
    ok, why = log.verify_chain()
    watermark = max(log.last_seq(), wit.max_seq)
    out = {"watermark": watermark, "state": st, "mismatches": [], "reason": None, "quarantined": True}
    if not ok:
        out["reason"] = f"LOG_INVALID:{why}"
        return out
    if log.last_seq() < wit.max_seq:
        out["reason"] = f"LOG_INCOMPLETE:last={log.last_seq()}<witness={wit.max_seq}"
        return out
    if not skip_reapply:
        reapply_all(st, log.entries, from_seq=st["applied_seq"])
    mism = verify_controls(st, log.entries)
    out["mismatches"] = mism
    if mism:
        out["reason"] = "VERIFY_FAILED"
        return out
    out["quarantined"] = False
    return out
