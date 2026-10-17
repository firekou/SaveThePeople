# D1-A 修補回收回覆（D1A-01／02／03）

- work_id：STP-PLATFORM-PLAN-001
- task_id：STP-PLATFORM-PLAN-001-D1-A-CATALOG
- 狀態：AUTHOR_EVIDENCE（作者自檢，非 GPT 覆核、非 APPROVED；未 merge、未部署）
- next_actor：GPT（獨立覆核）
- 授權來源：Frank 2026-10-17 指示（「修好既有產品，不重新規劃、不重建另一個網站」；明確允許本 session 接手，不冒充原 session）
- 接手宣告：PR #1 issuecomment-6232347648；開始 2026-10-17T09:34:18Z，期限 2026-10-17T11:04:18Z（90 分鐘）
- 原 repair1 期限 2026-10-13T14:09:39Z 已過期；該紀錄保留，本回覆不主張其仍有效
- source SHA（原產品）：914216cabdb7760f749265fee718b243764cee2b
- planning/review candidate：b360d77e6a0811f8b215318f98470c24815759c3
- trusted base：9a7bd1295e20837786acc45bdab7fb94f5a1b012
- 修補程式 commit：0225e418c42f7a038d59f96d4ac1c5214dbbe3d8（證據與本回覆在其後一個 commit；結果 SHA 見 PR #1 交付留言）
- 分支：ccr-dd86219c-ijac1h（自 914216c 延伸，非 force）

## 1. 範圍

只修補 GPT_D1_A_REVIEW_914216C_20261013 的 D1A-01、D1A-02、D1A-03 與證據腳本彙總失敗問題。未重新規劃、未新增功能、未修改 fixture、四基線、原作者證據、GPT 報告或既有歷史回覆。

變更檔案：

