# R1 修正回覆（第一輪覆核 CHANGES_REQUESTED）
work_id：STP-PLATFORM-PLAN-001｜修正版本：v0.3-draft（R1 修正）｜2026-10-04｜狀態：READY_FOR_REVIEW（待獨立覆核；作者不宣告通過）

| 項目 | 值 |
|---|---|
| Repo／PR／分支 | firekou/SaveThePeople／PR #1（Draft）／`claude/stp-platform-plan-001` |
| live base（origin/main） | `9a7bd1295e20837786acc45bdab7fb94f5a1b012`（開工時核對，與前輪相同，無新提交） |
| 前輪受審 head | `d523bb6d476580208def886e023ed5015f725b8e`（verdict：CHANGES_REQUESTED） |
| 修正起點 | 同前輪受審 head（PR live head 開工時仍為 `d523bb6`，無他人新增提交，無評論、無 review） |
| 結果 head | 見 PR #1 的最新提交（本檔隨該提交推送；交付回報列出 exact SHA） |

## 0. 範圍與誠實聲明
- 本輪只修正規劃文件、合成範例與參考檢查程式；**沒有建置產品、沒有部署、沒有處理真實個案、沒有提交申請**。
- 四份原始基線文件（`docs/PROJECT_BLUEPRINT.md`、`EXECUTION_PLAN.md`、`SERVICE_MODEL.md`、`DATA_AND_PRODUCT_SPEC.md`）**未修改**（`git diff origin/main` 對這四個檔案為空）。需要調整基線的內容只以「待決提案」列於 `DECISIONS_AND_UNKNOWNS.md`（D-311、D-312、D-313 與 G-10～G-13），不視為負責人已批准。
- **作者在本 session 取得的是 R-01～R-12 的條目摘要，沒有取得 GPT 前輪逐條原文。** 下方「問題」欄是依該摘要與現況重新檢視後的描述；若原文有超出本檔描述的細節，請覆核者指出，視為尚未處理。
- 凡不能以可執行檢查證明、只能靠文件敘述者，都在各項「剩餘未知」與 §8 明列，不標成已驗證。

## 1. 前輪結果（保留，未改寫）
前輪（v0.2-draft，head `d523bb6`）：verdict **CHANGES_REQUESTED**。前輪作者自檢曾回報「`check_examples.py` OK」「連結與 ID 交叉引用無缺」「個資樣式掃描無命中」。這些自檢**都是真的通過**，但**沒有覆蓋 R-01～R-12 的缺陷**（例如檢查程式只比對了作者自己寫的預期值、沒有測資料不足與已知不符並存、沒有測未知成員、沒有測推薦判定、狀態機文件的圖與表是手寫而未互相核對）。因此那些通過不能當作文件正確的證據，前輪的 CHANGES_REQUESTED 維持有效，直到新的覆核另行判定。

## 2. R-01～R-12 對照
格式：問題／修正位置／驗證方法／實際結果／剩餘未知。檔名省略 `docs/platform/`。

