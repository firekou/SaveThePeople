# R2_REPAIR_RESPONSE｜STP-PLATFORM-PLAN-001｜F-01／F-03／F-07 修補

作者：Claude（執行端，作者層級，非獨立覆核）｜日期：2026-10-05｜task_id：STP-PLATFORM-PLAN-001-R2-GPT-REPAIR-20261005
session：session_01PNBQLMHHDqYoqVg1sxmAm9｜結果分支：`claude/tender-allen-89joyz`（PR #1 head 不變）
source content：c1d56496bb210518314254b88d9c8b52e56408d9｜base／main：9a7bd1295e20837786acc45bdab7fb94f5a1b012｜起點（review_record／PR #1 head）：67e0c7998054a253267cf94d6dee9b76fded7062
驗證層級：文件政策檢查＋純邏輯參考模擬（AUTHOR_EVIDENCE）。產品自動化測試、人工演練：**未做**。

## 對照表（finding → 根因 → 位置 → 反例 → 命令 → 結果 → 缺口）

### F-01 CUSTOM expression 未知鍵被忽略
- 根因：`_expr_problems` 只讀 `op`／`children`，其他鍵靜默忽略，而 schema 的 node 拒絕額外欄位。
- 修改：`examples/ref_engine.py`（`NODE_KEYS`；逐節點遞迴拒絕未知鍵、空鍵名；`op` 不支援者仍只報 `UnsupportedError`，維持 N_OF_M 原行為）。推薦入口 `recommendation_status` 經 `rule_problems` 使用同一驗證。
- 反例（`examples/engine_cases.json` illegal_expression_variants，經 `check_examples.py`）：根層 `not`、深層 `weight`、空字串鍵、`children` 錯型別、`op` 錯型別 → 皆 `NOT_RECOMMENDED／RULE_INVALID`；`rule_problems` 具體訊息 `unknown expression node key`。合法巢狀 ALL／ANY 仍 FORMAL（既有控制）。
- 人為破壞：移除鍵檢查後 `check_examples.py` exit 1（9 項失敗，含 FORMAL 誤判）。
- GPT 原重現（`expression={"op":"ALL","children":["C1"],"not":true}`）現為 `{'status': 'NOT_RECOMMENDED', 'reasons': ['RULE_INVALID']}`。

### F-03 P9 逐案影響顯示與資料權限矛盾
- 根因：P9 主要操作「查看受影響案件」、引擎 §8.2「P9 顯示每案處理進度」、ARCHITECTURE transitions API「暫停時回受影響案件清單」與「R5／P9 不得見個案內容」矛盾；權限工具只驗結構化授權，不驗文字承諾。
- 修改：`USER_JOURNEYS_AND_SCREENS.md` P9、`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §8.2、`ARCHITECTURE.md` transitions API 一律改為**資源層級影響摘要**（有無受影響案件、彙總件數；不含逐案 ID、家庭或處理進度）；逐案重評交 P7／P8 的 R3·ASG、R4·SITE-REV。`permissions.json` **未修改，未新增任何權限**。
- 新檢查：`tools/prose_policy.py`（`p9_problems`），接入 `check_docs.py`。
- 反例（`tools/test_checks.py`）：把「查看受影響案件」、「每案處理進度」、「受影響案件清單」放回去、或刪除「資源層級影響摘要／不含逐案」→ 皆被具體攔截。
- 缺口：「彙總件數」在極小件數時的再識別風險與顯示門檻未定（未擅自訂門檻，列為後續待決；非本輪範圍）。

### F-07 recheck_started_at 狀態生命週期不一致
- 選定單一規範（採 GPT 建議）：`recheck_started_at` **只存在於 NEEDS_RECHECK**；RV-07 寫入（每次重新進入都是新起算日）；離開 NEEDS_RECHECK 的 RV-08、RV-09、RV-12、RV-13 一律於同一交易清除；歷史只留在 RV-07 的 AuditEvent。RV-11 自 SUSPENDED 進入 PUBLISHED 時欄位本已為空。14 天暫行門檻未改。
- 修改：`state_machines.json`（RV-09／12／13 pre；已用 `gen_state_machines.py` 重產 DATA_MODEL 生成區塊）、`DATA_MODEL_AND_STATE_MACHINES.md` §2.4／§2.4.1（刪除「RV-09 暫停時保留」）、`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §0.2、§8.0；`ref_engine.py`（非 NEEDS_RECHECK 帶起算日 → `VERSION_INVALID`；新增 `apply_version_transition` 參考實作生命週期）。
- 變更既有測試期待的說明：`F07-published-ignores-stale-recheck-start`（原期待 FORMAL）依本次裁定規範改為 `F07-published-with-stale-recheck-start-rejected`（期待 `VERSION_INVALID`）；期待值為依規範手算，非以 runner 輸出回填。
- 反例：PUBLISHED／SUSPENDED／EXPIRED／SUPERSEDED／RETIRED 帶起算日、PUBLISHED 帶亂碼起算日 → `VERSION_INVALID`；生命週期 RV-07→08→07→09→11、RV-12、RV-13 的欄位結果；缺／亂碼 trigger_date、錯來源狀態、錯操作者 → 拒絕；合法流程結果不被誤擋；原物件不被修改。`prose_policy.recheck_lifecycle_problems` 驗證 RV-08／09／12／13 的清除說明與「暫停保留」不得復活（逐一移除會被抓到）。
- 人為破壞：移除狀態×欄位檢查 → `check_examples.py` exit 1（6 項）；移除離開時清除 → exit 1（7 項）。
- 缺口：沒有真實資料庫交易；「同一交易清除」是規格與參考邏輯，未做整合驗證。

## 必跑命令（repo 根目錄；最終 content SHA 見交付留言）
```
python3 docs/platform/examples/check_examples.py        → OK: 942 checks passed（exit 0）
python3 docs/platform/tools/check_docs.py               → OK: 2009 doc checks passed（exit 0）
python3 docs/platform/tools/gen_state_machines.py --check → OK: 6 state machines, 86 transitions, doc in sync（exit 0）
python3 docs/platform/tools/gen_permissions.py --check  → OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync（exit 0）
python3 docs/platform/tools/test_checks.py              → OK: test_checks 62 counterexample checks passed（exit 0）
git diff origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md → 空（exit 0）
```
not-run：check_report_format.py（repo 無此檔，NOT_FOUND）；遠端 CI（repo 無 CI）；產品測試（無產品）。

## 邊界
外部呼叫無；支出 0；真實資料無（全為合成）；部署無；merge 無；基線文件未改；R1／R2 歷史與 GPT 紀錄未改；`permissions.json` 未改。法律結論、保存期限、U-xx、D-3xx 未動。無任何家庭因此取得幫助。
