# D1-A 交付回覆：合成資源目錄網站（本機可啟動、可點選、手機可操作）
work_id：STP-PLATFORM-PLAN-001｜task_id：STP-PLATFORM-PLAN-001-D1-A-CATALOG｜stage：D1_A｜一次初始交付
狀態：READY_FOR_GPT_REVIEW（作者自檢全部 AUTHOR_EVIDENCE；不自行 APPROVED、不 merge、不稱正式服務已啟用）
啟動依據與 claim：[D1_A_ACTIVATION_AND_CLAIM.md](D1_A_ACTIVATION_AND_CLAIM.md)；PR #1 claim 留言 issuecomment-6145294639。

## 座標
| 項目 | 值 |
|---|---|
| base／main | 9a7bd1295e20837786acc45bdab7fb94f5a1b012 |
| 候選 head（claude/stp-platform-plan-001） | 3e0bd9999e62787636843d8fe054e732b3f62305（已 non-force merge 進本分支，merge commit 00d4086） |
| 上一作者內容 | d755256040b1fb8ff5c3a6a48d2be3b7afd6f0c5（在候選歷史內；無 product/ 可重用） |
| 結果分支 | claude/relaxed-maxwell-q2b86k（本 session 平台指定分支） |
| result SHA | 以 PR #1 交付留言所載、`git ls-remote` 讀回的 SHA 為準（本檔不自引） |
| session | session_01U1KQKyyLgpjSHBhBLGqRq6 |
| 開始／deadline（session 時鐘，REPORTED） | 2026-10-13T12:09:39Z／2026-10-13T14:09:39Z；實作與自檢在期限內完成（GitHub 留言時間戳為獨立時鐘） |
| 外部成本 | 0；外部呼叫只有 GitHub（fetch／push／PR 留言）與 PyPI 套件下載 |

## 交付內容（product/）
- `stp_catalog/`：Django 5.2.18 專案；`DEBUG=False` 固定、`ALLOWED_HOSTS` 只有 127.0.0.1／localhost、設定全部來自環境變數、預設值皆為本機合成測試值（`.env.example`），無任何正式憑證。
- `catalog/models.py`：Region、Source、HouseholdScopeDefinition、Resource、ResourceVersion、ImportRun（DATA_MODEL §2.1–2.4 最小子集）。每張表有 CHECK 約束 `is_synthetic = true`；ResourceVersion 另有 `(resource, version_label)` 唯一與 `effective_unknown ⇔ effective_to IS NULL` 約束。
- `catalog/visibility.py`：`catalog_visibility`（引擎 §0.1 唯一展示判定）：PUBLISHED／NEEDS_RECHECK 列出；SUSPENDED／EXPIRED／SUPERSEDED／RETIRED 不列、直接連結顯示歷史狀態；CANDIDATE／DRAFT／IN_REVIEW 公開 404。附未生效（「某日起適用」）、期限未知（需人工確認、不列正式推薦）、期間已結束、名額已滿／需確認等白話說明。不做 §0.2 推薦判定。
- `catalog/importer.py`＋`import_synthetic_catalog`：讀既有 `docs/platform/examples/synthetic_resources.json`（未修改）。檔案須 `is_synthetic: true`、來源網址須在 example.invalid、資源代碼須 TW-DEMO-*；同一 version_label 內容不同即拒絕（版本不可變，需新 label）；全部在單一交易內，任何拒絕不留部分匯入；每次成功匯入記錄 ImportRun。
- 頁面：`/`（列表＋地區／類別篩選＋空態＋查無地區／類別）、`/resources/<key>/`（詳情、歷史版本橫幅）、`/api/public/resources`（JSON）、自訂 404、不碰資料庫的 500 安全頁。所有頁面含「合成資料，非真實個案」與「目錄展示不等於正式推薦；初篩不等於主管機關核定」。
- `scripts/pg_local.sh`（私人 PostgreSQL 16 叢集：unix socket、`listen_addresses=''`、port 54329）、`scripts/serve.sh`（只綁 127.0.0.1:8765）、`scripts/capture_evidence.py`（360px 截圖、水平捲動、Tab 順序、鍵盤篩選與開啟詳情）、`scripts/collect_http_evidence.sh`（整段 HTTP／DB／DB 失效／清理證據可重跑）。
- `README.md`：安裝、設定、啟動、匯入、測試、停止命令與 3 分鐘展示步驟；`requirements.txt`（Django 5.2.18、psycopg[binary] 3.3.6）、`requirements.lock.txt`（pip freeze）、`requirements-test.txt`（playwright 1.63.0，只用於 UI 證據）。
- `catalog/tests/test_catalog.py`：22 個測試。
- `evidence/`：8 張 360px 截圖、`ui_evidence.json`、`http_db_evidence.txt`、`test_output.txt`、`test_list.txt`（全部合成）。

