"""撤回／停止處理／刪除的「控制紀錄」參考模擬（非產品程式碼，只用標準函式庫；F-04）。

這是**純邏輯模擬**，不是資料庫、物件儲存或備份整合演練。它只用來驗證規格中的順序與判斷是否自洽：
  0. 先驗證 payload（schema＋目標存在＋用途／欄位非空）；不合法回 422，不寫任何東西（N-05）；
  1. 先寫（write-ahead）：先讓**獨立見證持久確認**即將使用的 seq（N-03：見證確認在前、且必須同步持久，不可只靠定期回報），
     再把控制意圖附加到外部僅附加的控制紀錄（含雜湊鏈）；任一未確認都不改主庫；
  2. 主庫在單一交易內套用；失敗則回 202（已記錄、待套用），不回「完成」；
  3. 還原：驗證控制紀錄鏈完整、尾端不短於獨立見證的水位，否則維持隔離；再把備份水位之後的紀錄全部重新套用；
  4. 驗證：HARD_DELETE 驗證物件不存在；REDACT 驗證指定欄位已遮蔽（列仍在）；用途撤回驗證通知取消、分享停止、存取限制。
所有套用動作都是冪等的：重複套用結果相同。
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import schema_lite as SL  # noqa: E402

MASK = "■■■"
CORE_PURPOSES = {"SCREENING", "CASE_MANAGEMENT"}


class LogUnavailable(Exception):
    pass


class DbCommitFailed(Exception):
    pass


class WitnessUnavailable(Exception):
    pass


class InvalidControl(ValueError):
    pass


def _hash(prev_hash, body):
    return hashlib.sha256((prev_hash + json.dumps(body, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()


def _body(e):
    """雜湊涵蓋的欄位：seq、recorded_at、payload（prev_hash 另外串接）。"""
    return {"seq": e["seq"], "recorded_at": e["recorded_at"], "payload": e["payload"]}


class ControlLog:
    """外部僅附加的控制紀錄（模擬：獨立帳號、物件鎖、雜湊鏈）。

    單筆為 envelope：{seq, prev_hash, hash, recorded_at, payload}；payload 才是動作內容（見 schemas/control_record.schema.json）。
    紀錄只含物件參照與用途，不含個人內容。recorded_at 由模擬時鐘產生（合成，不取系統時間）。
    """

    def __init__(self):
        self.entries = []
        self.fail_next = 0

    def next_seq(self):
        return len(self.entries) + 1

    def append(self, payload):
        if self.fail_next:
            self.fail_next -= 1
            raise LogUnavailable("control log unavailable")
        seq = self.next_seq()
        errs = payload_problems(payload)
        if payload.get("type") == "APPLIED":
            ref = payload.get("ref")
            if not (isinstance(ref, int) and 1 <= ref < seq) or self.entries[ref - 1]["payload"]["type"] == "APPLIED":
                errs.append("APPLIED.ref must point to an earlier non-APPLIED entry")
        if errs:
            raise InvalidControl("; ".join(errs))
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        e = {"seq": seq, "prev_hash": prev, "recorded_at": f"2026-01-01T00:{seq // 60:02d}:{seq % 60:02d}Z", "payload": copy.deepcopy(payload)}
        e["hash"] = _hash(prev, _body(e))
        self.entries.append(e)
        return seq

    def last_seq(self):
        return self.entries[-1]["seq"] if self.entries else 0

    def verify_chain(self):
        prev = "0" * 64
        for i, e in enumerate(self.entries, start=1):
            if e["seq"] != i:
                return False, f"SEQ_GAP_AT_{i}"
            if e["prev_hash"] != prev or e["hash"] != _hash(prev, _body(e)):
                return False, f"CHAIN_BROKEN_AT_{i}"
            prev = e["hash"]
        return True, "ok"


class Witness:
    """獨立見證（另一個獨立服務）。N-03 規範：

    - `report(seq)` 是**同步、持久**的確認：只有回傳 True 才算見證已持久記下「seq 即將使用」；
      例外、逾時、回傳 False／None（含只是排入「定期更新」尚未 flush）一律視為**未確認**，呼叫端必須 fail-closed（503，不改主庫）。
    - 見證記錄的是水位（max_seq）與各 seq 的雜湊（hash_at），用來偵測尾端遺失與整段重寫。
    - `available=False` 表示還原時無法查詢見證：不得放行。
    """

    def __init__(self):
        self.max_seq = 0
        self.hash_at = {}
        self.available = True
        self.fail_next = 0

    def report(self, seq):
        if self.fail_next:
            self.fail_next -= 1
            raise WitnessUnavailable("witness unavailable")
        if not self.available:
            raise WitnessUnavailable("witness unavailable")
        self.max_seq = max(self.max_seq, seq)
        return True

    def record_hash(self, seq, h):
        """寫入後補記雜湊（盡力而為；失敗只降低偵測力，不影響水位保護）。"""
        if self.available:
            self.hash_at[seq] = h


KNOWN_TABLE_ID = ("table", "id")


def payload_problems(payload):
    """結構驗證（schema）。回傳錯誤清單；空清單＝通過。"""
    schema = SL.load_schema("control_record")
    return SL.validate(payload, schema["definitions"]["payload"], schema)


def validate_payload(st, payload):
    """N-05：結構＋語意（目標存在、用途／欄位非空且不重複）。不合法拋 InvalidControl。"""
    errs = payload_problems(payload)
    if errs:
        raise InvalidControl("; ".join(errs))
    t = payload["type"]
    if t == "APPLIED":
        raise InvalidControl("APPLIED is written by the system after apply, not requested")
    if t == "CONSENT_REVOKE":
        if payload["consent_id"] not in st["consents"]:
            raise InvalidControl("unknown consent_id")
        if len(set(payload["purposes"])) != len(payload["purposes"]):
            raise InvalidControl("duplicate purposes")
    else:
        table = st.get(payload["table"])
        if not isinstance(table, dict) or payload["id"] not in table:
            raise InvalidControl("unknown control target")
        if t == "REDACT":
            if len(set(payload["fields"])) != len(payload["fields"]):
                raise InvalidControl("duplicate fields")
            row = table[payload["id"]]
            for f in payload["fields"]:
                if f == "exists" or f not in row:
                    raise InvalidControl(f"unknown or protected field {f!r}")


def apply_record(st, rec):
    """冪等套用一筆控制紀錄到狀態 st（dict）。"""
    t = rec["type"]
    if t == "CONSENT_REVOKE":
        c = st["consents"][rec["consent_id"]]
        c["revoked"] = sorted(set(c["revoked"]) | set(rec["purposes"]))
        purposes = set(rec["purposes"])
        for n in st["notifications"].values():
            if n["consent"] == rec["consent_id"] and (n["purpose"] in purposes or "CONTACT" in purposes) \
                    and n["status"] in ("SCHEDULED", "RETRY_SCHEDULED"):
                n["status"] = "CANCELLED"
        if "REFERRAL_SHARE" in purposes:
            for rid, r in st["referrals"].items():
                if r["consent"] != rec["consent_id"]:
                    continue
                if r["status"] not in ("CANCELLED", "CLOSED"):
                    r["status"] = "CANCELLED"
                st["tasks"].setdefault(f"STOP_USE:{rid}", {"type": "STOP_USE_NOTICE", "referral": rid})
        if "DOCUMENT_STORAGE" in purposes:
            for o in st["objects"].values():
                if o["consent"] == rec["consent_id"]:
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
    hard_deleted = {(e["payload"]["table"], e["payload"]["id"]) for e in entries if e["payload"]["type"] == "HARD_DELETE"}
    for e in entries:
        r = e["payload"]
        seq = e["seq"]
        if r["type"] == "CONSENT_REVOKE":
            c = st["consents"][r["consent_id"]]
            if not set(r["purposes"]) <= set(c["revoked"]):
                bad.append(f"seq{seq}:CONSENT_NOT_REVOKED")
            for p in r["purposes"]:
                if access_allowed(st, r["consent_id"], p):
                    bad.append(f"seq{seq}:ACCESS_NOT_RESTRICTED:{p}")
            purposes = set(r["purposes"])
            for nid, n in st["notifications"].items():
                if n["consent"] == r["consent_id"] and (n["purpose"] in purposes or "CONTACT" in purposes) \
                        and n["status"] in ("SCHEDULED", "RETRY_SCHEDULED"):
                    bad.append(f"seq{seq}:NOTIFICATION_NOT_CANCELLED:{nid}")
            if "REFERRAL_SHARE" in purposes:
                for rid, rf in st["referrals"].items():
                    if rf["consent"] == r["consent_id"]:
                        if rf["status"] not in ("CANCELLED", "CLOSED"):
                            bad.append(f"seq{seq}:SHARE_NOT_STOPPED:{rid}")
                        if f"STOP_USE:{rid}" not in st["tasks"]:
                            bad.append(f"seq{seq}:STOP_USE_TASK_MISSING:{rid}")
            if "DOCUMENT_STORAGE" in purposes:
                for oid, o in st["objects"].items():
                    if o["consent"] == r["consent_id"] and o["exists"]:
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

    順序（N-03、N-05）：
      0) 驗證 payload；不合法→422 INVALID_CONTROL，見證、控制紀錄、主庫都不動；
      1) 獨立見證**同步持久確認** seq；未確認（例外／逾時／未 flush／False）→503 WITNESS_UNCONFIRMED，控制紀錄與主庫都不動；
      2) 附加外部控制紀錄並取得確認；失敗→503 NOT_RECORDED，主庫不動（見證水位已先到 seq：同一 seq 重試即補上；
         若重試前就發生還原，水位大於紀錄尾端→維持隔離，由資料責任人與 R7 處理，這是刻意的 fail-closed）；
      3) 主庫單一交易套用；失敗→202 RECORDED_PENDING_APPLY（已記錄、待冪等重試，不得回完成）；
      4) 盡力附加 APPLIED（見證未確認或紀錄不可用就略過，非必要）。
    只有 1)～3) 都成功才回 200「完成」。
    """
    try:
        validate_payload(st, rec)
    except InvalidControl:
        return 422, "INVALID_CONTROL", st
    seq = log.next_seq()
    try:
        acked = wit.report(seq)
    except WitnessUnavailable:
        acked = False
    if acked is not True:
        return 503, "WITNESS_UNCONFIRMED", st
    try:
        log.append(rec)
    except LogUnavailable:
        return 503, "NOT_RECORDED", st
    wit.record_hash(seq, log.entries[-1]["hash"])
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
        s2 = log.next_seq()
        if wit.report(s2) is True:
            log.append({"type": "APPLIED", "ref": seq})
            wit.record_hash(s2, log.entries[-1]["hash"])
    except (LogUnavailable, WitnessUnavailable):
        pass
    return 200, "COMPLETE", st


