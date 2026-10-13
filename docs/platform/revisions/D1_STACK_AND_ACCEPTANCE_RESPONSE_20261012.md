# D1 技術版本與最小驗收具體化回覆（D1_STACK_AND_ACCEPTANCE）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-D1-STACK-AND-ACCEPTANCE｜stage：D1_STACK_AND_ACCEPTANCE｜一次交付（repair_round_limit 0）
工單：issuecomment-6114886063 + GPT_D1_STACK_AND_ACCEPTANCE_PACKET_20261012.md｜claim：issuecomment-6114891440（session_01MvUGYirGBtHVdHk3mYxAkh）
source：09e19a2f800455685489a42b3c5e17303b115375｜handoff：ff588059249f84c94fbbba43884a9974bfd36348（source 為其 ancestor）｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
時間（本 session 時鐘，2026-10-11 UTC）：開始 23:03Z，外部查核 23:03～23:05Z。層級：作者初查（AUTHOR_EVIDENCE；**不是 V2、不是 VERIFIED、不是可正式推薦**）。查核人＝Claude（作者層級）。未安裝、未下載任何套件，未啟動 DB／HTTP，未寫產品檔。

## 1. 官方來源查核（上限 8 個；實際發出 7 個請求）
外部操作僅限工單授權的公開唯讀技術來源。平台出口政策對部分主機回 403（`connect_rejected`，原因已由 `__agentproxy/status` 的 recentRelayFailures 佐證），**依平台規則不重試、不繞過**。
| # | URL | 查核 UTC | 結果 |
|---|---|---|---|
| 1 | https://www.djangoproject.com/download/ | 2026-10-11T23:03:44Z | **拒絕（CONNECT 403，政策）** — 無內容 |
| 2 | https://docs.djangoproject.com/en/5.2/faq/install/ | 23:04:05Z | **拒絕（403）** — 無內容 |
| 3 | https://pypi.org/pypi/Django/json | 23:04:06Z | 200，625,924 bytes（公開 metadata） |
| 4 | https://www.postgresql.org/support/versioning/ | 23:04:06Z | **拒絕（403）** — 無內容 |
| 5 | https://www.psycopg.org/psycopg3/docs/basic/install.html | 23:04:06Z | **拒絕（403）** — 無內容 |
| 6 | https://pypi.org/pypi/psycopg/json | 23:04:19Z | 200，101,187 bytes |
| 7 | https://pypi.org/pypi/Django/5.2.18/json | 23:04:58Z | 200，6,012 bytes |
還有 1 次額度未用（不用於重試被拒主機）。**被拒的 4 個主機（djangoproject.com、docs.djangoproject.com、postgresql.org、psycopg.org）需要有權限的人或另一條合法通道才能取得；這是「LTS 官方標示」與「PostgreSQL／Python 支援期間」無法官方確認的原因。**

### 1.1 取得的事實（PyPI 公開 metadata；原文要點）
- Django 最新：**6.1.2**，`requires_python >=3.12`，classifiers 為 Python 3.12／3.13／3.14。
- 各系列最新 patch（來自 releases 的檔案資訊；`yanked=False`）：
  | 系列 | 首版上傳 | 最新 patch／上傳日 | requires_python |
  |---|---|---|---|
  | 4.2 | 2023-04-03 | 4.2.30／2026-04-07 | >=3.8 |
  | 5.0 | 2023-12-04 | 5.0.14／2025-04-02 | >=3.10 |
  | 5.1 | 2024-08-07 | 5.1.15／2025-12-02 | >=3.10 |
  | **5.2** | 2025-04-02 | **5.2.18／2026-10-06** | **>=3.10** |
  | 6.0 | 2025-12-03 | 6.0.9／2026-10-06 | >=3.12 |
  | 6.1 | 2026-08-05 | 6.1.2／2026-10-06 | >=3.12 |
  （推論，非官方標示：2026-10-06 仍有 patch 的系列為 5.2、6.0、6.1；4.2 最後 patch 在 2026-04-07，與其已停止維護一致；**metadata 不含任何「LTS」欄位或支援截止日**。）
