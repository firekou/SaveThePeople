# R2 修正回覆（GPT 對 R1 的獨立覆核 F-01～F-08）
work_id：STP-PLATFORM-PLAN-001｜修正版本：v0.4-draft（R2 修正）｜2026-10-04｜狀態：READY_FOR_REVIEW（待 GPT 以 exact head 獨立覆核；作者不宣告通過）

| 項目 | 值 |
|---|---|
| Repo／PR／分支 | firekou/SaveThePeople／PR #1（Draft，維持 Draft）／`claude/stp-platform-plan-001` |
| base（origin/main） | `9a7bd1295e20837786acc45bdab7fb94f5a1b012`（開工時核對相符） |
| 本輪起點 head | `45e7034114a7ae27f8e9743033d901b8466dc199`（R1 交付，開工時核對相符） |
| 結果 head | 見 PR #1 的最新提交（本檔隨該提交推送；交付回報列出 exact SHA） |

## 0. 範圍、誠實聲明與前輪紀錄
- 本輪只修正平台規劃、合成範例、參考實作與檢查工具。**沒有開始網站開發、沒有部署、沒有使用真實個案、沒有 merge，也不宣告 APPROVED。**
- 四份原始基線文件未修改（`git diff origin/main -- <四檔>` 為空，見 §4）。D-311、D-312 仍是**未啟用**的放寬提案；外部 AI 文件處理（D-313）仍未啟用，人工登錄仍是預設。
- `revisions/R1_RESPONSE.md` 保留為歷史紀錄，**未改寫其結論**。它的下列說法在本輪被證明過寬，在此更正（不是刪除）：
  - R1 §4 表「權限：矩陣不變條件由程式檢查…… 通過」——當時的檢查只對 PRD 矩陣表格列做**字串前綴**比對與 API 權限欄的角色代碼是否為 R1～R9，從未比對頁面權限、API 授權與矩陣是否一致。因此「通過」只代表「矩陣表格列的前綴符合預期」，**不是**「權限一致性通過」。F-03 的兩個矛盾（P11 讓 R5 看到個案轉介清單；驗證 API 允許「另一位 R3」但矩陣只給 R3 ASG）就是它抓不到的。
  - R1 對 `recommendation_status`、口徑、申請唯一性的「參考檢查涵蓋」：涵蓋的是**正向範例與少數反例**，不是「任一位置的非法條件」「未知口徑鍵」「SUPPLEMENTARY 的完整生命週期」。
- 驗證層級（本輪所有「通過」只指所列層級，詳見 BUILD_PLAN §4.2）：**文件政策檢查**（check_docs、gen_permissions、gen_state_machines、test_checks）、**純邏輯參考模擬**（ref_engine、ref_control 與案例）。**沒有**資料庫整合測試、備份整合演練、真實授權行為測試或產品驗收。

## 1. R1 自我檢查沒有覆蓋的反例（GPT 覆核才發現）
| 未覆蓋的反例 | R1 檢查為何沒抓到 | R2 補上的回歸檢查 |
|---|---|---|
| 規則第一個條件合法、之後的條件或 CUSTOM 運算式非法 | `recommendation_status` 以空口徑表驗證並吞掉「未知口徑」例外，之後的結構未驗；R1 的反例只放在第一個條件 | `test_rule_validation_order_independence`（非法條件置於每個位置結論相同）、`illegal_criterion_variants`、`illegal_expression_variants` |
| 缺 `rule.status` | 預設值被當成 PUBLISHED；R1 沒有「欄位被移除」案例 | `recommendation_cases` 的 `RULE_STATUS_MISSING`、未發布案例 |
| 口徑含未支援或未知鍵 | runner 只讀自己認得的鍵，其餘忽略；R1 沒有任何「多出一個鍵」案例 | `scope_cases`（26）、`criterion_shape_cases`（42）、H1 的 F-02 回歸 |
| P11 混合容量資料與個案轉介清單、驗證 API 授權超出矩陣 | R1 權限檢查只看矩陣表格列前綴，頁面與 API 授權從未與矩陣比對 | `permissions.json` 單一來源＋`policy_problems`＋`tools/test_checks.py` 的 21 項權限反例 |
| 備份後才發生的用途撤回、匯出前主庫失效 | R1 只有刪除帳本的文字描述，沒有可執行模擬 | `ref_control.py`＋`control_cases.json`（12 情境） |
| P2 草稿儲存與副本清冊、冪等回應內容不一致 | R1 的清冊檢查只確認 ID 有定義，不看內容是否互相矛盾 | `replay_cases`（5）、T-55、T-56、CP-12／CP-25 重寫 |
| SUPPLEMENTARY 的 create→prepare→READY_TO_SUBMIT | R1 的申請案例只涵蓋建立，不涵蓋送件前檢查 | `application_ready_cases`（17）、`application_lifecycle_cases`（2）、`legacy_ap06_blocks`（證明 R1 規則會擋掉合法補件） |
| 必要欄位缺漏（`effective_unknown`、`expression`、複查起算資料） | R1 欄位路徑檢查只確認文件中出現的 `Entity.field` 存在於資料模型，沒有檢查必要欄位與結構 | `schemas/*.schema.json`＋`schema_lite.py`＋反例；複查與一致性案例 |
| 決策與章節引用錯位（PR-07→D-309、D-106→引擎 §6.4） | R1 的引用檢查只確認 ID 存在 | `tools/citation_check.py`（引用語境）與反例 |