## 與原規格對齊（指示第四節）
| 要求 | 結果 |
|---|---|
| 列表 5 項可展示 | 列表＝LIVING-001、EMERG-002、EDU-003、CHILD-004、FOOD-005（依資料集順序） |
| FOOD-005 顯示期限未知、需人工確認 | 列表標「期限未知」「名額已滿」；詳情「截止日未知，需先由人員向提供單位確認；在確認前不列為正式推薦」 |
| RENT-006 不進公開列表；歷史詳情標已過期 | 列表與 API 皆無；`?status=EXPIRED` 不能繞過；直接連結顯示「歷史版本：已過期」「不在公開列表、不可依此申請」 |
| 6 資源／6 來源／2 口徑 | DB 計數 resources 6、versions 6、sources 6、scopes 2、regions 3 |
| 規格差異 | 無需改資料。補充：資料集未提供 verified_at，頁面的「最後擷取日期」取該版本來源的 retrieved_at 並如此標示，未冒充查核人簽核日期 |

## 實際命令與結果（repo 根目錄／product/；全部 AUTHOR_EVIDENCE）
環境（OBSERVED）：Python 3.11.15、Django 5.2.18、psycopg 3.3.6、PostgreSQL 16.14（/usr/lib/postgresql/16/bin）、Chromium 141.0.7390.37（容器預裝，供 playwright 使用）。
| 命令 | stdout（末行） | stderr | exit |
|---|---|---|---|
| `python manage.py migrate` | Applying catalog.0001_initial... OK | 空 | 0 |
| `python manage.py migrate --check` | （無輸出） | 空 | 0 |
| `python manage.py import_synthetic_catalog`（第 1 次） | OK file_sha256=c6f0f152… created={regions 3, sources 6, scopes 2, resources 6, versions 6} | 空 | 0 |
| `python manage.py import_synthetic_catalog`（第 2、3 次） | created 全 0；unchanged={regions 3, sources 6, scopes 2, resources 6, versions 6} | 空 | 0 |
| `python manage.py test` | Ran 22 tests … OK | 空 | 0 |
| `scripts/collect_http_evidence.sh` | 見 evidence/http_db_evidence.txt（HTTP 11 個 GET、API、DB 計數、CHECK 約束拒絕、DB 失效 500、恢復、UI 7 頁、清理） | — | 0 |
| psql 插入 is_synthetic=false | ERROR: violates check constraint "catalog_resource_synthetic_only" | — | 1（預期） |
| `python3 docs/platform/examples/check_examples.py` | OK: 1306 checks passed | 空 | 0 |
| `python3 docs/platform/tools/gen_state_machines.py --check` | OK: 6 state machines, 86 transitions, doc in sync | 空 | 0 |
| `python3 docs/platform/tools/check_docs.py` | OK: 2153 doc checks passed（含本輪新增兩份 revisions 文件；提交前再跑一次並於 PR 留言列出） | 空 | 0 |
| `python3 docs/platform/tools/gen_permissions.py --check` | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | 空 | 0 |
| `python3 docs/platform/tools/test_checks.py` | OK: test_checks 136 counterexample checks passed | 空 | 0 |
| `git diff 9a7bd12 -- 四份基線` | 空（0 bytes） | — | 0 |