### R-01 資格結果與缺資料優先序
- **問題**：前輪引擎規則先判「任一 FAIL → 不符合」再判資料不足，與基線「資料不足不得排除」衝突；自述不符只在門檻 5% 內有人工確認；只定義 ALL，ANY／CUSTOM／HUMAN 組合語意缺漏；不支援的組合沒有拒絕規則；沒有 UNKNOWN＋FAIL 等測試。
- **修正**：`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §6.1（單條件結果，自述 C1 永遠只能得 FAIL_UNCONFIRMED）、§6.2（ALL／ANY／CUSTOM 節點語意：UNKNOWN 優先）、§6.3（資源結果、`known_failures`、`KNOWN_MISMATCH_PRESENT`）、§6.4（所有自述不符都有確認路徑與 R3 任務、14 天升 R4）、§5.1（`min_confirmation_for_fail` 只允許 C2／C3）、§5.2（支援與不支援運算子、不支援即拒絕）；`USER_JOURNEYS_AND_SCREENS.md` J6、P3；`BUILD_PLAN_AND_ACCEPTANCE.md` T-26～T-30；範例見 R-11。
- **驗證**：`examples/engine_cases.json` 的 `combinator_cases`（18）、`resource_mapping_cases`（5）、`invalid_rule_cases`（19，含 NOT、N_OF_M、未知組合、AGE_BETWEEN、DATE_WITHIN、C1 確認不符合）；H6（UNKNOWN＋已確認 FAIL）、H7（UNKNOWN＋FAIL_UNCONFIRMED）；以 `check_examples.py` 執行。另做**變異測試**：把 ALL 的 UNKNOWN 優先序改成 FAIL 優先 → 14 項檢查失敗；允許 C1 確認不符合 → 20 項失敗。
- **實際結果**：全部通過（見 §3）；兩個人為破壞都被抓到。
- **剩餘未知**：D-312（已確認的地區或期間不符與資料不足並存時是否改判）是**待決提案，未啟用**；5% 為暫行參數（PR-08）；真實方案是否需要 NOT／N_OF_M 要到 P1 查核才知道（目前明確不支援並拒絕）。

### R-02 唯一的正式推薦判定
- **問題**：「可展示於目錄」與「可正式推薦」沒有分開；PUBLISHED／NEEDS_RECHECK／SUSPENDED／EXPIRED 各處處理不一致；期限不明在 §9 寫成「可發布並顯示」，與基線「期限不明暫停自動推薦」衝突；沒有檢查生效起日、申請期間、來源有效性。
- **修正**：`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §0.1（`catalog_visibility`）、§0.2（`recommendation_status`：7 項檢查、原因碼、FORMAL／MANUAL_CHECK_ONLY／NOT_RECOMMENDED）、§9（期限不明→人工查核項）；`DATA_MODEL_AND_STATE_MACHINES.md` §2.3（`lifecycle_status` 衍生規則）、§2.4（`conflict_status`、`effective_unknown`、`application_window` 類型含 FIXED `ranges`）、§3.1；`USER_JOURNEYS_AND_SCREENS.md` P1、P3、P9；`ARCHITECTURE.md` §6（新增推薦判定 API）；`BUILD_PLAN_AND_ACCEPTANCE.md` T-21～T-25、AS-6。
- **驗證**：`engine_cases.json` 的 `recommendation_cases`（28）涵蓋未生效、期間已結束但狀態尚未轉 EXPIRED、申請期間已截止／未開放／多段、期限未知、申請期間未知、查核中（低風險 3 天／15 天、高風險）、暫停、過期、被取代、草稿、V1／V3、來源衝突／已解決、來源 BROKEN／MOVED、規則未發布／無效、多重原因順序、FULL 不影響推薦；H1～H7×FOOD-005／RENT-006。
- **實際結果**：全部通過。
- **剩餘未知**：D-311（私有資源期限不明時放寬）是**待決提案，未啟用**；真實來源的期限格式（U-05）；產品中的資料庫與排程行為待 WP-02、WP-04、WP-10 實作後驗證。

### R-03 角色與權限
- **問題**：矩陣缺 R9；R7 有一般 V 權限；R6 範圍不明；R8 可否下鑽未說明；各格沒有案件、機構、欄位、用途、分享範圍；API 權限與頁面權限未與矩陣對齊。
- **修正**：`PRODUCT_REQUIREMENTS.md` §4 全部重寫（§4.1 範圍代碼、§4.2 九個角色×19 類資料、§4.3 各角色限制、§4.4 BREAK_GLASS／REVIEW_SAMPLE、§4.5 分享匯出兼任）；`DATA_MODEL_AND_STATE_MACHINES.md` §2.21（AccessGrant、ReviewNote）、§2.20（`access_grant_id`）；`ARCHITECTURE.md` §5（access 模組）、§6（權限欄改用範圍代碼；新增 access-grants、review-notes API）；`USER_JOURNEYS_AND_SCREENS.md` 各頁「權限」；`BUILD_PLAN_AND_ACCEPTANCE.md` T-32～T-35、WP-08、G1。
- **驗證**：`tools/check_docs.py` 對矩陣的不變條件檢查（R7 在個案內容列只能是 BG 或「—」、R8 只有 AGG 或「—」且不得編輯、R9 只有 V·SAMPLE 且無寫入、R6 只有 REF 或「—」、API 權限欄角色代碼有效、下載 API 排除 R7）；變異測試（把 R7 改成一般 V、給 R9 編輯權）都被抓到。
- **實際結果**：通過。
- **剩餘未知**：矩陣的權限測試（T-32～T-35）要等 WP-08 實作後才能以產品驗證；BG 的第二核准人取決於資料控管者（D-303）；試點初期 R6 無帳號，由 R3 代為登錄。