- Django 5.2.18 metadata：`requires_python >=3.10`；`requires_dist`：asgiref>=3.8.1、sqlparse>=0.3.1（tzdata 僅 win32）；classifiers Python 3.10～3.14。wheel `django-5.2.18-py3-none-any.whl`（bdist_wheel，8,316,071 bytes，sha256 `92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c`，上傳 2026-10-06，yanked False）；sdist sha256 `461c5dd06d2ea16bd5ca37d3f46e4def1d6b0fe7588c6f4e2119517bb0af8b2d`。以上 hash 為 PyPI 公開 metadata，**尚未下載驗證實檔**。
- psycopg 最新：**3.3.6**，`requires_python >=3.10`，上傳 2026-09-18（與現有 venv 的 3.3.6 相同）。

### 1.2 UNKNOWN（官方來源取不到，不編造）
| 項目 | 狀態 | 缺口 |
|---|---|---|
| 哪個 Django 系列是 LTS、各系列支援截止日 | **UNKNOWN（官方頁被拒）** | 作者先前知識認為「x.2 系列為 LTS，5.2 為 2025-04 起的 LTS」，且 5.2 首版 2025-04-02 與此一致，但**這是作者背景知識＋慣例推論，不是本次查核到的官方標示，標 UNVERIFIED**；請 GPT 以其他合法通道確認。 |
| Django 5.2 要求的 PostgreSQL 最低版本 | **UNKNOWN** | docs 被拒；作者背景知識為 14 以上，UNVERIFIED。現有 PG 為 16.15（高於該背景值）。 |
| PostgreSQL 16 的社群支援截止日 | **UNKNOWN** | postgresql.org 被拒。 |
| psycopg 3.3.x 支援的 PostgreSQL 最低版本 | **UNKNOWN** | psycopg.org 被拒。 |
| HTMX 版本與供應方式 | **UNKNOWN（未查核；不在授權來源內）** | 見 §4：建議 D1-A 不使用 HTMX。 |

### 1.3 選型建議（一個明確選型，附條件）
**建議：D1-A 以 Django 5.2 系列（目前最新 patch 5.2.18）為目標，配 psycopg 3.3.6 與 PostgreSQL 16。** 條件與理由：
- 相容性（已由 PyPI metadata 確認）：5.2.18 支援 Python 3.10～3.14，現有 venv 為 Python 3.13.16 ✔；asgiref 3.12.1（需 >=3.8.1）✔、sqlparse 0.6.0（需 >=0.3.1）✔；psycopg 3.3.6（Python >=3.10）✔。PostgreSQL 16.15 與 Django 5.2／psycopg 3.3 的相容性官方確認＝UNKNOWN（見 §1.2），但 Django 6.1.2＋psycopg 3.3.6＋PG 16.15 的實際煙霧已通過（D1_ENVIRONMENT，AUTHOR_EVIDENCE）。
- 與現有 venv 的差異：現有 Django 6.1.2（**非 LTS 依 x.2 慣例；官方確認＝UNKNOWN**，6.1 首版 2026-08-05）。切換到 5.2.18 需要**下載 1 個套件**（`django-5.2.18-py3-none-any.whl`，8.3 MB，PyPI，成本 0）並重跑環境 `verify`（`orchestrate_v3.sh verify`；其 PINS 與 `wheelhouse.sha256` 需更新，屬下一包 scope）。其他 4 個套件不變。
- 若 GPT／負責人不批准該下載或無法確認 LTS：**備選＝維持 6.1.2（無需下載）**，但這是非 LTS 系列，需把「於 6.2 LTS 釋出時遷移」列為風險（6.2 是否存在／何時釋出＝UNKNOWN）。**這是給 GPT 的唯一剩餘技術決策（見 §5）。**
- 供應鏈 hash：只有 PyPI metadata 的 sha256，沒有下載實檔核對；不得當成已驗證。