HTTP（curl 對 127.0.0.1:8765，as_of=2026-10-13）：`/` 200／7555 bytes／共 5 項；`/?region=DEMO-A` 共 5 項（含 EDU-003）；`/?region=DEMO-B` 共 4 項（無 EDU-003）；`/?region=DEMO-B&category=EDUCATION` 200 空態「尚無已查核資源」＋1957；`/?category=FOOD_GOODS` 共 1 項；`/?status=EXPIRED` 仍 5 項；`/?region=NOWHERE` 200「查無此地區」；`/?as_of=2026-07-01` EDU-003「2026-08-01 起適用」、FOOD-005「2026-10-01 起適用」；FOOD-005 詳情 200「截止日未知」；RENT-006 詳情 200「歷史版本：已過期」；`/resources/TW-DEMO-NOPE-999/` 404「找不到這個頁面」；`/api/public/resources` count 5、is_synthetic true。
DB 失效：停止 postgres 後 `GET /` 回 500、755 bytes，「資料暫時無法載入」，洩漏掃描（Traceback／OperationalError／使用者／port／路徑／psycopg）0 筆；重啟後 `GET /` 200。
綁定：/proc/net/tcp 只有 `LISTEN 127.0.0.1 8765`；postgres 無 TCP listener（socket only）。
手機／鍵盤（playwright，viewport 360×740，DPR 2）：7 頁 scrollWidth 360／innerWidth 360，無水平捲動；Tab 順序＝跳到主要內容→站名→地區 select→類別 select→篩選按鈕→5 個資源連結；鍵盤選乙區＋Enter → `/?region=DEMO-B&category=` 「共 4 項・示範縣乙區」；Tab 到第一個資源按 Enter → `/resources/TW-DEMO-LIVING-001/`。截圖：evidence/01～07（含 01b 鍵盤篩選結果）。首屏 HTML 最大 7,639 bytes（≤300KB）。
清理：serve.sh stop 與 pg_local.sh stop 後，無 runserver／task postgres 程序；8765 連線拒絕；系統既有 16/main 叢集（原本 down）未被動過。

## 測試清單（22，全部通過）
匯入：冪等且保留歷史、版本內容變更被拒且無部分匯入、新 version_label 新增不覆蓋、is_synthetic=false 拒絕且零寫入、外部網址拒絕、中途失敗全部回滾、DB 拒絕非合成列、DB 拒絕 effective_unknown 不一致。
頁面：列表 5 項且無 RENT-006、status 參數不能繞過、FOOD-005 期限未知說明、RENT-006 歷史頁、地區篩選（甲區 5／乙區 4／示範縣 5）、類別篩選與空態、未知地區／類別 200 空態、404 頁、DRAFT 不可見且 SUSPENDED 不列但詳情顯示暫停、未生效標示、API 與列表一致、首屏 <300KB、DB 失效 500 頁無洩漏。
單元：catalog_visibility 規則。

## 3 分鐘展示步驟
見 product/README.md「3 分鐘展示步驟」：啟動 → 看列表（5 項） → 篩選乙區（4 項）／乙區＋就學（空態） → 看物資箱詳情（期限未知、名額已滿） → 直接開租屋補助（已過期歷史） → 404／查無地區 → 停 DB 看安全頁 → 停止服務。

## 已完成／未完成
已完成：指示第四節 1～6 全部；第七節驗收 1～10 皆有實際命令與輸出（第 7 項以實際截圖與 JSON）。
未完成／未做：無 CI；無 admin 後台（非本交付）；問答、行動清單、工作台為下一階段；未部署、未公開。
限制：
- Python 為容器既有 3.11.15，不是 GPT 先前工單提到的 3.13；Django 5.2 LTS 支援 3.10–3.13，功能無差異，但「指定版本」不同，列為差異交 GPT。
- 網站以 Django 開發用 `runserver` 暫時提供（loopback、短時），不是正式 WSGI 部署；本交付不含部署。
- UI 證據由容器預裝 Chromium 141 產生；無真人手機測試。
- 所有「通過」為作者在單一環境自檢（AUTHOR_EVIDENCE）；產品、DB、HTTP、手機各項分開列出，文件工具通過不代表網站驗收。
- 沒有任何真實家庭取得幫助；P0～P3 無真實服務成果。

## 最小恢復方式（給 Reviewer）
乾淨 checkout 本分支 → `cd product` → 依 README：venv＋`pip install -r requirements.lock.txt` → `scripts/pg_local.sh init && start && createdb` → `migrate` → `import_synthetic_catalog` 兩次 → `manage.py test` → `scripts/collect_http_evidence.sh`（需 playwright 與 Chromium；缺瀏覽器時其餘證據仍可跑，UI 段標 NOT_RUN）。
若 PostgreSQL 16 二進位路徑不同，設 `PGBIN`；若 /var/tmp 不可寫，設 `STP_PG_DIR` 為短路徑（unix socket 路徑上限 107 bytes）。

next_actor：GPT（固定成果獨立產品覆核）。next_action：exact-head 重現上述命令與證據；通過後派問答、資料不足說明與申請準備清單。Frank：不需例行行動；無帳號操作缺口。
