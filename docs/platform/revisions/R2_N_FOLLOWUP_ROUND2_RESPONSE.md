# R2_N_FOLLOWUP 第二輪回覆（僅 N-03）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP｜round 2／2｜工單：issuecomment-6111214276（handoff 143245c）
source：7bd0c69705bfda2562a81f7fa751be0e21a4981b｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
驗證層級：文件政策檢查＋純邏輯參考模擬（AUTHOR_EVIDENCE；非 VERIFIED、非 APPROVED）。合成資料，無真實資料。

## N-03 對照
- **根因**：雜湊錨點是「寫入後盡力補記」，補記失敗仍回 200／202；還原只比對「已存在」的錨點，缺錨點的紀錄被當成已被見證。攻擊：合法撤回（REMINDERS＋REFERRAL_SHARE）→錨點補記失敗→縮減用途並重算合法鏈→還原放行、轉介仍 SENT。另 `Witness.report` 的 `TimeoutError` 未轉成規範的 503。
- **修改位置**：`examples/ref_control.py`（`Witness.record_hash` 改為同步確認並可失敗／逾時；`request_control` 在 DB 套用與 200／202 前要求錨點確認，失敗回 503 `ANCHOR_UNCONFIRMED`；新增 `reanchor_missing`；`recover` 對每筆非 APPLIED 紀錄要求錨點，缺則 `ANCHOR_MISSING_AT_n`；`UNCONFIRMED` 涵蓋 TimeoutError）、`OPERATIONS_AND_PRIVACY.md` §1.3.3、`ARCHITECTURE.md` revoke API 順序文字。
- **案例**：`control_cases.json` 新增 CS-22～CS-32（共 32 個）；`check_examples.py` 新增 witness 模式 `hash_fail_next`／`timeout_next`／`hash_timeout_next` 與 `rewrite_log_entry.set_purposes`。
- **反例（合法新 payload，不靠 422）**：CS-22 錨點失敗→503、主庫不動、還原隔離；CS-23 GPT 攻擊（縮減用途重算鏈）→ `ANCHOR_MISSING_AT_1`；CS-24 合法重試補錨點後 200、還原放行；CS-25 補錨點仍失敗→503 不新增紀錄；CS-26 seq 確認逾時→503；CS-27 錨點逾時→503＋隔離；CS-28 錨點失敗後尾端遺失→`LOG_INCOMPLETE`；CS-29／30 同步錨點成功、主庫失敗 202，改寫被 `LOG_REWRITTEN_AT_1` 抓到／未改寫可還原重套；CS-31／32 HARD_DELETE、REDACT 的錨點失敗與重試。既有 CS-13～21 仍通過（未動期待值）。
- **人為破壞（`tools/test_checks.py::test_n03_round2`）**：移除還原的缺錨點檢查→攻擊被放行（被抓到）；忽略錨點未確認→不回 503（被抓到）；TimeoutError 不轉換→例外外洩（被抓到）；合法控制（錨點成功＋主庫失敗 202 可還原）通過。
- **可重跑命令**（repo 根目錄）：見下。

## 命令結果（皆 exit 0，stderr 空）
- `python3 docs/platform/examples/check_examples.py` → OK: 1239 checks passed
- `python3 docs/platform/tools/gen_state_machines.py --check` → OK: 6 state machines, 86 transitions, doc in sync
- `python3 docs/platform/tools/check_docs.py` → OK: 2009 doc checks passed
- `python3 docs/platform/tools/gen_permissions.py --check` → OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync
- `python3 docs/platform/tools/test_checks.py` → OK: test_checks 122 counterexample checks passed
- `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- <四份基線>` → 空

## 剩餘缺口
- 補錨點信任當下紀錄內容：失敗到重試之間若紀錄被改寫，補錨點無法偵測（此窗口內還原一律因缺錨點隔離）。
- 未驗證：真實見證服務與逾時語意、DB 交易原子性、備份整合演練、產品授權行為、法律可接受性（U-23）。
- not-run：`check_report_format.py`（NOT_FOUND）、遠端 CI（無）、產品測試（無產品）。