| 檔案 | 變更 |
|---|---|
| product/catalog/importer.py | D1A-01 逐筆旗標驗證、明確寫入旗標；D1A-02 URL 解析驗證 |
| product/catalog/management/commands/import_synthetic_catalog.py | 輸出加 `inherited_flag=` 計數 |
| product/scripts/serve.sh | D1A-03 重寫：bind 白名單、程序身分紀錄與核對、確認停止才移除紀錄 |
| product/scripts/collect_http_evidence.sh | 逐步記錄結束碼、彙總失敗、非零結束；輸出到 evidence/repair-recovery/ |
| product/catalog/tests/test_import_repair.py | 新增 9 個測試（DB） |
| product/catalog/tests/test_serve_script.py | 新增 12 個測試（stub，不終止無關程序） |
| product/README.md | 匯入規則、serve.sh 規則與結束碼、收證腳本 |
| product/evidence/repair-recovery/* | 本輪新證據（原 product/evidence/* 未覆寫） |

## 2. 逐項結果

### D1A-01 逐筆 is_synthetic

- 原反例：在 fixture 的任一記錄加 `"is_synthetic": false`（或 `"false"`、`1`、`null`），原 914216c importer 照常匯入 6 資源，且 ORM 預設 `default=True` 把該筆改標為合成。重跑結果：`resources[0].is_synthetic=false` 與 `sources[2].is_synthetic='false'` 皆 ACCEPTED，created 為 3/6/2/6/6（original_counterexamples.txt）。
- 合法對照：未修改的 fixture 匯入 regions 3／sources 6／scopes 2／resources 6／versions 6；重跑 created 全 0（冪等）；記錄層明確 `true` 可匯入。
- 變更位置：importer.py `_flag_problems()`、`validate_dataset()`、`_record_flag()`、`import_dataset()`。
- 規則：
  - 檔案層 `is_synthetic` 必須正好是布林 `true`。
  - 任何層級的物件只要帶 `is_synthetic`，值就必須正好是布林 `true`，否則整檔拒絕。涵蓋地區、來源、範圍、資源、版本、規則及其他巢狀物件。
  - 相容規則：記錄未帶旗標時繼承檔案層宣告。繼承筆數會出現在 `run.inherited_flag` 與命令輸出中，現行 fixture 不需修改。
  - 寫入時每個 `create`／`get_or_create` 都明確傳入 `is_synthetic=True`，不依賴 ORM 預設值。
  - 驗證在交易外先跑一次，交易內第一筆寫入前再跑一次。
- 實際結果（修補後）：6 種值 × 6 種記錄類型全部 REJECTED，原因為 `non-synthetic or invalid per-record is_synthetic flag(s): $.resources[0].is_synthetic=False`。在空 DB 與已有資料的 DB 上，各表與 ImportRun 筆數都不變。即使繞過驗證器，DB CHECK 約束仍會拒絕寫入。
- 預期拒絕原因：記錄層明示非合成或非法旗標，不得被預設值改標。

### D1A-02 來源網址解析

- 原反例：`https://example.invalid.attacker.invalid/x`、userinfo 偽裝網址（`https://example.invalid` 後接 `@` 再接 `attacker.invalid/x`）、`ftp://example.invalid/x` 在 914216c 皆 ACCEPTED，並原樣存入 `url_or_ref`。
- 合法對照：`https://example.invalid/...`、`http://example.invalid/...`、`HTTPS://EXAMPLE.INVALID/Case`（主機名稱不分大小寫）、`https://example.invalid`，以及既有的非網址合成說明 S-0005，皆可匯入。
- 變更位置：importer.py `source_ref_problem()`，由 `validate_dataset()` 對每個來源呼叫。
- 規則：用 `urllib.parse.urlsplit` 解析。
  - scheme 只允許 http／https。
  - 不允許 userinfo，也不允許明示連接埠。
  - hostname 必須正好是 `example.invalid`；子網域不在允許範圍，結尾點也拒絕。
  - 不允許空白、控制字元或反斜線。
  - 看起來像網址的字串（有 scheme、含 `://` 或以 `www.` 開頭）一律按 URL 規則檢查；非網址文字中若夾帶網址也拒絕。
  - 全程不發出任何網路請求，測試以 patch `socket.connect` 驗證。
- 實際結果：
  - 後綴攻擊 → `hostname 'example.invalid.attacker.invalid' is not exactly example.invalid`
  - userinfo → `userinfo in URL is not allowed`
  - ftp → `scheme 'ftp' not allowed`
  - 其他非法 URL（無主機、`[::1`、port 99999 等）→ 對應原因
  - 拒絕後各表筆數不變。
- 預期拒絕原因：來源不是 example.invalid 合成網址，視同非合成資料。

### D1A-03 serve.sh 程序安全

- 原反例（靜態列出，未實際執行，以免真的綁定萬用位址或對外部 PID 送訊號）：
  - `BIND` 原樣使用，可傳入 0.0.0.0。
  - pidfile 只存一個整數，`kill -0`／`kill` 不核對身分。
  - 不論是否確認停止，都會 `rm -f` pidfile。
  - 健康檢查失敗時，已產生的程序被留下。
- 合法對照：`127.0.0.1:<port>` 的 start／status／stop 正常；stop 重複執行回「not running」並 exit 0。
- 變更位置：scripts/serve.sh 全檔（validate_bind、read_record、identity、stop_ours、start/stop/status）。
- 規則：
  - bind 只接受 `127.0.0.1:1024-65535`，在產生程序前檢查；空值也拒絕。
  - 紀錄檔：
    - 原子寫入、0600、本人擁有、非符號連結；
    - 恰好 6 個已知鍵：pid、啟動時間、checkout、bind、32 位十六進位 launch token、python。
  - 送訊號前核對 `/proc`：
    - 啟動時間（防 PID 重用）；
    - checkout 與 cwd；
    - 完整 cmdline；
    - environ 中的 `STP_LAUNCH_TOKEN`。
  - 任何一項不符即視為外部程序：exit 3，不送訊號，紀錄保留。
  - 只有確認程序已消失（含 zombie）才移除紀錄。kill 失敗或逾時仍存活時 exit 4，紀錄保留。
  - 健康檢查失敗只停止已核對身分的自身程序（exit 1）；無法確認時 exit 5。
- 實際結果（test_serve_script.py，12 測試，stub）：

  | 情境 | 結果 |
  |---|---|
  | 萬用、區網、主機名稱、非法 port、空 bind | exit 2，未產生程序 |
  | 正常啟停 | 只送一次 `-TERM <pid>`，紀錄已移除 |
  | 健康檢查失敗 | 只停自己 |
  | kill 失敗 | exit 4，紀錄保留 |
  | 仍存活 | exit 4 |
  | 外部 PID（啟動時間相同）、PID 重用、pid 1、他 checkout、token 錯 | exit 3，kill 呼叫 0 次 |
  | 紀錄檔異常（格式錯、pid 非法、多餘鍵、0644、符號連結、他人擁有） | start／stop 皆 exit 3，無訊號，紀錄保留 |
  | 已死的自身紀錄 | 清除，exit 0 |

  實機：`STP_BIND=0.0.0.0:8765 serve.sh start` 回 exit 2；loopback 監聽只見 127.0.0.1（http_db_evidence.txt）。
- 預期拒絕原因：非 loopback 或身分無法證明的程序一律不碰。

### 證據腳本彙總失敗

collect_http_evidence.sh 每步比對預期結束碼（負向步驟預期非零），最後列出 `SUMMARY steps=N failures=M`，有任何失敗即非零結束。實測：

- 首次執行時，腳本自身有兩處錯誤（測試輸入欄位名寫錯、列表筆數標記寫錯），另有 Chromium 路徑未設定，共 4 個 STEP_FAIL，exit 1。這證明後續成功的步驟不會掩蓋先前失敗。
- 修正腳本後重跑：58 步、0 失敗，exit 0。
- 首次失敗的輸出已被重跑覆寫，未另存；此處如實記錄。

### 突變檢查（mutation_checks.txt）

| 突變 | 結果 |
|---|---|
| M1 拿掉逐筆旗標檢查 | test_import_repair FAILED（failures=67, errors=5） |
| M2 拿掉 URL 檢查 | FAILED（failures=57） |
| M3 identity 永遠視為自身 | test_serve_script FAILED（failures=8） |
| M4 bind 檢查永遠通過 | FAILED（failures=11） |

檢查後原檔已還原（cmp 一致）。

## 3. 產品／DB／HTTP／UI 驗收（AUTHOR_EVIDENCE）

| 項目 | 指令 | 結果 | 證據 |
|---|---|---|---|
| 產品測試 | `manage.py test -v 2` | Ran 43（22 原有＋12＋9），OK，exit 0 | test_output.txt |
| migrate／migrate --check | 同上 | exit 0／exit 0 | test_output.txt、http_db_evidence.txt |
| 合法匯入、重複匯入 | `import_synthetic_catalog` | exit 0；重跑 created 全 0 | http_db_evidence.txt |
| 非法匯入回滾 | 逐筆 false、攻擊網址 | 皆非零結束；前後計數 `cmp` 相同 | http_db_evidence.txt |
| DB 只走 unix socket | `show listen_addresses` | 空字串 | http_db_evidence.txt |
| DB CHECK | 插入 is_synthetic=false | 拒絕 | http_db_evidence.txt |
| 列表／篩選／詳情／空態／未知地區／404 | 11 個 GET | 狀態碼與標記皆符合 | http_db_evidence.txt |
| API | `/api/public/resources` | is_synthetic=true，count>0 | http_db_evidence.txt |
| DB 中斷 | 停 PG 後 GET / | 500 安全頁、洩漏掃描 0、恢復後 200 | http_db_evidence.txt |
| 安全啟停與清理 | serve.sh start／status／stop／stop、pg stop | 全部符合預期；無殘留程序；停止後連線被拒 | http_db_evidence.txt |
| 360px＋鍵盤 | capture_evidence.py（Chromium 141.0.7390.37） | 8 張截圖；scrollWidth=360、無水平捲動；Tab 順序與鍵盤篩選結果 | ui_evidence.json、*.png |

## 4. 文件工具與四基線（非產品驗收）

| 指令 | 結果 |
|---|---|
| python3 docs/platform/examples/check_examples.py | OK: 1306 checks, exit 0 |
| python3 docs/platform/tools/gen_state_machines.py --check | OK: 6 machines/86 transitions, exit 0 |
| python3 docs/platform/tools/gen_permissions.py --check | OK: 25 classes/143 cells/42 API/12 pages, exit 0 |
| python3 docs/platform/tools/test_checks.py | OK: 136 counterexamples, exit 0 |
| python3 docs/platform/tools/check_docs.py | 修補 commit 0225e41：OK 2180 doc checks, exit 0；加入本回覆後重跑：OK 2209 doc checks, exit 0（首次重跑因本回覆含 userinfo 網址字面被 email 樣式檢查擋下 1 項，已改寫描述） |
| git diff 9a7bd12 HEAD -- 四基線 | 0 bytes, exit 0 |

完整 stdout／stderr／exit 見 doc_tools_and_baselines.txt。914216c→修補 commit 在 product/ 以外無差異；本回覆檔是唯一新增的非 product 檔案。

## 5. 待對帳的額外路徑（列出，不追認）

914216c 相對 trusted base 9a7bd12，在 product/ 以外另有兩個檔案的差異，來自 37764f6。本輪未修改、未追認，交由 GPT 對帳：

- README.md（+20 行）
- docs/governance/CLAUDE_EXECUTOR_PROMPT.md（+379 行）

## 6. NOT_RUN 與限制

- 原 914216c 的 serve.sh 沒有實際執行反例，只做靜態列出；原因是避免真的綁定萬用位址或對外部 PID 送訊號。修補後的行為以 stub 測試與實機 loopback 驗證。
- 未在其他作業系統或真實多使用者環境測試。紀錄檔「他人擁有」情境以 chown 65534 模擬。
- 環境沒有 init reaper，停止後的 postgres 程序會短暫以 `<defunct>` 留在程序表。serve.sh 把 Z／X 狀態視為已結束。
- 無公開部署、雲端資源、外部 AI、外部通知、正式憑證或真實資料。

## 7. 資源與清理

- 外部新增成本 0。
- 依賴裝在獨立 venv，依 requirements.lock.txt。
- 本機私有 PostgreSQL 16 叢集位於 /var/tmp/stp_rr_pg（只開 unix socket），結束時已停止。
- 為重現原反例建立的 914216c 臨時 worktree 已移除。
- 測試產生的程序都由測試自行結束。

## 8. Prompt 2／3／4 狀態

- Prompt 2（D2 合成引導）：NOT_STARTED。前置條件是 D1A-01～03 經 GPT 獨立關閉並取得明確的產品驗收範圍，目前尚未達成。
- Prompt 3（資源資料管線）：NOT_STARTED。前置條件是前包通過，或 GPT 明確允許本包獨立進行；目前查無此允許。
- Prompt 4（公開資源試點）：另行回報，不包含在本次交付中。

現在：Claude〔已交付 D1-A 修補回收，AUTHOR_EVIDENCE〕；GPT〔待獨立覆核〕；Frank〔不需搬運驗證 Prompt〕。