### R-04 撤回、保存與資料副本
- **問題**：沒有敏感資料副本清冊；撤回只列大項、沒有依用途處理；備份還原後如何重新套用刪除未說明；稽核「禁止修改」與保存期滿清除混在一起；成人成員資料、兒少代理、拒絕匿名報告後的處理沒有標示需法律確認。
- **修正**：`OPERATIONS_AND_PRIVACY.md` §1.3.1（副本清冊 CP-01～CP-24）、§1.3.2（依撤回用途的當日／7 天／通知與例外）、§1.3.3（隔離模式、`reapply_deletions()`、對帳）、§1.3.4（稽核日常保護 vs 受控清除）、§1.3.5（U-18～U-23 與限制處理）、§1.4（新增 RT-LEDGER、RT-REF）；`DATA_MODEL_AND_STATE_MACHINES.md` §1.6（保存與刪除適用表）、§2.10（Consent 撤回欄位）、§2.20、§2.21（DeletionLedger、PurgeRecord）；`DECISIONS_AND_UNKNOWNS.md` U-18～U-23；`BUILD_PLAN_AND_ACCEPTANCE.md` T-36～T-38、WP-09、G2。
- **驗證**：`check_docs.py`（CP／RT／U 引用皆有定義、欄位路徑、表格欄數）。**沒有可執行測試**（尚無產品）。
- **實際結果**：文件檢查通過；行為驗證未做（待 WP-09、WP-18）。
- **剩餘未知**：U-18～U-23 全部待法律確認，文件中的限制處理是暫行；備份內已刪除資料最長可存在 14～30 天（U-23）；供應商端（簡訊）紀錄的刪除能力（U-12）；本檔不下任何法律合規結論。

### R-05 取得成果與證據
- **問題**：以 Outcome 狀態計數，轉 ONGOING／ENDED 會漏計；核准證據與取得證據混用（核定書當取得證據）；RECEIVED 與 PARTIALLY_RECEIVED 的驗證要求不一致；部分取得、持續服務、重複給付、更正的計數沒有定義。
- **修正**：`PRODUCT_REQUIREMENTS.md` §7.2（核准證據 A1～A3 與取得證據 E1～E3 分開）、§7.2.1（事件計數表）、§7.4；`DATA_MODEL_AND_STATE_MACHINES.md` §2.19（Outcome 容器與原因枚舉）、§2.21（OutcomeEvent）、§3.5；`state_machines.json` OC-01～OC-09；`ARCHITECTURE.md` §6（events、verify API）；`BUILD_PLAN_AND_ACCEPTANCE.md` T-39～T-42。
- **驗證**：`engine_cases.json` 的 `outcome_scenarios`（9）與 `outcome_invalid_events`（1）：狀態推進不漏計、跨區間新增與累計、部分後完整只計一次、兩項資源一戶、未驗證（缺驗證人、驗證人＝登錄人、驗證人＝責任人）另列、驗證後移出待驗證、重複給付不計、更正後新報表重算而舊報表不變、非新增不計、核准無取得不計、窗口外事件忽略、缺證據等級被拒。
- **實際結果**：全部通過。
- **剩餘未知**：回溯期（PR-01）與驗證規則（D-105）是暫行／推薦值；各方案「取得」的實際語意（例如何時算已給付）要在 P1 逐方案查核；第二人驗證的人力可得性。