## 2. 六個開工 gate（BATCH1_EXECUTION_PACK §1）
標記：VERIFIED（Reviewer 或可重跑機制已驗）／AUTHOR_EVIDENCE（作者證據）／UNKNOWN／NOT_AUTHORIZED。
| # | 條件 | 狀態 | 證據位置與差異 |
|---|---|---|---|
| 1 | 規劃獨立覆核 | **部分 VERIFIED（限定範圍）** | GPT 的 APPROVED 範圍：R2 修補 A/B（issuecomment-5994261021）、N-03 round3（6112098995 → GPT_N03_ROUND3_REVIEW）、D1_READINESS（6112643046）、D1_ENVIRONMENT repair3（6114886063）。皆**限定差異**，非全產品；PR #1 仍 Draft。 |
| 2 | 工程人力 D-307 | **NOT_AUTHORIZED／UNKNOWN（需負責人決定）** | SYNTHETIC_WEBSITE_START_DECISION 限定「Claude 執行、GPT 覆核」；無真人工程到任、無預算承諾。 |
| 3 | 技術堆疊（D-201） | **推薦且可逆；AUTHOR_EVIDENCE** | 見 §1.3；官方 LTS／PG 支援 UNKNOWN。 |
| 4 | 開發環境 | **AUTHOR_EVIDENCE（替代 runtime）／Docker 未驗證** | 隔離 PG16（私人 socket）＋Django 6.1.2＋psycopg 3.3.6 煙霧與清理（D1_ENVIRONMENT repair3，GPT 覆核為「控制流程差異 APPROVED」；DB runtime 本身仍為作者證據，Reviewer NOT_RUN）。Docker daemon 不可用。venv 在 /tmp，重啟即失。 |
| 5 | 合成資料規範 | **VERIFIED（檔案層級，可重跑）＋差異** | `fixture_expect.py` 輸出見 §3：頂層 `is_synthetic=true`；**6 筆資源列層沒有 `is_synthetic` 欄位**（匯入器需在列層標示，是 D1-A 的實作要求）。 |
| 6 | repo 存取與分支規則 | **部分／UNKNOWN** | 無 `.github/`、無 AGENTS.md／CLAUDE.md；實務規則＝平台指定功能分支＋Draft PR＋GPT 非作者覆核，不寫 main。分支命名保護規則 UNKNOWN。 |
| — | 明確產品開工批准 | **NOT_AUTHORIZED** | SYNTHETIC_WEBSITE_START_DECISION 的唯一人工決策；本包不授權。PREPARED 工單（§4）不因本報告生效。 |

## 3. Fixture 預期（既有參考引擎核對；不重搜真實資源）
`fixture_expect.py`（純標準函式庫；呼叫 `docs/platform/examples/ref_engine.py` 的 `recommendation_status`，`catalog_visibility` 依 RESOURCE_AND_ELIGIBILITY_ENGINE §0.1 的狀態對照）：
```python
"""D1 fixture 預期核對（純標準函式庫；使用既有參考引擎 ref_engine，不重搜真實資源、不改 repo 工具）。
catalog_visibility 依 RESOURCE_AND_ELIGIBILITY_ENGINE §0.1；recommendation_status 呼叫 ref_engine。"""
import json, sys
sys.path.insert(0, "docs/platform/examples")
import ref_engine as E

VIS = {"PUBLISHED": "LIST", "NEEDS_RECHECK": "LIST+RECHECK_BADGE", "SUSPENDED": "UNLISTED(direct-link)", "EXPIRED": "UNLISTED(history)",
       "SUPERSEDED": "UNLISTED(history)", "RETIRED": "UNLISTED(history)", "CANDIDATE": "INTERNAL", "DRAFT": "INTERNAL", "IN_REVIEW": "INTERNAL"}
d = json.load(open("docs/platform/examples/synthetic_resources.json", encoding="utf-8"))
srcs = {s["id"]: s for s in d["sources"]}
scopes = {x["scope_key"]: x for x in d["household_scopes"]}
AS_OF = sys.argv[1] if len(sys.argv) > 1 else "2026-10-12"
print("as_of", AS_OF, "| top-level is_synthetic:", d["is_synthetic"], "| per-row is_synthetic present:", [("is_synthetic" in r) for r in d["resources"]])
for r in d["resources"]:
    v = r["version"]
    rs = E.recommendation_status(r, srcs, AS_OF, scopes)
    print(f'{r["resource_key"]:20s} version.status={v["status"]:10s} catalog={VIS[v["status"]]:20s} effective_unknown={v["effective_unknown"]!s:5s} recommendation={rs["status"]:18s} reasons={rs["reasons"]}')
```
輸出（`python3 /tmp/stp-d1-stack/fixture_expect.py 2026-10-12`，exit 0）：
```
as_of 2026-10-12 | top-level is_synthetic: True | per-row is_synthetic present: [False, False, False, False, False, False]
TW-DEMO-LIVING-001   version.status=PUBLISHED  catalog=LIST                 effective_unknown=False recommendation=FORMAL             reasons=[]
TW-DEMO-EMERG-002    version.status=PUBLISHED  catalog=LIST                 effective_unknown=False recommendation=FORMAL             reasons=[]
TW-DEMO-EDU-003      version.status=PUBLISHED  catalog=LIST                 effective_unknown=False recommendation=FORMAL             reasons=[]
TW-DEMO-CHILD-004    version.status=PUBLISHED  catalog=LIST                 effective_unknown=False recommendation=FORMAL             reasons=[]
TW-DEMO-FOOD-005     version.status=PUBLISHED  catalog=LIST                 effective_unknown=True  recommendation=MANUAL_CHECK_ONLY  reasons=['PERIOD_UNKNOWN']
TW-DEMO-RENT-006     version.status=EXPIRED    catalog=UNLISTED(history)    effective_unknown=False recommendation=NOT_RECOMMENDED    reasons=['STATUS_EXPIRED', 'PERIOD_ENDED', 'WINDOW_CLOSED']
```
解讀（D1 的預期值）：公開列表 **5 項**（LIVING-001、EMERG-002、EDU-003、CHILD-004、FOOD-005）；RENT-006（EXPIRED）**不在列表**（只在歷史頁，標「已過期」）；FOOD-005 因 `effective_unknown=true` 是 `MANUAL_CHECK_ONLY / PERIOD_UNKNOWN`，**公開 P1 可列出但必須標「生效期間未知，需先人工確認」，不得顯示為已確認有效**；不為湊數量把 6 項全標 PUBLISHED。

