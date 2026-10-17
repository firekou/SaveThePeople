# D1 環境與啟動條件核對回覆（D1_READINESS）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-D1-READINESS｜stage：D1_READINESS｜一次交付
工單：issuecomment-6112098995 + GPT_D1_READINESS_PACKET_20261012.md｜claim：issuecomment-6112104744（session_01MvUGYirGBtHVdHk3mYxAkh）
source：ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9（為 handoff 的 ancestor）｜handoff/起點：bf8c5ed4a0cc592c239a92006264523e8754e3c6｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
診斷時間：2026-10-11T18:12Z（本 session 時鐘）。層級：環境能力診斷（AUTHOR_EVIDENCE）；**不是產品、不是 HTTP／DB 驗證**。未安裝任何東西、未啟動任何服務、未讀環境變數或 Secret、未連外。

## 1. 存取與唯一性
- GitHub 存取：`git fetch origin refs/pull/1/head` 成功；`ls-remote` 見 PR #1 head = bf8c5ed…，main = 9a7bd12…。
- 唯一 claim：PR #1 無其他 D1_READINESS claim 或結果分支。分支 `claude/tender-allen-c9p5u1`（平台指定）ff 至 bf8c5ed，non-force。
- 其他遠端分支 `claude/relaxed-maxwell-q2b86k` 內容未讀（UNKNOWN，非本工單範圍）。

## 2. 工具能力診斷（實際 command／exit／輸出）
| 命令 | exit | 輸出 |
|---|---:|---|
| `python3 --version` | 0 | Python 3.11.17 |
| `docker --version` | 0 | Docker version 29.8.2, build 7fc2dff |
| `docker compose version` | 0 | Docker Compose version v5.6.0 |
| `psql --version` | 0 | psql (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) |
| `docker info --format '{{.ServerVersion}}'` | 1 | failed to connect to the docker API at unix:///var/run/docker.sock; … no such file or directory |
| `python3 -I -c "import django"` | 1 | ModuleNotFoundError: No module named 'django' |
| `python3 -I -c "import psycopg"`／`psycopg2` | 1 | ModuleNotFoundError（兩者皆無） |
| `python3 -m pip --version` | 0 | pip 24.0（僅確認存在；**未**執行任何安裝／下載） |
| 其他 | 0 | git 2.43.0、GNU Make 4.3、Python sqlite3 3.45.1 |
- 另（唯讀）`/usr/lib/postgresql/*/bin` 內有 `postgres`、`initdb`、`pg_ctl`、`pg_isready` 等伺服器端執行檔（未執行、未啟動）；`/usr/bin/dockerd` 存在但 daemon 不在執行（以 `docker info` 為準）。目前身分 uid 0。
- 結論：**Docker CLI／Compose 已安裝但 daemon 不可連線 → 不能憑 CLI 宣稱 `docker compose up` 可行（NOT_AVAILABLE，實測失敗）**。**Django 與 PostgreSQL 驅動（psycopg）未安裝 → NOT_AVAILABLE**。`psql` 客戶端與 PostgreSQL 16 伺服器執行檔存在，**但本診斷未啟動伺服器，故「可啟動」是 UNKNOWN**。

## 3. 六個開工條件（BATCH1_EXECUTION_PACK §1）逐項
| # | 條件 | 狀態 | 證據與缺口 |
|---|---|---|---|
| 1 | 本輪規劃經獨立覆核 APPROVED | **部分滿足** | GPT 對 N 修補 A/B 差異出具 APPROVED（R2_REPAIR 02935f5；round3 ebfad3d：issuecomment-6112098995），皆限定範圍；**非全產品 APPROVED**。PR #1 仍 Draft、main 未動。 |
| 2 | 工程人力（D-307） | **UNKNOWN／NOT_AUTHORIZED（需負責人決定）** | SYNTHETIC_WEBSITE_START_DECISION 限定 Claude 執行、GPT 覆核，不等於真人工程到任，不視為全 MVP 人力已配置。 |
| 3 | 技術堆疊（D-201 Django＋PostgreSQL＋HTMX） | **推薦且可逆；實際環境未備** | Django、psycopg 未安裝；PostgreSQL 客戶端與伺服器執行檔存在但未驗證可啟動。 |
| 4 | 開發環境（本機 Docker Compose） | **未滿足（實測）** | docker daemon 不可連線（exit 1）。見 §5 替代路徑。 |
| 5 | 合成資料規範 | **滿足（檔案層級）** | `synthetic_resources.json`：頂層 `is_synthetic: true`；6 項資源、6 來源、2 口徑、3 地區。資源個別**沒有** `is_synthetic` 欄位（只在頂層）——匯入器需在列層標示，列為 D1 實作注意事項。狀態：RESOURCE 1～4 PUBLISHED 且 `effective_unknown=false`；FOOD-005 `PUBLISHED` 且 `effective_unknown=true`（生效期間未知，依規格為 MANUAL_CHECK_ONLY，公開列表是否顯示需依引擎 §0.1 `catalog_visibility`，不可為湊數量全標 PUBLISHED）；RENT-006 `EXPIRED`（`effective_to=2026-06-30`，不在列表）。 |
| 6 | repo 存取與分支規則 | **部分滿足／UNKNOWN** | repo 無 `.github/`（無 PR 範本、無 CI）、無 AGENTS.md／CLAUDE.md；README 無分支規範。實際可行：平台指定功能分支＋Draft PR＋GPT 非作者覆核（決策包建議）；「直接寫 main」不允許。具體分支命名／保護規則：UNKNOWN／NOT_AUTHORIZED（需負責人或 GPT 在工單中指定）。 |

