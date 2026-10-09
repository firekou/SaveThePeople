#!/usr/bin/env python3
"""平台規劃文件的一致性檢查（只使用標準函式庫）。

檢查項目：
 1. 相對連結與錨點存在；「[檔案](檔案) §N.M」所指章節存在
 2. WP／T／G／D／U／F／RT／PR／OP／CP／AS／J 與狀態轉換 ID：被引用者皆有定義；T 編號連續
 3. 資料模型欄位路徑：文件中的 `Entity.field` 都存在於 DATA_MODEL 的實體表
 4. 權限：permissions.json 單一來源與政策檢查（呼叫 gen_permissions --check）；引用語境（citation_check）；schemas；新測試 T-50～T-61
 5. 工時加總：BUILD_PLAN 工作包表 ↔ 文件中的總數字 ↔ 批次執行包；舊數字不得殘留
 6. 狀態機 JSON 與文件同步（呼叫 gen_state_machines）
 7. 版本標示一致；範例資料皆為合成；公開 repo 不含個資樣式
用法：python3 docs/platform/tools/check_docs.py（任一失敗 exit 1）
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAT = ROOT / "docs" / "platform"
FAILS = []
N = 0


def ok(name, cond, detail=""):
    global N
    N += 1
    if not cond:
        FAILS.append(f"{name} {detail}".strip())


def read(p):
    return Path(p).read_text(encoding="utf-8")


MD = [ROOT / "README.md"] + sorted((ROOT / "docs").rglob("*.md"))
TEXT = {p: read(p) for p in MD}
PLAT_MD = [p for p in MD if p.parent == PLAT or p.parent == PLAT / "revisions" or p.parent == PLAT / "examples"]


def slug(title):
    t = title.strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def headings(text):
    out = []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and not in_code:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


def section_numbers(text):
    nums = set()
    for _, t in headings(text):
        m = re.match(r"^(\d+(?:\.\d+)*)[ .]", t + " ")
        if m:
            nums.add(m.group(1))
    return nums


# ------------------------------------------------------------ 1. 連結與章節
def check_links():
    for p, text in TEXT.items():
        base = p.parent
        body = re.sub(r"```.*?```", "", text, flags=re.S)
        for m in re.finditer(r"\]\(([^)\s]+)\)", body):
            t = m.group(1)
            if t.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, anchor = t.partition("#")
            target = (base / path).resolve() if path else p
            ok(f"link {p.relative_to(ROOT)} -> {t}", target.exists())
            if anchor and target.suffix == ".md" and target.exists():
                slugs = {slug(h) for _, h in headings(read(target))}
                ok(f"anchor {p.relative_to(ROOT)} -> {t}", anchor in slugs)
        for m in re.finditer(r"\]\(([\w./\-]+\.md)\)\s*§(\d+(?:\.\d+)*)", body):
            target = (base / m.group(1)).resolve()
            if target.exists():
                ok(f"section {p.relative_to(ROOT)} -> {m.group(1)} §{m.group(2)}", m.group(2) in section_numbers(read(target)))


# ------------------------------------------------------------ 2. ID
def table_ids(text, pattern):
    return set(re.findall(r"^\|\s*(" + pattern + r")\b", text, re.M))


def check_ids(sm):
    bp = read(PLAT / "BUILD_PLAN_AND_ACCEPTANCE.md")
    dec = read(PLAT / "DECISIONS_AND_UNKNOWNS.md")
    prd = read(PLAT / "PRODUCT_REQUIREMENTS.md")
    ops = read(PLAT / "OPERATIONS_AND_PRIVACY.md")
    jr = read(PLAT / "USER_JOURNEYS_AND_SCREENS.md")
    alltext = "\n".join(read(p) for p in PLAT_MD if p.suffix == ".md" and "revisions" not in str(p))
    spec = [
        (r"WP-\d\d[a]?", table_ids(bp, r"WP-\d\d[a]?")),
        (r"T-\d\d", table_ids(bp, r"T-\d\d")),
        (r"G-\d\d", table_ids(dec, r"G-\d\d")),
        (r"D-\d{3}", table_ids(dec, r"D-\d{3}")),
        (r"U-\d\d", table_ids(dec, r"U-\d\d")),
        (r"F-\d\d", table_ids(prd, r"F-\d\d")),
        (r"PR-\d\d", table_ids(prd, r"PR-\d\d")),
        (r"OP-\d\d", table_ids(dec, r"OP-\d\d")),
        (r"CP-\d\d", table_ids(ops, r"CP-\d\d")),
        (r"AS-[1-6]\b", table_ids(bp, r"AS-[1-6]")),
        (r"RT-[A-Z]+(?:-[A-Z]+)*", table_ids(ops, r"RT-[A-Z]+(?:-[A-Z]+)*")),
        (r"J[1-9]\b", {m for m in re.findall(r"^### (J[1-9])", jr, re.M)}),
    ]
    for pat, defined in spec:
        used = set(re.findall(r"(?<![A-Za-z])(" + pat + ")", alltext))
        used = {u.rstrip() for u in used}
        missing = sorted(u for u in used if u not in defined)
        ok(f"ids {pat} used but not defined", not missing, str(missing))
    # 狀態轉換 ID：RV／AP／RF／OC／NF 為兩位數；Assessment 為 AS-0x
    known = {t["id"] for m in sm["machines"].values() for t in m["transitions"]}
    used = set(re.findall(r"\b((?:RV|AP|RF|OC|NF)-\d\d|AS-0\d)\b", alltext))
    ok("transition ids used but not in state_machines.json", not (used - known), str(sorted(used - known)))
    # 測試 ID 連續
    nums = sorted(int(x.split("-")[1]) for x in table_ids(bp, r"T-\d\d"))
    ok("T ids contiguous", nums == list(range(1, len(nums) + 1)), str(nums))
    # 角色代碼
    for r in set(re.findall(r"\bR(\d+)\b", alltext)):
        ok(f"role R{r} valid", 1 <= int(r) <= 9)


# ------------------------------------------------------------ 3. 欄位路徑
COMMON = {"id", "created_at", "created_by", "updated_at", "row_version", "is_synthetic", "organization_id", "retention_class", "deleted_at"}


def entity_fields():
    dm = read(PLAT / "DATA_MODEL_AND_STATE_MACHINES.md")
    fields = {}
    parts = re.split(r"^### 2\.\d+ ", dm, flags=re.M)[1:]
    for part in parts:
        name = re.match(r"([A-Za-z]+|其他補充實體)", part).group(1)
        end = part.split("\n### ")[0].split("\n## ")[0]
        names = set()
        for line in end.splitlines():
            m = re.match(r"^\|\s*([^|]+?)\s*\|", line)
            if not m or m.group(1) in ("欄位", "---", "實體"):
                continue
            first = m.group(1)
            if name == "其他補充實體":
                cols = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cols) >= 3:
                    toks = set(re.findall(r"`([a-z_]+)`", cols[2]))
                    for nm in cols[0].split("／"):
                        fields.setdefault(nm.strip(), set()).update(toks)
                continue
            for tok in re.split(r"\s*[/／｜]\s*", first.replace("`", "")):
                tok = tok.strip()
                if re.match(r"^[a-z_][a-z0-9_]*$", tok):
                    names.add(tok)
        if name != "其他補充實體":
            fields[name] = names
    # 補充實體表（2.21）中的實體名稱
    return fields


def check_fields():
    fields = entity_fields()
    ok("entity table parsed", len(fields) >= 20, str(len(fields)))
    required = ["Organization", "Resource", "ResourceVersion", "EligibilityRule", "Household", "Person", "Consent", "Assessment",
                "Application", "Referral", "DocumentRequirement", "DocumentRecord", "Task", "Notification", "Outcome", "AuditEvent"]
    for r in required:
        ok(f"required entity {r} has fields", len(fields.get(r, ())) >= 4, str(len(fields.get(r, ()))))
    alltext = "\n".join(read(p) for p in PLAT_MD if p.suffix == ".md" and "revisions" not in str(p))
    seen = set()
    for m in re.finditer(r"(?<![\w.])([A-Z][A-Za-z]+)\.([a-z_][a-z0-9_]*)((?:\.[a-z_]+)*)", alltext):
        ent, field = m.group(1), m.group(2)
        if ent not in fields or (ent, field) in seen:
            continue
        seen.add((ent, field))
        ok(f"field path `{ent}.{field}` exists", field in fields[ent] or field in COMMON, "")


# ------------------------------------------------------------ 4. 權限（單一來源 permissions.json）
def check_matrix():
    """R2：矩陣、API 權限欄與頁面權限行由 permissions.json 產生；政策檢查（gen_permissions.policy_problems）取代 R1 的字串前綴檢查。

    這是**文件政策檢查**：確認矩陣、API、頁面、狀態機操作者之間自洽；不是產品授權行為測試。
    """
    r = subprocess.run([sys.executable, str(PLAT / "tools" / "gen_permissions.py"), "--check"], capture_output=True, text=True)
    ok("permissions policy and generated blocks in sync", r.returncode == 0, (r.stdout + r.stderr).strip()[:600])
    arch = read(PLAT / "ARCHITECTURE.md")
    for line in arch.splitlines():
        if line.startswith("| `") and "/api/" in line:
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) == 6:
                perm = cols[4]
                ok(f"API perm uses valid roles {cols[0][:40]}", all(1 <= int(x) <= 9 for x in re.findall(r"R(\d)", perm)), perm)
                ok(f"API perm not placeholder {cols[0][:40]}", perm not in ("x", ""), perm)


# ------------------------------------------------------------ 4b. 引用語境與 schema 與 R2 回覆
def check_citations():
    sys.path.insert(0, str(PLAT / "tools"))
    import citation_check as CC
    for p in PLAT_MD:
        if "revisions" in str(p):
            continue
        for n, msg in CC.citation_problems(p.name, read(p)):
            ok(f"citation context {p.name}:{n}", False, msg)
        ok(f"citation context scanned {p.name}", True)


def check_schemas():
    sys.path.insert(0, str(PLAT / "tools"))
    import schema_lite as SL
    names = ("resource_version", "eligibility_rule", "household_scope", "idempotency_response", "control_record")
    docs = "\n".join(read(p) for p in PLAT_MD if "revisions" not in str(p))
    for n in names:
        f = PLAT / "schemas" / f"{n}.schema.json"
        ok(f"schema file {n}", f.exists())
        if f.exists():
            try:
                SL.validate({}, json.loads(read(f)))
                ok(f"schema {n} loads and uses only supported keywords", True)
            except ValueError as e:
                ok(f"schema {n} loads and uses only supported keywords", False, str(e))
        ok(f"schema {n} referenced in docs", f"{n}.schema.json" in docs)


def check_new_tests():
    bp = read(PLAT / "BUILD_PLAN_AND_ACCEPTANCE.md")
    alltext = "\n".join(read(p) for p in PLAT_MD if "revisions" not in str(p) and p.name != "BUILD_PLAN_AND_ACCEPTANCE.md")
    for i in range(50, 62):
        tid = f"T-{i}"
        ok(f"{tid} defined", re.search(r"^\| " + tid + r" \|", bp, re.M) is not None)
        ok(f"{tid} mapped in BUILD_PLAN 4.1 or 4.2", len(re.findall(tid + r"(?!\d)", bp)) >= 2 or tid in alltext)
        in_range = any(re.search(r"T-(\d+)～T-(\d+)", m.group(0)) and int(re.search(r"T-(\d+)～T-(\d+)", m.group(0)).group(1)) <= i <= int(re.search(r"T-(\d+)～T-(\d+)", m.group(0)).group(2)) for m in re.finditer(r"T-\d+～T-\d+", bp + alltext))
        ok(f"{tid} referenced outside its own definition", (tid in alltext) or in_range or len(re.findall(tid + r"(?!\d)", bp)) >= 2, tid)
    r = subprocess.run([sys.executable, str(PLAT / "tools" / "test_checks.py")], capture_output=True, text=True)
    ok("tools/test_checks.py counterexamples all caught", r.returncode == 0, (r.stdout + r.stderr).strip()[:600])


# ------------------------------------------------------------ 5. 工時
def check_hours():
    bp = read(PLAT / "BUILD_PLAN_AND_ACCEPTANCE.md")
    rows = re.findall(r"^\| (WP-\d+a?)[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\| (\d+)～(\d+) \|", bp, re.M)
    hours = {w: (int(a), int(b)) for w, a, b in rows}
    first = [f"WP-0{i}" for i in range(0, 8)] + ["WP-08a"]
    mvp = [w for w in hours if w != "WP-19" and int(re.match(r"WP-(\d+)", w).group(1)) <= 18]
    f = (sum(hours[w][0] for w in first), sum(hours[w][1] for w in first))
    m = (sum(hours[w][0] for w in mvp), sum(hours[w][1] for w in mvp))
    ok("BUILD_PLAN first-batch total text", f"第一批次（WP-00～WP-07＋WP-08a）約 {f[0]}～{f[1]} 人日" in bp, str(f))
    ok("BUILD_PLAN MVP total text", f"MVP 全部（不含 WP-19）約 {m[0]}～{m[1]} 人日" in bp, str(m))
    weeks2 = (int(m[0] / 10 + 0.5), int(m[1] / 10 + 0.5))
    weeks1 = (int(m[0] / 5 + 0.5), int(m[1] / 5 + 0.5))
    ok("BUILD_PLAN weeks text", f"以 2 名工程師並行約 {weeks2[0]}～{weeks2[1]} 週；1 名約 {weeks1[0]}～{weeks1[1]} 週" in bp, f"{weeks2} {weeks1}")
    pack = read(PLAT / "BATCH1_EXECUTION_PACK.md")
    ok("pack total", f"合計 {f[0]}～{f[1]} 人日" in pack, str(f))
    # 批次執行包的任務工時加總 = WP 工時
    task_rows = re.findall(r"^\| (B(\d)-\d) \|.*\| ([\d.]+)(?:～([\d.]+))? \|$", pack, re.M)
    per = {}
    for tid, wp, lo, hi in task_rows:
        key = "WP-08a" if wp == "8" else f"WP-0{wp}"
        a, b = per.get(key, (0.0, 0.0))
        per[key] = (a + float(lo), b + float(hi or lo))
    for w in first:
        ok(f"pack tasks sum == {w}", per.get(w) == (float(hours[w][0]), float(hours[w][1])), f"{per.get(w)} vs {hours[w]}")
    seg = {"D1": ["WP-00", "WP-01", "WP-02", "WP-03"], "D2": ["WP-04"], "D3": ["WP-05", "WP-06"], "D4": ["WP-07", "WP-08a"]}
    for k, ws in seg.items():
        lo, hi = sum(hours[w][0] for w in ws), sum(hours[w][1] for w in ws)
        ok(f"pack segment {k} hours", f"{lo}～{hi}" in pack, f"{lo}～{hi}")
    ops = read(PLAT / "OPERATIONS_AND_PRIVACY.md")
    wan = (int(m[0] * 6000 / 10000 + 0.5), int(m[1] * 8000 / 10000 + 0.5))
    ok("OPERATIONS engineering cost row", f"NT${wan[0]}～{wan[1]} 萬（{m[0]}～{m[1]} 人日）" in ops, str(wan))
    one = (int(wan[0] + 4.5 + 10 + 5 + 0.5), int(wan[1] + 4.5 + 30 + 15 + 0.5))
    ok("OPERATIONS pilot build-cost sentence", f"一次性建置約 NT${one[0]}～{one[1]} 萬" in ops, str(one))
    ok("DECISIONS G-01 hours", f"MVP 工程估 {m[0]}～{m[1]} 人日" in read(PLAT / "DECISIONS_AND_UNKNOWNS.md"))
    stale = ["42～61", "90～135", "NT$54～108", "NT$74～158", "2 名工程師並行約 9～14 週", "18～27 週",
             "45～65 人日", "100～152 人日", "NT$60～122", "NT$80～172", "10～15 週；1 名約 20～30 週"]
    for p in PLAT_MD:
        if "revisions" in str(p):
            continue
        t = "\n".join(l for l in read(p).splitlines() if "相對 v0.2-draft" not in l and "相對 R1" not in l and "R1 修正對工時" not in l)
        for s in stale:
            ok(f"stale number {s} in {p.name}", s not in t)


# ------------------------------------------------------------ 5b. 表格欄數
def check_tables():
    for p, text in TEXT.items():
        lines = text.splitlines()
        in_code = False
        i = 0
        while i < len(lines):
            if lines[i].startswith("```"):
                in_code = not in_code
            if not in_code and lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
                n = len(re.sub(r"`[^`]*`", "", lines[i]).strip().strip("|").split("|"))
                j = i + 2
                while j < len(lines) and lines[j].startswith("|"):
                    m = len(re.sub(r"`[^`]*`", "", lines[j]).strip().strip("|").split("|"))
                    ok(f"table columns {p.relative_to(ROOT)}:{j + 1}", m == n, f"{m} vs {n}")
                    j += 1
                i = j
            else:
                i += 1


# ------------------------------------------------------------ 6. 其他
def check_misc():
    r = subprocess.run([sys.executable, str(PLAT / "tools" / "gen_state_machines.py"), "--check"], capture_output=True, text=True)
    ok("state machines in sync", r.returncode == 0, r.stdout + r.stderr)
    versions = {re.search(r"版本：([^｜\n]+)", read(p)).group(1) for p in PLAT.glob("*.md") if re.search(r"版本：([^｜\n]+)", read(p))}
    ok("platform doc version labels identical", len(versions) == 1, str(versions))
    for f in ("synthetic_resources.json", "synthetic_households.json"):
        ok(f"{f} is_synthetic", json.loads(read(PLAT / "examples" / f))["is_synthetic"] is True)
    pii = [(re.compile(r"[A-Z][12]\d{8}"), "id-number"), (re.compile(r"\b09\d{8}\b"), "mobile"),
           (re.compile(r"[\w.+-]+@(?!example\.invalid)[\w-]+\.[\w.]+"), "email")]
    for p in list((ROOT / "docs").rglob("*")) + [ROOT / "README.md"]:
        if p.is_file() and p.suffix in (".md", ".json", ".py"):
            t = read(p)
            for rx, kind in pii:
                for m in rx.finditer(t):
                    if kind == "email" and m.group(0) in ("noreply@anthropic.com",):
                        continue
                    ok(f"no {kind} pattern in {p.relative_to(ROOT)}", False, m.group(0))
    r2 = PLAT / "revisions" / "R2_RESPONSE.md"
    ok("R2_RESPONSE exists", r2.exists())
    if r2.exists():
        t2 = read(r2)
        for i in range(1, 9):
            ok(f"R2_RESPONSE mentions F-{i:02d}", f"F-{i:02d}" in t2)
    r1 = PLAT / "revisions" / "R1_RESPONSE.md"
    if r1.exists():
        t = read(r1)
        for i in range(1, 13):
            ok(f"R1_RESPONSE mentions R-{i:02d}", f"R-{i:02d}" in t)


def main():
    sm = json.loads(read(PLAT / "state_machines.json"))
    check_links()
    check_ids(sm)
    check_fields()
    check_matrix()
    check_citations()
    check_schemas()
    check_new_tests()
    check_hours()
    check_tables()
    check_misc()
    if FAILS:
        print(f"FAILED ({len(FAILS)} of {N} checks):")
        for f in FAILS:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {N} doc checks passed")


if __name__ == "__main__":
    main()