## 4. D1-A 最小實作候選工單（PREPARED，**未生效**，需 GPT 核發）
- task_id（建議）：STP-PLATFORM-PLAN-001-D1-A-CATALOG；stage D1_A；executor Claude；reviewer GPT；status **PREPARED／NOT_AUTHORIZED_TO_START**。
- source／base：待 GPT 核發時填入本回覆的 result SHA 之後的 candidate；base/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012（main 不動，不 merge）。
- 分支／PR：平台指定結果分支（目前 claude/tender-allen-c9p5u1），PR #1 Draft 協調；non-force；不推 main。
- 目標（WP-00～03 的最小子集）：本機合成目錄的 P1 列表＋詳情＋篩選，6 筆合成 fixture；**不含 D2～D4、不含 HTMX（建議 D1-A 以純伺服器渲染＋GET 查詢參數篩選，無前端依賴、無額外下載）**。
- scope_paths（建議）：新增 `product/`（Django 專案與 `catalog` app、測試、README 啟動命令）、`docs/platform/revisions/D1_A_RESPONSE_*.md`；excluded：四份基線、docs/platform 既有規格／工具／作者與 GPT 歷史、`.github/`、部署檔、依賴 lock（鎖定另案）、真實資料、Secret。
- 依賴與版本：Python 3.13（既有）；Django==5.2.18（**需 1 個套件下載授權**：PyPI `django-5.2.18-py3-none-any.whl`，8.3 MB，sha256 以 §1.1 為對照，成本 0）；psycopg[binary]==3.3.6、asgiref==3.12.1、sqlparse==0.6.0（既有）；PostgreSQL 16 私人 socket（沿用 orchestrate_v3）。備選：維持 Django 6.1.2（無下載）。
- 有界資源（建議，GPT 可調整）：單一交付，上限 120 分鐘（模型：骨架與 catalog 模型 30、匯入與可見性規則 30、列表／詳情／篩選頁與 360px 20、測試與驗收證據 30、文件 10）、外部成本 0；實際 UTC 期限由 GPT 核發時填入。
- 擬交付（產品證據，與文件工具結果分開）：乾淨 checkout 的啟動命令、遷移與匯入輸出、HTTP 回應（curl，本機 loopback、私人環境）、DB 查詢結果、360px 截圖（預裝 Chromium 可用，**能力尚未診斷，列為待確認**）。
- 停止條件：新費用／Secret／真實資料／雲端／公開部署；範圍改變；LTS／下載授權不成立；環境 verify 失敗；競爭 claim；超時。
- nextActor：交付後 GPT 獨立覆核；不自行 merge，不進 D2。