### R-06 完整狀態轉換
- **問題**：六個狀態機的圖、表、API 文字各自手寫而不一致；轉換缺操作者、前置條件、證據、可否撤回、更正方式；缺抽查複核、轉介結束、取消、重試、未取得後恢復；補件逾期被自動推定為 LAPSED。
- **修正**：新增 `state_machines.json`（單一事實來源，86 個轉換：RV 14、AS 9、AP 23、RF 18、OC 9、NF 13）與 `tools/gen_state_machines.py`（產生 `DATA_MODEL_AND_STATE_MACHINES.md` §3 的狀態表、mermaid 圖、轉換表，並驗證可到達、撤回為反向轉換、更正只限 R4、操作者合法）；API 一律以 `transition_id`（`ARCHITECTURE.md` §6）；補件逾期只產生警示（AP-14 要機關依據與 R4 確認）；`USER_JOURNEYS_AND_SCREENS.md` J8；`BUILD_PLAN_AND_ACCEPTANCE.md` T-15、T-43、T-44。
- **驗證**：`gen_state_machines.py --check`；`check_examples.py` 的狀態機檢查（非法來源狀態／操作者被拒、LAPSED 只有 AP-14 且不可由 SYSTEM、SUBMITTED→UNDER_REVIEW 不可自動、DENIED 之後只有更正、抽查、重試、取消、恢復等轉換存在、通知狀態不回退）；`check_docs.py` 確認文件引用的轉換 ID 都存在。變異測試：手改文件中的轉換列 → `--check` 失敗。
- **實際結果**：通過。
- **剩餘未知**：轉換的前置條件文字需在試點由 R3／R4 實務驗證；機關通知的形式因方案而異（U-05）；轉換執行函式與 API 的行為待 WP-11 實作。

### R-07 冪等與重複申請
- **問題**：訊息 ID 與回呼事件 ID 混用，沒有處理同訊息多事件、重複與亂序；狀態更新、稽核、後續任務沒有交易一致性說明；`unique` 只擋進行中申請，已核准後仍可重建；重新申請、更正、救濟沒有流程；併發建立沒有防護。
- **修正**：`ARCHITECTURE.md` §6（冪等語意：replay／422／409）、§6.2（單一交易的 6 步、Outbox、`SKIP LOCKED`、`UNKNOWN_OUTCOME`）、§6.3；`DATA_MODEL_AND_STATE_MACHINES.md` §2.13（修正的唯一約束：ORIGINAL 全狀態唯一；REAPPLY／APPEAL／SUPPLEMENTARY 的來源狀態條件）、§2.18、§2.21（NotificationEvent）、§3.6；`BUILD_PLAN_AND_ACCEPTANCE.md` T-45～T-47、WP-13。
- **驗證**：`engine_cases.json` 的 `application_cases`（14）、`callback_scenarios`（7），以及 `check_examples.py` 的 `IdempotencyStore` 與並發建立檢查（兩個不同 key 只有一件成功）。
- **實際結果**：通過。
- **剩餘未知**：交易與鎖的行為（雜湊鏈分鏈、`SKIP LOCKED`、約束）**只有規格與參考模擬，沒有資料庫整合測試**，待 WP-11、WP-13；供應商回呼的實際語意與順序保證（U-12）。

