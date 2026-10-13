"""catalog_visibility — the single display judgement (ENGINE §0.1).

Listing in the public catalog and being formally recommendable are different
judgements; this module only answers "may it be shown, and with which notes".
Recommendation (§0.2) is out of D1-A scope and is never computed here.
"""
from dataclasses import dataclass, field
from datetime import date

LISTED_STATUSES = {"PUBLISHED", "NEEDS_RECHECK"}
HISTORY_STATUSES = {"SUSPENDED", "EXPIRED", "SUPERSEDED", "RETIRED"}
INTERNAL_STATUSES = {"CANDIDATE", "DRAFT", "IN_REVIEW"}

STATUS_LABELS = {
    "PUBLISHED": "已查核",
    "NEEDS_RECHECK": "查核中",
    "SUSPENDED": "暫停推薦",
    "EXPIRED": "已過期",
    "SUPERSEDED": "已被新版本取代",
    "RETIRED": "已停用",
}

CAPACITY_LABELS = {"OPEN": "可受理", "LIMITED": "名額有限", "FULL": "名額已滿", "UNKNOWN": "名額需確認"}


@dataclass
class Visibility:
    listed: bool
    detail: str  # "PUBLIC" | "HISTORY" | "NONE"
    status_label: str
    notes: list = field(default_factory=list)   # plain-language explanations shown to the reader
    badges: list = field(default_factory=list)  # short tags shown in list rows


def catalog_visibility(version, as_of: date) -> Visibility:
    status = version.status
    if status in INTERNAL_STATUSES:
        return Visibility(listed=False, detail="NONE", status_label="")
    label = STATUS_LABELS.get(status, status)
    notes, badges = [], []
    if status in HISTORY_STATUSES:
        reason = {"EXPIRED": "此版本的有效期間已結束，僅保留為歷史紀錄，不再接受依此申請。",
                  "SUSPENDED": "此資源目前暫停推薦（例如來源失效或查核中），不列於公開目錄。",
                  "SUPERSEDED": "此版本已被新版本取代，僅保留為歷史紀錄。",
                  "RETIRED": "此資源已停用，僅保留為歷史紀錄。"}[status]
        notes.append(reason)
        return Visibility(listed=False, detail="HISTORY", status_label=label, notes=notes, badges=[label])

    # PUBLISHED or NEEDS_RECHECK: listed, with notes
    if status == "NEEDS_RECHECK":
        badges.append("查核中")
        notes.append("此資源正在重新查核，資料可能變動。")
    if version.effective_from and as_of < version.effective_from:
        badges.append(f"{version.effective_from:%Y-%m-%d} 起適用")
        notes.append(f"此資源自 {version.effective_from:%Y-%m-%d} 起才適用，目前尚未生效，不列為推薦。")
    if version.effective_unknown:
        badges.append("期限未知")
        notes.append("有效期間的截止日未知，需先由人員向提供單位確認；在確認前不列為正式推薦。")
    elif version.effective_to and as_of > version.effective_to:
        badges.append("期間已結束")
        notes.append(f"資料所載有效期間已於 {version.effective_to:%Y-%m-%d} 結束，狀態尚待更新；申請前請先確認。")
    cap = version.capacity_status
    if cap == "FULL":
        badges.append("名額已滿")
        when = f"（{version.capacity_confirmed_at:%Y-%m-%d} 確認）" if version.capacity_confirmed_at else ""
        notes.append(f"提供單位目前名額已滿{when}，可能需候補；轉介前須再確認。")
    elif cap == "UNKNOWN":
        badges.append("名額需確認")
    win = (version.application_window or {}).get("type")
    if win == "UNKNOWN":
        badges.append("申請期間未知")
        notes.append("申請期間未知，需先人工確認。")
    elif win == "FIXED":
        ranges = (version.application_window or {}).get("ranges") or []
        if ranges and all(as_of > date.fromisoformat(r["to"]) for r in ranges):
            notes.append("本版本的申請期間已全部結束。")
    return Visibility(listed=True, detail="PUBLIC", status_label=label, notes=notes, badges=badges)