另：「明確的產品開工批准」（SYNTHETIC_WEBSITE_START_DECISION 的唯一人工決策）— **NOT_AUTHORIZED**（文件記為 PREPARED／NOT_AUTHORIZED_TO_START；本工單明文不授權產品實作）。

## 4. D1 最小實作建議（建議，不實作）
**可見成果**：本機啟動後 P1 目錄列表＋詳情，6 項合成資源（5 項依可見性規範列示／標示，RENT-006 不在列表），每項顯示「合成，非真實」標示、來源、適用地區、查核日期、有效狀態；篩選；360px 可用、鍵盤可操作、空列表與錯誤可理解、無水平捲動、首屏 ≤300KB。
**建議下一包（D1-A，待 GPT 核發）**：
- scope：WP-01～03 的最小可跑子集：Django 骨架、`catalog` 模型（Organization、Source、Resource、ResourceVersion）、`import_synthetic_catalog`、`GET /api/public/resources`、P1 列表／詳情頁（HTMX 篩選）、遷移與目錄測試（T-04、T-21）。
- 時間：BATCH1 估 D1 17～25 人日（規劃估算，非 Agent 工時）；此最小子集 GPT 另定有界時間；外部成本 0。
- 命令（建議，須待環境備妥）：`python3 -m venv`＋依賴安裝（**需工單明文允許**）→ `python3 manage.py migrate` → `python3 manage.py import_synthetic_catalog` → `python3 manage.py test` → `make spec-check`（跑 `check_examples.py` 等）。
- 負向控制：RENT-006（EXPIRED）不得出現在公開列表；FOOD-005 不得被顯示為已確認有效；匯入非 `is_synthetic` 資料被拒；列表只含 PUBLISHED／NEEDS_RECHECK；故意改壞 `synthetic_resources.json` 一個狀態，測試須失敗。
- 證據（與文件工具結果分開）：實際啟動輸出、遷移輸出、HTTP 回應（curl 本機）、DB 查詢結果、360px 截圖（Chromium 已預裝可用 Playwright 擷取；**尚未診斷，列為待確認**）。

## 5. 失敗歸因與不受阻工作／最小恢復
- **受阻**：Docker daemon 不可連線（環境）；Django／psycopg 未安裝（依賴，本工單禁止安裝）；工程人力 D-307 與明確產品開工批准（未決條件）。
- **不受阻（無需新依賴）**：①把 D1 驗收腳本與 fixtures 準備為純標準函式庫（例如依 `synthetic_resources.json` 計算預期列表／可見性的參考檢查，與既有 `check_examples.py` 同層級）；②撰寫 README 啟動步驟草稿（標「未驗證」）；③準備 CI 設定草稿但不放入 `.github/`（scope 外）。
- **最小恢復操作（擇一，由 GPT 決定；需新權限者才交帳號持有人）**：
  - (a) 工單明文允許在隔離虛擬環境以 pip 安裝 Django 與 psycopg（需套件來源可達，目前 UNKNOWN，本診斷未連外）；DB 以本機隔離 PostgreSQL 16（`initdb`＋`pg_ctl`，僅限 /tmp 資料夾、loopback、無外部連線）取代 Docker Compose。這屬於「既存隔離 runtime 替代」，不改 PostgreSQL→SQLite，且在實際執行前不宣稱 DB 已驗證。
  - (b) 由帳號持有人讓 Docker daemon 可用（平台層設定，Claude 無法自行完成）。
  - 不採用：SQLite 替代 PostgreSQL（會讓 jsonb、partial unique index 等驗收失去意義）。
- 這些阻擋都不涉及新費用、真實資料或 Secret；不需 Frank 重新規劃。

## 6. 邊界聲明
外部呼叫：無；支出：0；真實資料：無；Secret：未讀；部署／通知／merge：無；安裝／啟動服務：無；PR 維持 Draft；四份基線未改。AUTHOR_EVIDENCE，不自批、不宣稱 D1 已開工或有網站。