def reapply_all(st, entries, from_seq=0):
    """把 seq > from_seq 的控制紀錄全部（冪等）重新套用。"""
    for e in entries:
        if e["seq"] > from_seq:
            apply_record(st, e["payload"])
            st["applied_seq"] = max(st["applied_seq"], e["seq"])
    return st


def recover(snapshot, log, wit, skip_reapply=False):
    """由備份還原後的處理。回傳 dict：quarantined、reason、watermark、mismatches、state。

    維持隔離（不恢復服務）的條件：控制紀錄鏈不完整；獨立見證無法查詢；紀錄尾端短於獨立見證的水位；見證記下的雜湊與紀錄不符（整段重寫）；套用後驗證仍有不符合。
    """
    st = new_state(snapshot)
    ok, why = log.verify_chain()
    watermark = max(log.last_seq(), wit.max_seq)
    out = {"watermark": watermark, "state": st, "mismatches": [], "reason": None, "quarantined": True}
    if not ok:
        out["reason"] = f"LOG_INVALID:{why}"
        return out
    if not wit.available:
        out["reason"] = "WITNESS_UNAVAILABLE"
        return out
    if log.last_seq() < wit.max_seq:
        out["reason"] = f"LOG_INCOMPLETE:last={log.last_seq()}<witness={wit.max_seq}"
        return out
    for seq, h in sorted(wit.hash_at.items()):
        if seq <= log.last_seq() and log.entries[seq - 1]["hash"] != h:
            out["reason"] = f"LOG_REWRITTEN_AT_{seq}"
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
