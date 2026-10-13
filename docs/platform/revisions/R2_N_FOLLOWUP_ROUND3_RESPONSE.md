# R2_N_FOLLOWUP 第三輪回覆（僅 N-03 兩條繞過）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP｜round 3／3｜工單：issuecomment-6111510957（handoff 286f296）
source：c563865173a402c71af4c2b3ad3c46edac771200｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
驗證層級：文件政策檢查＋純邏輯參考模擬（AUTHOR_EVIDENCE；非 VERIFIED、非 APPROVED）。合成資料，無真實資料。

## 根因
補錨點（`reanchor_missing`）從「目前的紀錄內容」建立可信錨點，而還原只依目前 payload.type 判斷是否需要錨點。
- A：錨點失敗→縮減 REFERRAL_SHARE 並重算鏈→下一個無關合法請求把改寫後內容補成可信錨點→還原放行、r1 仍 SENT。
- B：錨點失敗→改成 `APPLIED`／ref 0 並重算鏈→APPLIED 免錨點→還原放行。

## 選擇的修法（原始意圖綁定，非保守全面拒絕）
- `Witness.report(seq, digest)`：寫入前同步持久確認 seq 時，同時綁定 `seq→完整 payload 摘要`（含 type、purposes、ref）；同 seq 不同摘要→`IntentConflict`→503 `INTENT_CONFLICT`，不可覆寫。
- `reanchor_missing`：缺錨點的紀錄（含偽裝成 APPLIED 者）只在摘要與見證綁定相符時才補；不符或無綁定→503 `INTENT_MISMATCH`，不寫任何東西；絕不從目前紀錄建立信任。
- `recover`：每筆紀錄（含 APPLIED）都比對見證綁定，不符→`INTENT_MISMATCH_AT_n`；其後仍要求非 APPLIED 紀錄有錨點。順序：鏈→見證可用→尾端→錨點雜湊改寫（LOG_REWRITTEN）→意圖→缺錨點。
- 合法重試保留：原始完整意圖在錨點失敗後，下一個請求會用見證綁定先補錨點再繼續（CS-24、CS-38）。見證持久保存綁定，caller 重啟不丟失。
- 受控恢復（不在自動路徑）：缺錨點或意圖不符時，由資料責任人與 R7 以見證綁定的原始摘要對照獨立保存的紀錄副本或備份後處理；具體 SOP 未訂（列為未決），在此之前維持隔離。
- 改動位置：`examples/ref_control.py`、`control_cases.json`（新增 CS-33～CS-38，共 38 個；CS-23 期待 reason 由 `ANCHOR_MISSING_AT_1` 改為 `INTENT_MISMATCH_AT_1`，因缺錨點前先比對意圖，理由為原路徑現在更早被意圖檢查擋下）、`check_examples.py`（rewrite 支援 `set_payload`；UnflushedWitness 簽名）、`tools/test_checks.py`、`OPERATIONS_AND_PRIVACY.md` §1.3.3、`ARCHITECTURE.md` revoke 順序文字。

## 驗收對照
1. 缺錨縮減用途→無關合法請求→503 `INTENT_MISMATCH`（主庫不動、無新增紀錄）→recover `INTENT_MISMATCH_AT_1`、r1 仍 SENT（CS-33；test_checks `_r3_attack('A')`）。
2. 缺錨偽裝 APPLIED／ref0：直接 recover 與先送無關請求皆 `INTENT_MISMATCH_AT_1`（CS-34、CS-35；`_r3_attack('B')`）。已錨定的 APPLIED 被改寫由 `LOG_REWRITTEN_AT_2` 擋下（CS-36）。
3. 合法重試只重試見證綁定的原始完整意圖（CS-24、CS-38）；同 seq 不同意圖→`INTENT_CONFLICT`（CS-37）。
4. 保留：正常 200 完整撤回、已錨定 202 可重套且 r1 CANCELLED（CS-29/30）、seq／錨點逾時 503 主庫不變（CS-26/27）、尾端遺失隔離（CS-28）、HARD_DELETE 不存在與 REDACT 列保留遮蔽（CS-31/32）。
5. 人為破壞（`test_n03_round3`）：補錨點不比對意圖→攻擊 A 的無關請求回 200（被抓到）；還原不比對意圖→攻擊 B 放行（被抓到）；兩者都移除→重現原繞過（還原放行、r1 SENT，作為預期失敗原因）；APPLIED 免補錨點意圖檢查→偽裝 APPLIED 被放行（被抓到）。
6. 既有 `test_n03_mutation` 的「移除雜湊比對」破壞版本，因意圖檢查現在也會擋下改寫，改為同時移除兩者才預期放行（理由：兩道檢查重疊）；未弱化任何預期。

## 命令結果（於交付 SHA，repo 根目錄；皆 exit 0，stderr 空）
- `python3 docs/platform/examples/check_examples.py` → OK: 1306 checks passed
- `python3 docs/platform/tools/gen_state_machines.py --check` → OK: 6 state machines, 86 transitions, doc in sync
- `python3 docs/platform/tools/gen_permissions.py --check` → OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync
- `python3 docs/platform/tools/test_checks.py` → OK: test_checks 136 counterexample checks passed
- `python3 docs/platform/tools/check_docs.py` → OK: 2009 doc checks passed
- 四份基線 `git diff 9a7bd12 HEAD` → 空

## 未證明／未決
- 見證實作（真實獨立服務的持久性、逾時語意）、DB 交易、備份整合演練、產品授權行為、法律可接受性（U-23）。
- 受控恢復 SOP 未訂；見證與紀錄同時被攻擊者控制的情境不在此模型內。
- 見證綁定摘要的儲存、保留期限與存取權限屬產品設計，未決。
- not-run：`check_report_format.py`（NOT_FOUND）、遠端 CI（無）、產品測試（無產品）。
