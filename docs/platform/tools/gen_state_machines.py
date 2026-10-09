#!/usr/bin/env python3
"""由 docs/platform/state_machines.json 產生並驗證 DATA_MODEL_AND_STATE_MACHINES.md §3 的狀態機圖與表。

用法：
  python3 docs/platform/tools/gen_state_machines.py           # 重新產生（寫入文件）
  python3 docs/platform/tools/gen_state_machines.py --check   # 只檢查文件是否與 JSON 一致（不一致 exit 1）
只使用 Python 標準函式庫。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "state_machines.json"
DOC = ROOT / "DATA_MODEL_AND_STATE_MACHINES.md"
KIND = {"normal": "一般", "undo": "撤回", "correction": "更正", "system": "系統"}


def load():
    data = json.loads(SM.read_text(encoding="utf-8"))
    for m in data["machines"].values():
        for t in m["transitions"]:
            if isinstance(t["to"], str):
                t["to"] = [t["to"]]  # 目標可為多個（例如恢復到 held_from）
    return data


def validate(data):
    errors = []
    roles = set(data["roles"])
    for mid, m in data["machines"].items():
        states = set(m["states"])
        ids = [t["id"] for t in m["transitions"]]
        if len(ids) != len(set(ids)):
            errors.append(f"{mid}: duplicate transition ids")
        if m["initial"] not in states:
            errors.append(f"{mid}: initial state not declared")
        reach = {m["initial"]}
        changed = True
        while changed:
            changed = False
            for t in m["transitions"]:
                if set(t["from"]) & reach and not set(t["to"]) <= reach:
                    reach |= set(t["to"])
                    changed = True
        for s in states - reach:
            errors.append(f"{mid}: state {s} unreachable")
        for t in m["transitions"]:
            for s in t["from"] + t["to"]:
                if s not in states:
                    errors.append(f"{mid}/{t['id']}: unknown state {s}")
            if not t["actors"] or not set(t["actors"]) <= roles:
                errors.append(f"{mid}/{t['id']}: bad actors {t['actors']}")
            if not t["evidence"].strip() or not t["pre"].strip():
                errors.append(f"{mid}/{t['id']}: missing pre/evidence")
            if t["revocable"] != "no" and t["revocable"] not in ids:
                errors.append(f"{mid}/{t['id']}: revocable refers to unknown {t['revocable']}")
            if t["revocable"] != "no":
                back = next(x for x in m["transitions"] if x["id"] == t["revocable"])
                if not set(t["to"]) <= set(back["from"]) or not set(t["from"]) <= set(back["to"]):
                    errors.append(f"{mid}/{t['id']}: revocable {back['id']} does not reverse it")
            if t["kind"] == "correction" and t["actors"] != ["R4"]:
                errors.append(f"{mid}/{t['id']}: corrections must be R4 only")
    return errors


def terminal_states(m):
    """沒有任何一般／系統轉換可離開的狀態（撤回與更正不算）。"""
    out = set(m["states"])
    for t in m["transitions"]:
        if t["kind"] in ("normal", "system"):
            for f in t["from"]:
                if t["to"] != [f]:
                    out.discard(f)
    return sorted(out)


def render(mid, m):
    lines = [f"<!-- BEGIN GENERATED:{mid} (來源：state_machines.json，請勿手改) -->"]
    term = set(terminal_states(m))
    lines += ["", "| 狀態 | 說明 | 終止狀態 |", "|---|---|---|"]
    for s, label in m["states"].items():
        mark = "是" if s in term else ""
        if s == m["initial"]:
            mark = (mark + " 初始").strip()
        lines.append(f"| `{s}` | {label} | {mark} |")
    if m.get("creation"):
        lines += ["", f"建立：{m['creation']}"]
    lines += ["", "```mermaid", "stateDiagram-v2", f"  [*] --> {m['initial']}"]
    for t in m["transitions"]:
        for f in t["from"]:
            for to in t["to"]:
                style = {"undo": "撤回 ", "correction": "更正 "}.get(t["kind"], "")
                lines.append(f"  {f} --> {to}: {style}{t['id']}")
    lines += ["```", "",
              "| ID | 從 → 到 | 類型 | 操作者 | 前置條件 | 必要證據 | 可否撤回 | 更正方式 |",
              "|---|---|---|---|---|---|---|---|"]
    for t in m["transitions"]:
        frm = "、".join(f"`{x}`" for x in t["from"])
        rev = "否" if t["revocable"] == "no" else f"可（{t['revocable']}）"
        corr = t["correction"] or "—"
        to = "、".join(f"`{x}`" for x in t["to"])
        lines.append(f"| {t['id']} | {frm} → {to} | {KIND[t['kind']]} | {'、'.join(t['actors'])} | {t['pre']} | {t['evidence']} | {rev} | {corr} |")
    lines += ["", f"<!-- END GENERATED:{mid} -->"]
    return "\n".join(lines)


def main():
    check = "--check" in sys.argv
    data = load()
    errors = validate(data)
    text = DOC.read_text(encoding="utf-8")
    new = text
    for mid, m in data["machines"].items():
        pat = re.compile(rf"<!-- BEGIN GENERATED:{mid} .*?<!-- END GENERATED:{mid} -->", re.S)
        if not pat.search(new):
            errors.append(f"marker for {mid} missing in {DOC.name}")
            continue
        new = pat.sub(lambda _m: render(mid, m), new)
    if errors:
        print("state machine validation FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    if check:
        if new != text:
            print("DATA_MODEL_AND_STATE_MACHINES.md 的狀態機區塊與 state_machines.json 不一致；請執行 gen_state_machines.py")
            sys.exit(1)
        n = sum(len(m["transitions"]) for m in data["machines"].values())
        print(f"OK: {len(data['machines'])} state machines, {n} transitions, doc in sync")
    else:
        DOC.write_text(new, encoding="utf-8")
        print("regenerated", DOC.name)


if __name__ == "__main__":
    main()
