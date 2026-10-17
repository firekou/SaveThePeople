# SaveThePeople D1-A：合成資源目錄（本機示範）

本目錄是第一個可本機啟動、可點選、手機可操作的**合成資料**資源目錄網站。
全部資料來自 `docs/platform/examples/synthetic_resources.json`（6 項資源、6 個來源、2 種家庭口徑，示範縣，`example.invalid`）。
沒有真實個案、沒有對外連線、沒有部署；目錄展示不等於正式推薦，初篩不等於主管機關核定。

範圍（D1-A）：資源列表、資源詳情、依地區與類別篩選、合成標示／來源／擷取日期／有效狀態、未知期限與過期資源說明、空白／錯誤／不存在頁、`GET /api/public/resources`。
不含問答、個案工作台、上傳、聯絡表單、登入、通知、申請送件。

## 需求
- Python 3.11 以上（本次驗證：3.11.15）。
- PostgreSQL 16 本機二進位（`/usr/lib/postgresql/16/bin`；本次驗證：16.14）。
- 可連 PyPI 安裝 `requirements.txt`（Django 5.2.18、psycopg 3.3.6）。

## 安裝
```bash
cd product
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt            # 或 pip install -r requirements.lock.txt 取得完全相同版本
```

## 設定
所有設定來自環境變數，預設值即為本機合成測試值（見 `.env.example`）。不需要任何正式憑證。
`DEBUG` 固定為 False；只允許 `127.0.0.1` 與 `localhost`。

## 啟動資料庫（私人叢集，只開 unix socket，不開 TCP）
```bash
scripts/pg_local.sh init       # 建立 $STP_PG_DIR（預設 /var/tmp/stp_d1a_pg），使用者 stp_d1a，socket 信任
scripts/pg_local.sh start
scripts/pg_local.sh createdb   # 建立 stp_catalog
```
以 root 執行時腳本會自動改用 `postgres` 系統使用者；一般使用者直接執行。

## 遷移與匯入
```bash
python manage.py migrate
python manage.py migrate --check
python manage.py import_synthetic_catalog            # 第一次：created 3/6/2/6/6
python manage.py import_synthetic_catalog            # 第二次：全部 unchanged，不新增、不覆蓋
```
匯入規則：檔案必須宣告 `is_synthetic: true`；任何記錄（地區、來源、範圍、資源、版本、規則）若自帶 `is_synthetic`，必須正好是布林 `true`，
`false`、`"true"`、`1`、`null` 等一律拒絕；未帶旗標的記錄繼承檔案層宣告（輸出 `inherited_flag=` 計數），寫入時一律明確指定、不依賴 ORM 預設值。
來源網址以 URL 解析器檢查：只允許 `http`/`https`、主機名稱必須「正好」是 `example.invalid`（不含子網域、不允許結尾點、userinfo 或連接埠）；
非網址的合成說明文字允許，但不得夾帶網址。匯入不發出任何網路請求。資源代碼必須是 `TW-DEMO-*`；
已匯入的版本內容不可變（同一 `version_label` 內容不同即拒絕，需用新的 `version_label` 新增版本）；
任何拒絕都在交易內回滾，不留部分匯入。每張表都有資料庫 CHECK 約束 `is_synthetic = true`。

## 啟動與停止網站（只綁 loopback）
```bash
scripts/serve.sh start         # http://127.0.0.1:8765/
scripts/serve.sh status
scripts/serve.sh stop
scripts/pg_local.sh stop
```
`serve.sh` 安全規則：`STP_BIND` 只接受 `127.0.0.1:<1024-65535>`，萬用位址、區網位址、主機名稱與空值在啟動前即拒絕（不產生程序）。
啟動時寫入 0600 權限的紀錄檔（pid、程序啟動時間、checkout 路徑、bind、隨機 launch token、python 路徑）；停止前逐項核對
`/proc` 中的啟動時間、工作目錄、完整命令列與環境中的 launch token，任何一項不符即視為外部程序，不送訊號。
只有確認程序已結束才移除紀錄檔；健康檢查失敗只停止自己剛啟動的程序。
結束碼：0 成功；1 啟動健康檢查失敗（已停止自身程序）；2 參數或 bind 不合法；3 紀錄檔異常／外部程序（未送任何訊號、紀錄保留）；
4 停止未獲確認（紀錄保留）；5 啟動失敗且無法確認清理。