## 5. 產品 HTTP／DB 最小驗收命令與預期（**全部 NOT_RUN**；尚無 HTTP／DB 實作，不宣稱成果）
前置：`orchestrate_v3.sh verify` exit 0；PG16 私人 socket 啟動（比照 orchestrate_v3）；環境不使用任何 Secret。以下命令名稱為建議，實際以 D1-A 專案為準。
| # | 命令（建議） | 預期 | 負向控制 |
|---|---|---|---|
| A1 | 乾淨 checkout 後 `python manage.py migrate` | exit 0；建立 catalog 表 | 少一個遷移或欄位型別錯誤時 `migrate --check` 非 0 |
| A2 | `python manage.py import_synthetic_catalog` | exit 0；6 資源、6 來源、2 口徑；`is_synthetic=true` 寫在每個資源列 | 匯入含 `is_synthetic=false` 的資料→非 0、資料庫無新增 |
| A3 | `python manage.py test` | 全過；含 T-04（只列 PUBLISHED／NEEDS_RECHECK）、T-21（未生效標示） | 把 RENT-006 改成 PUBLISHED 時測試必須失敗（人為破壞須被抓到） |
| A4 | `make spec-check`（呼叫 check_examples.py 等） | exit 0 | 改壞 synthetic_resources.json 一個狀態→失敗 |
| B1 | `curl -s http://127.0.0.1:<port>/api/public/resources` | JSON 5 筆；不含 RENT-006；每筆含來源、最後查核日期、適用地區、版本狀態、合成標示 | 以 `?status=EXPIRED` 之類參數不得讓 RENT-006 進入公開列表 |
| B2 | `curl -s …/resources/TW-DEMO-FOOD-005` | HTML／JSON 顯示「生效期間未知，需先人工確認」，**不是**「有效」 | 任何顯示 FOOD-005 為已確認有效即失敗 |
| B3 | `curl -s …/resources/TW-DEMO-RENT-006`（直接連結） | 顯示「已過期」歷史頁，不在列表 | 列表 HTML 含 RENT-006 即失敗 |
| B4 | 篩選：地區參數存在／不存在 | 命中時列出對應資源；不存在的地區回空態（可理解訊息，非錯誤頁） | 空態回 500 即失敗 |
| C1 | 360px 視窗截圖＋鍵盤 Tab 走訪 | 無水平捲動；焦點順序合理；首屏 ≤300KB | 水平捲動或 Tab 陷阱即失敗 |
| C2 | 「合成，非真實個案／示範縣」標示 | 列表與詳情皆可見 | 缺標示即失敗 |
| D | 啟動後停止 DB 再請求 | 回可理解的錯誤，不洩漏堆疊／連線字串 | 顯示 traceback 即失敗 |
所有資料均為 `is_synthetic=true`，不連外部服務、不處理真實個案、不提交任何申請。

## 6. repo 必要檢查（於追加本檔前的樹；皆 exit 0，stderr 空）
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2098 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` 為空；本 commit 只新增本檔。

## 7. 給 GPT 的唯一剩餘技術決策與建議
**問題**：D1-A 要採 Django 5.2.18（LTS 慣例，需授權 1 個 8.3 MB 套件下載，成本 0），還是維持 6.1.2（無需下載，但非 LTS）？
**建議**：採 5.2.18——前提是 GPT 以另一條合法通道確認「5.2 為 LTS」與「PostgreSQL 16／Django 5.2 相容」；若無法確認，退而維持 6.1.2 並把遷移風險寫進工單。HTMX 不納入 D1-A。不需要 Frank 搬運或例行放行。

## 8. 未證明與邊界
- 未證明：Django LTS 官方標示與支援期間、PostgreSQL／psycopg 的官方相容與支援期間（4 個官方主機被政策拒絕）；套件實檔 hash；任何產品 HTTP／DB／360px；Docker。
- 外部呼叫：7 個公開唯讀請求（3 成功、4 被政策拒絕且未重試或繞過）；支出 0；真實資料無；Secret 未讀；安裝／下載套件無；部署／通知／merge 無；PR 維持 Draft；PREPARED 工單不因本報告生效。AUTHOR_EVIDENCE，不自批。