## 2. F-01～F-08 對照
格式：問題／修正位置／驗證方法／實際結果／剩餘缺口。檔名省略 `docs/platform/`。

### F-01 `recommendation_status` 驗證不完整，缺 `status` 預設為已發布　**狀態：完成（文件與純邏輯模擬層級）**
- **問題**：舊版以空口徑表驗證並吞掉未知口徑例外，後續非法條件與 CUSTOM 運算式沒被檢查；缺 `rule.status` 預設為 PUBLISHED。GPT 的三個重現（後面的條件違規、CUSTOM NOT、移除 `rule.status`）在 R1 head 都仍為 FORMAL。
- **修正**：
  - `examples/ref_engine.py`：驗證分為完整結構驗證（`rule_problems` 收集全部問題，順序無關）與範圍參照驗證（`validate_rule(rule, scopes)` 必須給完整口徑表，缺少即 `TypeError`）；`recommendation_status(res, sources, as_of, scopes)` 對驗證未完成或例外一律 `RULE_INVALID`；缺 `status`→`RULE_STATUS_MISSING`；非 PUBLISHED→`RULE_NOT_PUBLISHED`；無規則→`RULE_MISSING`。
  - `RESOURCE_AND_ELIGIBILITY_ENGINE.md` §0.2 第 1 項、§5.1、§5.4（兩階段流程）、§5.5（CUSTOM 運算式）；`DATA_MODEL_AND_STATE_MACHINES.md` §2.5（`status` 必填、無預設值）。
  - `examples/engine_cases.json`：`recommendation_cases`（59）、`illegal_criterion_variants`（8）、`illegal_expression_variants`（4）、含一個合法有口徑的正例（仍 FORMAL）。
- **驗證方法**：先在 R1 head 重現，再在修正後重跑；`check_examples.py` 的 `test_rule_validation_order_independence` 把非法條件放在每個位置；人為破壞。
- **實際結果**（同一支重現腳本）：
  - R1 head `45e7034`：後面條件違規→`FORMAL`；CUSTOM NOT→`FORMAL`；移除 `rule.status`→`FORMAL`。
  - R2 工作樹：`NOT_RECOMMENDED／RULE_INVALID`；`NOT_RECOMMENDED／RULE_INVALID`；`NOT_RECOMMENDED／RULE_STATUS_MISSING`；`status=DRAFT`→`RULE_NOT_PUBLISHED`。
  - 人為破壞：缺 `status` 預設回 PUBLISHED→2 項失敗；吞掉未知口徑例外→28 項失敗；（均被抓到，見 §5）。
- **剩餘缺口**：產品尚未實作（WP-04）；驗證器是參考實作，不是 JSON Schema 的完整等價。