## 端到端收證（HTTP／DB／DB 中斷／啟停）
```bash
STP_CHROMIUM=/path/to/chrome scripts/collect_http_evidence.sh   # 輸出 evidence/repair-recovery/http_db_evidence.txt
```
每一步都記錄結束碼並比對預期（含預期失敗的負向步驟）；只要任一步不符，最後 `SUMMARY` 列出失敗清單並以非零結束，
後續成功的步驟不會掩蓋先前的失敗。輸出目錄可用 `STP_EVIDENCE_DIR` 改變。

## 測試
```bash
python manage.py test          # 43 個測試：原 22 個＋serve.sh 12 個（stub）＋匯入修補 9 個；原 22 個涵蓋匯入冪等／不可變／拒絕非合成／回滾／DB 約束、列表與可見性、篩選、空態、404、500 安全頁、300KB
```
手機與鍵盤證據（需 `pip install -r requirements-test.txt` 與可用的 Chromium）：
```bash
STP_CHROMIUM=/path/to/chrome python scripts/capture_evidence.py http://127.0.0.1:8765 evidence
```

## 3 分鐘展示步驟（全程合成資料）
1. `scripts/pg_local.sh start && scripts/serve.sh start`，開 `http://127.0.0.1:8765/`：列表 5 項（生活扶助、急難救助、甲區午餐、兒少補助、物資箱）。每項顯示狀態、來源筆數與最後擷取日期；租屋補助（已過期）不在列表。
2. 地區選「示範縣乙區」按篩選：剩 4 項（甲區午餐補助不再出現）。再選類別「就學」：顯示「目前此地區此類別尚無已查核資源」與 1957 提示。
3. 點「示範食物互助協會物資箱」：看到「期限未知」「名額已滿」標記，與「截止日未知，需先人工確認，不列為正式推薦」說明。
4. 直接開 `/resources/TW-DEMO-RENT-006/`：紅色「歷史版本：已過期」橫幅，說明不在公開列表、不可依此申請。
5. 開 `/resources/TW-DEMO-NOPE-999/`：可理解的 404 頁；`/?region=NOWHERE`：「查無此地區」空態。
6. `scripts/pg_local.sh stop` 後重新整理列表：顯示「資料暫時無法載入」安全頁（無 traceback、無連線字串）；`scripts/pg_local.sh start` 後恢復。
7. 結束：`scripts/serve.sh stop && scripts/pg_local.sh stop`。

查詢參數 `as_of=YYYY-MM-DD` 可改變評估基準日（例如 `?as_of=2026-07-01` 會把甲區午餐補助標為「2026-08-01 起適用」）。

## 目錄
- `stp_catalog/`：Django 專案設定（DEBUG=False、loopback、PostgreSQL）。
- `catalog/models.py`：Region、Source、HouseholdScopeDefinition、Resource、ResourceVersion、ImportRun（DATA_MODEL §2.1–2.4 最小子集）。
- `catalog/visibility.py`：`catalog_visibility`（引擎 §0.1 的唯一展示判定；不做 §0.2 推薦判定）。
- `catalog/importer.py`、`catalog/management/commands/import_synthetic_catalog.py`：冪等、fail-closed 匯入。
- `catalog/views.py`、`catalog/templates/catalog/`：列表、詳情、API、404、500。
- `scripts/`：`pg_local.sh`、`serve.sh`、`capture_evidence.py`、`collect_http_evidence.sh`。
- `evidence/`：D1-A 原交付的實際畫面與 JSON 證據（合成，保留不覆寫）；`evidence/repair-recovery/`：D1A-01～03 修補回收的作者證據。