### R-08 文件擷取與外部 AI
- **問題**：同時宣稱「不送文件影像給外部 AI」與「文件擷取輔助」，路徑不明。
- **修正**：選定路徑：**人工登錄為預設；本機文字辨識（F-26）為試點後選項、不離開私有環境；外部 AI 文件處理（F-37）列為未啟用的待確認功能**。`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §11、§11.1、§11.2；`OPERATIONS_AND_PRIVACY.md` §1.2（DOCUMENT_EXTRACTION 用途）、§1.6；`ARCHITECTURE.md` §5、§6（`extract` API 只有本機版本）；`PRODUCT_REQUIREMENTS.md` F-26、F-37；`DATA_MODEL_AND_STATE_MACHINES.md` §2.16（`extraction.method`）；`BUILD_PLAN_AND_ACCEPTANCE.md` WP-26、WP-37、T-48；`DECISIONS_AND_UNKNOWNS.md` D-313、U-21。允許輸入、同意、人工確認、保存刪除、不可用時替代都已寫明；MVP 不把任何個案資料送外部 AI。
- **驗證**：文件交叉檢查（`check_docs.py`）與人工比對各處用語。
- **實際結果**：文件之間不再互相矛盾（人工檢視＋檢查程式的 ID／連結檢查）。
- **剩餘未知**：本機辨識引擎尚未選定與評估（U-21）；外部 AI 文件處理要啟用必須先經法律與供應商條款確認並由負責人書面核可；行為未實作。

### R-09 流程及閘門
- **問題**：J8 各分支缺輸入與失敗處理；J6 的複核佇列頁碼錯成 P5；未通過 G1～G8 時哪些工具可用、哪些真實資料不可輸入未定義；免姓名、免帳號被當成匿名。
- **修正**：`USER_JOURNEYS_AND_SCREENS.md` J8（8 欄、含轉換 ID、輸入、失敗處理，新增「機關認定失效」分支）、J6（→P8）、J1 註記；`BUILD_PLAN_AND_ACCEPTANCE.md` §3 閘門內容更新、§3.1（工具×前提×可做×不得做）、§3.2（AS-1～AS-6 匿名初篩最低條件）、T-49；`OPERATIONS_AND_PRIVACY.md` §1.1；`DATA_MODEL_AND_STATE_MACHINES.md` §2.21（ScreeningSession 去連結化）；`DECISIONS_AND_UNKNOWNS.md` G-13。
- **驗證**：`check_docs.py`（頁碼與 J／AS 引用、連結）與人工檢視。
- **實際結果**：通過。
- **剩餘未知**：AS-1～AS-6 與 §3.1 的實作與演練待 WP-18、WP-05；資料控管者尚未指定（D-303）。

### R-10 實體規格補齊
- **問題**：16 個指定實體的型別、枚舉、必填、外鍵、來源確認、保存、刪除、去重、版本規則不齊；Consent 撤回欄位、Application 本人確認欄位、Outcome 原因枚舉缺；欄位路徑與 API 不一致。
- **修正**：`DATA_MODEL_AND_STATE_MACHINES.md` §1.6（共同規則適用表）、§2.8～§2.21 重寫（Person／Fact 改為口徑屬性一律走 Fact；Consent 撤回與代理欄位；Application 本人確認欄位與 `kind`；Referral 關閉與取消原因；Notification 的訊息 ID 與錯誤分類；Outcome 的 `not_received_reason` 枚舉；AuditEvent；補充實體表）；`ARCHITECTURE.md` §6 API 的輸入輸出欄位與資料模型對齊。
- **驗證**：`check_docs.py` 解析資料模型的實體欄位表，驗證文件中 29 個 `Entity.field` 路徑都存在（變異測試：改成不存在的欄位 → 失敗）；表格欄數檢查（1279 個表格列）。
- **實際結果**：通過。
- **剩餘未知**：`FactKeyDefinition` 的實際字彙要在 P1 查核資源後才能定稿；資料庫層級的型別與約束待實作驗證。

### R-11 範例與 runner
- **問題**：必要成員口徑為 UNKNOWN 時，runner 直接排除該成員後繼續計算；C1 自述、`min_confirmation_for_fail`、FAIL_UNCONFIRMED 與 Markdown 星號不一致；md、JSON、規則、runner 不同步；不支援的語意沒有報錯；缺可重現測試。
- **修正**：`examples/synthetic_households.json` 重做（成員屬性為含確認程度的 Fact；新增 H5、H6、H7）；`synthetic_resources.json`（`min_confirmation_for_fail` 全為 C2、`conflict_status`、來源狀態、FIXED 申請期間 `ranges`）；`expected_assessments.json`（手算，含 `recommendation`、`known_failures`、`flags`）；`expected_assessments.md` 改由程式依 JSON 產生（`--write-md`，檢查程式驗證同步，**已無星號記號**，改用文字圖例）；新增 `ref_engine.py`、`engine_cases.json`、重寫 `check_examples.py`；`examples/README.md` 明列支援與不支援範圍。
- **驗證**：`check_examples.py`；三個人為破壞：UNKNOWN 優先序反轉 → 14 項失敗、允許 C1 確認不符合 → 20 項失敗、丟掉未知成員 → 7 項失敗；不支援項目（AGE_BETWEEN、DATE_WITHIN、區間值輸入、NOT／N_OF_M、C1 當確認）都有報錯測試。
- **實際結果**：通過；人為破壞都被抓到。
- **剩餘未知**：runner 刻意不支援 AGE_BETWEEN、DATE_WITHIN、區間值（正式產品需支援，見引擎文件 §5.2）；預期值是規格作者手算，**尚未經 R4 社工標註的 golden set 驗證**（WP-17、G6）；所有資料維持合成，不以模型輸出作為獨立正確基準。

### R-12 待決統計口徑
- **問題**：12 個月新增回溯期、第 180 天追蹤等被寫成既定；統計與規則沒有版本；`renewal_rule` 與 `benefit_period_rule` 欄位路徑不一致。
- **修正**：`PRODUCT_REQUIREMENTS.md` §7（開頭與 §7.6 參數登錄 PR-01～PR-08，標明「暫行」「待負責人決定」「已成立」）、§7.3；`DECISIONS_AND_UNKNOWNS.md` D-305、D-308 標暫行、§7（OP-01～OP-11）；`DATA_MODEL_AND_STATE_MACHINES.md` §2.21（ReportRun：`metric_spec_version`、參數、`restatement_note`）、§2.4（`benefit_period_rule.renewal`）；`USER_JOURNEYS_AND_SCREENS.md` J9 欄位路徑、P12；`OPERATIONS_AND_PRIVACY.md` §2.4 暫行聲明、§1.4。
- **驗證**：`check_docs.py` 欄位路徑檢查（`ResourceVersion.benefit_period_rule` 存在且 J9 使用 `.renewal.lead_days`）；人工檢視暫行標示。
- **實際結果**：通過。
- **剩餘未知**：PR-01、PR-02 等待負責人決定（D-308、D-305）；OP 系列時限待與據點約定（D-310）；報表版本化的實作待 WP-14。

## 3. 驗證命令與實際輸出
全部在 repo 根目錄執行，使用 Python 標準函式庫。
| 命令 | exit code | 實際輸出（最後一行） |
|---|---|---|
| `python3 docs/platform/examples/check_examples.py` | 0 | `OK: 433 checks passed` |
| `python3 docs/platform/tools/gen_state_machines.py --check` | 0 | `OK: 6 state machines, 86 transitions, doc in sync` |
| `python3 docs/platform/tools/check_docs.py` | 0 | `OK: 1750 doc checks passed` |
| `git diff --stat origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` | 0 | （空輸出＝四份基線未修改） |

測試範圍：參考檢查程式涵蓋 R-01、R-02、R-05、R-06（狀態機轉換規則）、R-07（申請唯一性、冪等、回呼）、R-11；文件檢查涵蓋連結與章節引用、ID 定義、欄位路徑、權限矩陣不變條件、工時加總、狀態機同步、表格欄數、版本標示、合成資料標記與個資樣式掃描。
變異測試（人為破壞後確認檢查會失敗）：參考檢查程式 3 項（見 R-01、R-11）；文件檢查 14 項——錯誤欄位路徑、R7 取得一般 V、R9 取得編輯權、總工時文字錯誤、工作包工時改了但總數沒改、手改狀態機表、未定義的 T／CP／轉換 ID、斷鏈、不存在的章節引用、Email、身分證號格式、舊數字殘留；其中**第一次嘗試的「錯誤欄位路徑」變異沒有被抓到**（當時只檢查有反引號的路徑、且變異字串剛好落在規則邊界），因此擴大為檢查所有 `Entity.field` 路徑（從 8 個擴大到 29 個），並以 `Household.no_such_field` 重測確認會失敗。

## 4. 圖、表、API、權限與欄位的一致性
| 面向 | 做法 | 結果 |
|---|---|---|
| 狀態機圖／表／文字 | 由 JSON 產生；`--check` 比對 | 6 個狀態機、86 個轉換，同步 |
| API 與狀態機 | API 以 `transition_id` 呼叫；文件引用的轉換 ID 都存在於 JSON | 通過 |
| 權限 | 矩陣不變條件由程式檢查；API 權限欄使用同一組角色與範圍代碼；頁面權限引用範圍代碼 | 通過 |
| 資料欄位 | `Entity.field` 路徑與實體表比對（29 個） | 通過 |
| 工時與成本 | 工作包表加總 ↔ BUILD_PLAN、批次執行包、OPERATIONS 成本、DECISIONS G-01 | 通過；舊數字不得殘留 |
| 連結／章節／ID | 全部 md 檢查 | 通過 |

## 5. G1～G8 對新增控制的涵蓋
| 新增控制 | 對應閘門與測試 |
|---|---|
| 資料不足優先、組合語意、不支援即拒絕、自述確認路徑、成員口徑未知 | G6（T-26～T-31） |
| 正式推薦判定（期限、申請期間、查核中、來源有效性） | G6（T-21～T-25）；AS-6 |
| R6／R7／R8／R9 限制、AccessGrant | G1（T-19、T-32～T-35） |
| 副本清冊 CP-01～CP-24、撤回清除、刪除帳本、備份還原重新套用、稽核受控清除 | G2（T-13、T-36～T-38） |
| 文件處理路徑（人工預設、本機辨識、外部 AI 未啟用） | G2（T-48） |
| 取得事件、第二人驗證、報表版本化、核准／取得證據分開 | G5（T-14、T-39～T-42） |
| 狀態轉換合法性、內部逾期不推定失效、回呼去重與亂序、併發與重新申請 | G4（T-44、T-45）、G5（T-43、T-46、T-47） |
| 閘門未通過的資料邊界、匿名初篩最低條件 | BUILD_PLAN §3.1、§3.2（T-49）；AS-4 對應 G7 |
| 暫行參數可參數化 | D-310（G3 前決定）；PR／OP 登錄 |

## 6. 工時與成本變動
R1 新增內容使工時由 42～61／90～135 人日調為**第一批次 45～65、MVP 100～152 人日**（+10～17）：WP-02 +1～1、WP-04 +2～3、WP-08 +1～2、WP-09 +1～2、WP-11 +2～3、WP-13 +1～2、WP-14 +1～2、WP-18 +1～2。同步更新：BUILD_PLAN §2、OPERATIONS 工程成本（NT$60～122 萬）與試點一次性建置（NT$80～172 萬）、DECISIONS G-01、批次執行包。成本仍為**估算**，不是報價或預算。

## 7. 基線保留確認
一縣市兩據點、兒少家庭優先、30～50 項資源、20～30 戶盤點、至少 10 戶新增取得（目標、無承諾）、受助者免費、多管道並行、初篩不等於核定、資料不足不得排除、真實個案不進公開 repo——**全部保留**。本輪對基線的所有可能調整（D-311、D-312、D-313、G-10～G-13）只是待決提案。

## 8. 未完成或僅部分完成（不標成已修正）
| 項目 | 狀態 |
|---|---|
| 產品行為（權限、刪除、還原、交易、冪等、回呼、AS 條件）的實際驗證 | **未做**：沒有產品。目前只有規格＋參考實作（R-01、R-02、R-05、R-06 轉換規則、R-07 純邏輯、R-11）；其餘為文件規格，行為待 WP-08～WP-18 |
| 可執行規格覆蓋的測試 | T-01～T-06、T-08～T-10、T-14、T-21～T-31、T-39～T-47（僅純邏輯層，產品行為待實作）；T-07、T-11～T-13、T-15～T-20、T-32～T-38、T-48、T-49 只有文件規格（BUILD_PLAN §4.1） |
| golden set 與 R4 標註 | 未做（需社工，WP-17） |
| 法律確認 U-18～U-23、U-08 | 全部待確認；僅暫行限制處理 |
| 本機文字辨識引擎、外部 AI 文件處理 | 未選定／未啟用 |
| GPT 前輪逐條原文 | 作者未取得；依 R-ID 摘要處理 |

## 9. 外部待確認事項
試點縣市與兩據點（U-01、U-02）、R4 人選（U-03）、經費（U-04）、30～50 項資源的正式規定（U-05）、雲端帳號（U-06）、機構對資料位置與境外服務的要求（U-07）、個資法修正施行日與事故通報（U-08）、AI 供應商條款（U-09）、雲端與簡訊價格（U-10～U-12）、LINE（U-13）、MyData 與政府介接（U-14）、法定通報（U-15）、各方案代辦規則（U-16）、公開專線現況（U-17）、法律確認（U-18～U-23）。皆不阻斷第一批次（見 DECISIONS §4 的「不受影響可先做」）。

## 10. 下一批次執行包
見 `BATCH1_EXECUTION_PACK.md`：承接 WP-00～WP-07、WP-08a；指定第一個可驗收交付物（D1：合成資源目錄上線於 staging 並可公開查詢）、依賴、35 項任務拆解（工時加總與工作包一致）、操作示範腳本與完成定義。**本輪不開工**；啟動條件之一是本輪規劃經獨立覆核通過。

## 11. 狀態
**READY_FOR_REVIEW。** 作者不宣告 APPROVED，也不 merge。