### F-02 未支援或未知的口徑鍵被默默忽略　**狀態：完成（文件與純邏輯模擬層級）**
- **問題**：`SCOPE-CO` 加上 `age_between=[0,17]` 時，runner 仍把 35 歲與 66 歲成員計入。
- **修正**：`ref_engine.py` 的 `scope_problems`、`where_problems`、`criterion_problems`：支援清單之外的鍵（含已知但未實作的 `age_between`、`in_school`、`military_service`、`exclusions`、年度所得期間、推估所得）一律報錯；`COUNT_MEMBERS_WHERE` 的 `where` 與 `min_count` 受控驗證；`scope_members` 先 `validate_scope`。`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §5.2、§5.3 增列支援／未支援表；`DATA_MODEL_AND_STATE_MACHINES.md` §2.6；`examples/README.md`。
- **驗證方法與結果**：`scope_cases`（26）、`criterion_shape_cases`（42）含未知鍵、未支援 `age_between`、型別錯誤、合法口徑；`test_unknown_member_not_dropped` 與 H5 保留「成員資料未知不得被排除」。重現腳本：R1 head 計入 `['H1-P1','H1-P2','H1-P3','H1-P4']`；R2 工作樹拋出 `UnsupportedError: SCOPE-CO: member_inclusion.age_between is not supported by this runner`；未知鍵拋出 `ValidationError`。人為破壞（未支援鍵再次被忽略）→33 項失敗。
- **剩餘缺口**：年齡、就學、服役與工作能力推估所得**尚未實作**，只是被明確拒絕；使用它們的規則目前不可推薦，正式實作要補（WP-04）。

### F-03 矩陣、頁面、API 權限不一致　**狀態：完成（文件政策檢查層級；產品授權行為測試未做）**
- **問題**：P11 同頁混合容量資料與個案轉介清單，R5 因此看得到轉介；驗證 API 允許「另一位 R3」，矩陣卻只給 R3 ASG；另外 R1 的矩陣與狀態機也有不一致（RV 的 R4、R7 在資源內部資料沒有編輯權）。
- **修正**：
  - 新增單一事實來源 `permissions.json`（角色、範圍、資料類別、矩陣、API、頁面、狀態機 API 對應）與 `tools/gen_permissions.py`：產生 PRD §4.1 範圍表與 §4.2 矩陣、ARCHITECTURE §6 的 API 權限欄、USER_JOURNEYS 各頁「權限」行（`--check` 驗證同步）。
  - P11 拆為 A「容量資料（不含個案）」（R3、R4、R5、R6·OWN-ORG）與 B「個案轉介清單」（R3·ASG、R4·SITE-REV、R6·REF；R5 不可）。新增 `GET /api/capacity`、`PATCH /api/organizations/{id}/capacity`、`GET /api/referrals`。
  - 其他 R3 驗證：新增 VERIFY 範圍（`PRODUCT_REQUIREMENTS.md` §4.5）——驗證人由 R4 或負責人指派單筆事件，≠登錄人、≠責任人與備援，只見事件摘要（類型、日期、取得證據、描述），不含家庭、成員與文件，無一般讀取、不能 E；新增 `GET /api/outcome-events/pending-verification`。
  - 補齊 API：`POST /api/assessments/{id}/retry`（AS-03）、`POST /api/tasks`／`PATCH /api/tasks/{id}`／`POST /api/resource-tasks` 分開、`DELETE /api/screenings/{token}`；供應商回呼列為 `api_external`（非人員角色）。矩陣新增 `resource_task`、`capacity_data` 類別，R4／R7 的資源暫停轉換權限寫進矩陣備註。
  - `policy_problems`：R5 不得見個案資料與轉介清單；R7 無一般個案讀取（只能 BG）且不可碰文件檔案與安全旗標；R9 唯讀（除 ReviewNote）且個案只能 SAMPLE；R6 只能 REF（案件類別限定）或 OWN-RES／OWN-ORG／AGG；R8 只能 AGG 且不可編輯；VERIFY 只可 R3＋outcome_event＋V／A；驗證 API 不得授權 ASG；每個 API 與頁面授權必須被矩陣涵蓋；每個狀態機操作者必須在對應 API 與矩陣有權；ARCHITECTURE 與 JSON 的 API、頁面清單必須互相涵蓋。
  - `tools/check_docs.py`：以 `gen_permissions.py --check` 取代 R1 的字串前綴檢查。
- **驗證方法與結果**：`gen_permissions.py --check` 通過（25 類、143 格、42 個 API、12 頁）；`tools/test_checks.py` 的權限反例（R5 取得轉介清單、混合區段、API 超出矩陣、VERIFY 放寬或用於個案資料、R7 一般讀取或文件、R9 可寫或非 SAMPLE、R6 超出 REF、R8 越權、R5 看個案、AS-03 無 API、API 或頁面在 JSON 缺漏）全部被抓到，每項斷言特定訊息而非任意失敗；人為破壞（R5 看轉介、驗證給 ASG、R7 一般讀取、手改產生區塊）全部被抓到。第一次執行 `gen_permissions.py` 就抓出 15 項既有矛盾（例如 R1 撤回同意在矩陣只有 V、R3 文件上傳在矩陣只有 V、AS-03 沒有 API），已在 JSON 修正後清零。
- **剩餘缺口**：這是**文件政策檢查，不是產品授權行為測試**（T-19、T-32～T-35、T-50、T-51 要等 WP-08 以真實帳號逐格測）；`permissions.json` 的矩陣內容本身是否符合實際營運，仍需 R4、資料責任人覆核。

### F-04 每日匯出的帳本有失敗窗口，撤回在備份後無保證　**狀態：完成（技術規格與純邏輯模擬層級；整合演練與法律可接受性未做）**
- **問題**：每日匯出的 DeletionLedger 在匯出前主庫失效會遺失；它只記 HARD_DELETE／REDACT，無法保證備份後的用途撤回（例如 REMINDERS）在還原後重新套用；驗證步驟「全部物件不存在」與 REDACT 矛盾。
- **修正**：`OPERATIONS_AND_PRIVACY.md` §1.3.3 重寫為**先寫的外部控制紀錄**（ControlRecord：僅附加、雜湊鏈、獨立權限域、不含個人內容）：寫入順序（先外部紀錄並取得確認、後主庫單一交易）、完成回應條件（200／202／503）、外部紀錄不可用時的人工處置、獨立見證水位、紀錄不完整或短於水位則維持隔離、還原後重新套用撤回（通知取消、分享停止與 STOP_USE_NOTICE、存取受限、核心撤回關閉處理、法令保存者保留並限制）、HARD_DELETE 驗證不存在而 REDACT 驗證已遮蔽、冪等重複套用。CP-16 改寫、新增 CP-26、RT-CTRL、U-23 擴大（只列待確認，不下法律結論）；`DATA_MODEL_AND_STATE_MACHINES.md` 的 ControlRecord；`ARCHITECTURE.md` 的 retention 模組與撤回 API 說明；`schemas/control_record.schema.json`。
- **驗證方法與結果**：`examples/ref_control.py`＋`examples/control_cases.json` 的 12 個情境：CS-01「備份後撤回、匯出前主庫失效」重新套用後通知取消、分享停止、物件消失、遮蔽套用；CS-02 冪等；CS-03 外部紀錄不可用→503 且主庫不變；CS-04 已記錄但提交失敗→202 後可恢復；CS-05 尾端遺失、CS-06 竄改、CS-07 缺號→維持隔離；CS-08～CS-10 HARD_DELETE 與 REDACT 驗證差異；CS-11 核心撤回與保留限制；CS-12 重疊撤回。人為破壞（忽略水位、略過重新套用、REDACT 改驗不存在、DB 失敗仍回完成、外部紀錄失敗仍改主庫、撤回不取消通知）全部被抓到。
- **剩餘缺口**：**這是純邏輯模擬，不是資料庫、物件儲存或備份整合演練**；沒有驗證任何供應商產品的不可變儲存能力、見證服務的實際可得性或備份時間點與序號的對應；備份內已刪除資料（≤30 天）、重新套用的法律可接受性、控制紀錄保存碼仍待法律與資安確認（U-23）；T-37 的整合演練要等 WP-09、WP-18。

### F-05 儲存清冊不一致（P2 草稿、CP-12 與 CP-24、冪等回應）　**狀態：完成（文件、參考案例；產品驗收未做）**
- **問題**：P2 承諾「儲存草稿（本機）」但清冊沒有瀏覽器端位置；CP-12 宣稱 IdempotencyRecord「只存 ID」，ARCHITECTURE 卻存 `response`；重播語意與權限、同意、刪除的關係未定。
- **修正（決定）**：P2 答案**只存伺服器端 ScreeningSession（24 小時，CP-05）**；瀏覽器端**不做內容持久化**（不使用 localStorage、sessionStorage、IndexedDB、Cache API、service worker），token 僅放 session cookie（HttpOnly、Secure、SameSite=Strict，無到期日）。移除「本機草稿」承諾；網路中斷時內容留在頁面記憶體並重送；新增「清除並離開」`DELETE /api/screenings/{token}`（共用裝置）。`USER_JOURNEYS_AND_SCREENS.md` P2；`OPERATIONS_AND_PRIVACY.md` CP-05、CP-12（重寫）、新增 CP-25（瀏覽器端）；`ARCHITECTURE.md` §6 冪等與 §6.3；`DATA_MODEL_AND_STATE_MACHINES.md` IdempotencyRecord；`schemas/idempotency_response.schema.json`。IdempotencyRecord.response＝`{status_code, resource_ref{type,id}, shape_version}`，**只存形狀**；只記錄 2xx；重播時以**當下**權限、同意與刪除狀態重新取得內容（失權或撤回→403 無內容；已刪除→410 且優先）。
- **驗證方法與結果**：`engine_cases.json` 的 `replay_cases`（5）、`IdempotencyStore` 只接受形狀（含非形狀欄位即拒絕）；人為破壞（儲存回應本文、重播不重檢）被抓到；`test_checks.py` 的 `idempotency_response` 結構反例。T-55（重播）、T-56（P2 瀏覽器端儲存邊界，未實作）已定義。
- **剩餘缺口**：T-56 要等 WP-05 才能以真實瀏覽器驗證；session cookie 是否構成「瀏覽器持久化」已列入 CP-25 並標注限制；現場共用裝置的實際風險需 AS-1～AS-6 與據點流程。

### F-06 AP-06 防重複擋掉合法 SUPPLEMENTARY　**狀態：完成（文件與純邏輯模擬層級）**
- **問題**：AP-06 的「無同鍵進行中或已核准申請」會把必須連結 APPROVED 原件的 SUPPLEMENTARY 擋住，合法補領永遠無法送件。
- **修正**：`state_machines.json`（單一來源）改寫 AP-06 前置條件與證據，再以 `gen_state_machines.py` 重新產生 `DATA_MODEL_AND_STATE_MACHINES.md` §3 區塊（沒有手改產生區塊）；新增 DATA_MODEL §2.13.1：依 kind 的送件前檢查、排除申請本身；`ref_engine.py` 的 `application_ready_check`；ORIGINAL 全狀態唯一與關聯件重複限制不變；關聯需同家庭、同資源、同給付期間，SUPPLEMENTARY 原件須 APPROVED 且 R4 核可。
- **驗證方法與結果**：`application_ready_cases`（17）與 `application_lifecycle_cases`（2：建立→準備→READY_TO_SUBMIT 的 SUPPLEMENTARY 正例；無核准、關係錯誤、重複關聯、ORIGINAL 重複的反例）；`legacy_ap06_blocks` 證明 R1 規則會擋掉該合法補件；人為破壞（AP-06 擋同鍵已核准）→13 項失敗。`gen_state_machines.py --check` 通過（6 台、86 個轉換）。
- **剩餘缺口**：資料庫的 partial unique index 與交易競態（T-46）屬產品測試；R4 核可流程（誰、何時）的畫面尚未設計。

### F-07 模型必要欄位定義不完整　**狀態：完成（結構與參考層級；schema 檢查範圍有限）**
- **問題**：`effective_unknown`、CUSTOM `expression`、複查寬限的起算資料沒有正式欄位定義，複查天數沒有可稽核的時間來源。
- **修正**：`DATA_MODEL_AND_STATE_MACHINES.md` §2.4／§2.4.1（欄位、型別、必填、類別、來源、更新時機、版本控管與派生欄位演算法）、§2.5（`expression`）；`state_machines.json` 的 RV-07 寫入、RV-08 清除 `recheck_started_at`；引擎 §0.2、§5.5、§8.0；`schemas/resource_version.schema.json`、`eligibility_rule.schema.json`、`household_scope.schema.json`；`tools/schema_lite.py`（不支援的 schema 關鍵字會報錯，不默默忽略）；`ref_engine.py`：`VERSION_INVALID`（缺必要欄位或 `effective_unknown` 與 `effective_to` 不一致）、`RECHECK_START_MISSING`、`RECHECK_START_INVALID`（格式不合、非字串或晚於 `as_of`）、`RECHECK_GRACE_EXCEEDED`、`RECHECK_HIGH_RISK`；`synthetic_resources.json` 補 `effective_unknown`。API 欄位見 DATA_MODEL §2.4.1 與 ARCHITECTURE。
- **驗證方法與結果**：`check_examples.py` 的 `test_schemas`（合成資源、口徑、控制紀錄逐一驗證結構）與 `recommendation_cases`（複查 14／15 天、HIGH 風險、缺起算、未來日期、亂碼、非字串、版本欄位不一致）；`test_checks.py` 的 schema 反例（缺必要欄位、型別錯誤、未知鍵、非法列舉、非法運算式）。人為破壞（移除 `effective_unknown` 一致性檢查）→4 項失敗；缺起算視為 0 天→2 項失敗；`schema_lite` 忽略未知鍵→4 項失敗。
- **剩餘缺口與限制**：**schema 只檢查結構、型別、必要、列舉與未知鍵**，不含跨欄位語意（`test_checks.py` 明確記錄「僅 schema 抓不到 `effective_unknown` 不一致」，由引擎驗證處理）；`check_docs.py` 的欄位路徑檢查仍只確認 `Entity.field` 存在，**頂層欄位名稱檢查不等於完整 schema 驗證**；`recommendation_base` 是精簡 fixture，不符合完整 resource_version schema（只有 `synthetic_resources.json` 通過）；真實 Django 模型與 CHECK 約束尚未實作。

### F-08 決策與章節引用錯位　**狀態：完成（文件政策檢查層級）**
- **問題**：PRD §7.6 的 PR-07（停滯天數門檻）引用 D-309（預算）而不是 D-310（營運時限與門檻）；DECISIONS D-106 的排序權重引用引擎 §6.4（自述不符的確認路徑）而不是 §6.6（排序）。
- **修正**：`PRODUCT_REQUIREMENTS.md` PR-07→D-310；`DECISIONS_AND_UNKNOWNS.md` D-106→引擎 §6.6。新增 `tools/citation_check.py`：對每個被引用的 D-xxx 與跨文件章節要求引用行含該主題的關鍵字，關鍵字表與例外清單（含原因）寫在程式內；`check_docs.py` 與 `test_checks.py` 呼叫它。同類掃描涵蓋 47 處 D-xxx 引用與 93 處跨文件章節引用（章節引用只有關鍵字表有列的章節才檢查語境），只發現上述兩處錯位（另有兩個誤報已列入關鍵字或例外並說明）。
- **驗證方法與結果**：`test_checks.py` 的反例（PR-07 引 D-309、D-106 引 §6.4、章節與主題不符、無關決策）全部被抓到，且「目前文件無任何引用語境問題」通過；人為破壞（把兩處改回原錯誤）→`check_docs.py` 失敗；停用檢查器→`test_checks.py` 失敗。T-61 定義於 BUILD_PLAN。
- **剩餘缺口**：這是**啟發式**檢查：只能抓到「引用行完全沒有被引用對象的主題字」，不能證明所有引用語意正確；關鍵字表需人工維護；只涵蓋 D-xxx 與列出的章節，其他引用類型（如 F-xx、G-xx）仍只檢查 ID 存在。

## 3. 同步更新（工時、批次執行包、測試）
- 測試 ID：新增 T-50～T-61（定義於 BUILD_PLAN §4，對應 §4.1 可執行規格與 §4.2 驗證層級；`check_docs.py` 逐一檢查「已定義、已被引用、已對應」）。
- 工時（BUILD_PLAN §2）：WP-02 +1～1、WP-04 +1～1、WP-05 +0～1、WP-08 +1～1、WP-09 +2～3、WP-11 +1～1、WP-18 +1～1，合計 +7～9 人日；第一批次 45～65 → **47～68**；MVP 100～152 → **107～161**；2 名並行 11～16 週、1 名 21～32 週；`OPERATIONS_AND_PRIVACY.md` 工程成本 NT$64～129 萬、一次性建置約 NT$84～179 萬；`DECISIONS_AND_UNKNOWNS.md` G-01 同步。這些是規劃估算，不是承諾。
- `BATCH1_EXECUTION_PACK.md`：B2-1、B2-2、B4-1、B4-5、B5-1 任務與驗收更新，D1～D4 小計與合計重新加總（17～25、10～14、10～15、10～14＝47～68），`check_docs.py` 逐項核對任務加總＝WP 工時。
- 版本標示改為 v0.4-draft（R2 修正）；`README.md`、`examples/README.md`、`DECISIONS_AND_UNKNOWNS.md` 更新入口與說明。

## 4. 必跑命令與實際輸出
以下於 repo 根目錄執行，輸出為交付前最後一次實際執行（commit 前）：
```
$ python3 docs/platform/examples/check_examples.py
OK: 910 checks passed                                   (exit 0)
$ python3 docs/platform/tools/gen_state_machines.py --check
OK: 6 state machines, 86 transitions, doc in sync       (exit 0)
$ python3 docs/platform/tools/gen_permissions.py --check
OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync   (exit 0)
$ python3 docs/platform/tools/test_checks.py
OK: test_checks 50 counterexample checks passed         (exit 0)
$ python3 docs/platform/tools/check_docs.py
OK: 1962 doc checks passed                              (exit 0)
$ git diff origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
（空輸出，exit 0）
```

## 5. 人為破壞（確認回歸檢查會失敗）
在暫存副本中各自套用一個破壞，執行對應檢查，全部被抓到（22 項；第 1～3 項在修正過程中先做，第 4～22 項以腳本在暫存副本重跑，結果摘要）：
| # | 破壞 | 被抓到的檢查 | 結果 |
|---|---|---|---|
| 1 | 缺 `rule.status` 預設回 PUBLISHED（F-01） | check_examples | 2 項失敗 |
| 2 | 未支援的口徑鍵再次被忽略（F-02） | check_examples | 33 項失敗 |
| 3 | 驗證吞掉未知口徑例外（F-01） | check_examples | 28 項失敗 |
| 4 | PR-07 改回引 D-309（F-08） | check_docs | exit 1 |
| 5 | D-106 改回引 §6.4（F-08） | check_docs | exit 1 |
| 6 | P11 轉介清單開放給 R5（F-03） | gen_permissions、check_docs | exit 1 |
| 7 | 驗證 API 授權給 ASG（F-03） | gen_permissions、check_docs | exit 1 |
| 8 | R7 取得一般個案讀取（F-03） | gen_permissions、check_docs | exit 1 |
| 9 | 手改產生的矩陣（F-03） | gen_permissions、check_docs | exit 1 |
| 10 | AP-06 擋同鍵已核准申請（F-06） | check_examples | 13 項失敗 |
| 11 | IdempotencyRecord 儲存回應本文（F-05） | check_examples | 4 項失敗 |
| 12 | 重播不重新檢查（F-05） | check_examples | 5 項失敗 |
| 13 | 移除 `effective_unknown` 一致性檢查（F-07） | check_examples | 4 項失敗 |
| 14 | 缺複查起算視為 0 天（F-07） | check_examples | 2 項失敗 |
| 15 | 還原忽略見證水位（F-04） | check_examples | 2 項失敗 |
| 16 | 還原略過重新套用（F-04） | check_examples | 7 項失敗 |
| 17 | REDACT 改驗「不存在」（F-04） | check_examples | 6 項失敗 |
| 18 | DB 失敗仍回完成（F-04） | check_examples | 1 項失敗 |
| 19 | 外部紀錄失敗仍改主庫（F-04） | check_examples | 2 項失敗 |
| 20 | 撤回不取消排程通知（F-04） | check_examples | 12 項失敗 |
| 21 | `schema_lite` 忽略未知鍵（F-07） | test_checks | 4 項失敗 |
| 22 | 停用引用語境檢查（F-08） | test_checks、check_docs | exit 1 |

## 6. 未完成事項與限制
- 沒有任何產品程式、資料庫、備份、授權行為或瀏覽器端的實際驗證；上列「通過」只在文件政策檢查與純邏輯模擬層級。
- 法律可接受性（備份中已刪除資料、還原後重新套用、控制紀錄保存碼）未確認（U-23），本輪不下法律結論。
- 年齡、就學、服役與工作能力推估所得等口徑能力**未實作**，只是被明確拒絕。
- `schema_lite` 只涵蓋結構；引用語境檢查是啟發式；`permissions.json` 的矩陣內容仍待 R4 與資料責任人覆核。
- 本輪沒有 GPT 的 F-01～F-08 逐字原文以外的補充資料；問題描述依任務所載內容。
- 維持：PR #1 為 Draft、不 merge、不宣告 APPROVED、不開始網站開發。

## 7. 下一步
GPT 以本輪 exact head 做獨立覆核：逐項驗證 F-01～F-08、重跑 §4 的命令，並抽查新反例（例如把非法條件放在規則最後、在口徑加入未知鍵、讓 P11 轉介清單給 R5、備份後撤回且匯出前主庫失效）。
