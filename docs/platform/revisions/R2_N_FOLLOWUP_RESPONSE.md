# R2_N_FOLLOWUP 作者回覆（N-02～N-06）

work_id：STP-PLATFORM-PLAN-001；task_id：STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP；stage：R2_N_FOLLOWUP；revision 1（repair_round 1／1）
起點 source_content：02935f528b42a35b3a793d1dec370a5091691288；handoff：599a25b8882a5a4671d79443670364f127202a9c；base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
驗證層級：文件政策檢查＋純邏輯參考模擬（AUTHOR_EVIDENCE）。**未做**：產品自動化測試、整合演練、人工演練。不是 VERIFIED、不是 APPROVED。
資料：全部合成；無真實資料、無外部呼叫、無支出。

## 逐項對照（finding → 根因 → 修改位置 → 反例 → 命令 → 結果 → 缺口）

### N-01（保持不退化）
未動 `_expr_problems`；既有 order-independence 與 illegal_expression_variants 檢查仍通過（check_examples 全綠）。

### N-02 `in_school=false` 被當成未提供
- 根因：`ref_engine.py` 以 `where.get("in_school")` 真值判斷，False 與缺鍵同義。
- 修改：`ref_engine.py` COUNT_MEMBERS_WHERE 改以鍵「存在」判斷，並以 `sch["value"] is where["in_school"]` 比對；`RESOURCE_AND_ELIGIBILITY_ENGINE.md` §5.2 定義三態（未提供＝不篩選、true＝在學、false＝不在學；加鍵後成員就學未知→UNKNOWN）。採「支援 false」，未選擇拒絕。
- 反例（手算，H1 SCOPE-CO，0～17 歲成員為 P2 8 歲在學 C1、P3 3 歲不在學 C1；P1、P4 不在年齡範圍）：無鍵 count=2 PASS；true count=1（min1 PASS／min2 FAIL_UNCONFIRMED）；false count=1（min1 PASS／min2 FAIL_UNCONFIRMED，不是 PASS）；P2 就學未知＋false→UNKNOWN（missing H1-P2:person.in_school）；無鍵時忽略就學未知仍 PASS；全部輸入改 C3 後 false min2 才是 FAIL（確認程度不被提升）。位置：`check_examples.py::test_count_in_school`。
- 人為破壞：`tools/test_checks.py::test_n02_mutation` 把舊寫法放回，結果變 PASS，被抓到。

### N-03 見證「定期」更新的時序缺口
- 根因：文件稱見證定期更新，而參考實作同步更新；定期更新尚未 flush 時，主庫失敗（202）後再遺失控制尾端，還原會放行且撤回效果遺失。
- 規範（`OPERATIONS_AND_PRIVACY.md` §1.3.3）：見證必須在寫入控制紀錄**前**同步持久確認 seq（未確認／逾時／未 flush／不可用＝未確認→503，控制紀錄與主庫都不動）；202 只在見證與控制紀錄都確認後才可回覆；紀錄寫入失敗→503 且見證水位已領先（同 seq 重試補上，否則還原時維持隔離，刻意 fail-closed）；見證另記各 seq 雜湊，還原時比對以抓「重算鏈的整段重寫」；還原時查不到見證→隔離。
- 修改：`ref_control.py`（Witness.report 回傳確認、record_hash、WitnessUnavailable；request_control 先驗證→見證→紀錄→主庫；recover 增加 WITNESS_UNAVAILABLE、LOG_REWRITTEN_AT_n）。
- 案例（`control_cases.json` CS-13～CS-20，預期值依規範手算，水位含 APPLIED 紀錄）：CS-13 未 flush 見證→503/不動/還原不隔離（無承諾）；CS-14 見證單次失敗→503，重試→200，水位 2；CS-15 紀錄失敗後見證領先→還原隔離 `LOG_INCOMPLETE:last=0<witness=1`；CS-16 同 seq 重試後還原通過；CS-17 還原時見證不可用→隔離；CS-18 重算鏈改寫→`LOG_REWRITTEN_AT_1`；CS-19 重播舊紀錄→`LOG_INVALID:SEQ_GAP_AT_3`；CS-20 HARD_DELETE／REDACT 見證失敗→503、資料不動；既有 CS-01～12（含 REDACT／HARD_DELETE）維持通過（合法同步控制）。
- 人為破壞：`test_checks.py::test_n03_mutation`：移除見證確認判斷、移除雜湊比對，各自被抓到。
- 對 GPT 反例腳本的說明：`reconcile_probe_20261007.py` 的 N-03 使用修補前的 payload 形狀（`consent` 鍵、無 envelope），現在會因 N-05 回 422 `INVALID_CONTROL`，不再走到見證情境；等價的修補後情境是 CS-13（PeriodicWitness＝未 flush 見證）。腳本未修改。
- 缺口：真實見證服務、逾時語意、DB 交易、備份演練、法律可接受性（U-23）均未驗證。

### N-04 verify 人員排除與 P9 R4 範圍
- 根因：排除條件只是 note 文字，政策檢查不看；P9／transitions API 的「R4、R7 僅可暫停／停用」與矩陣（R4 僅 RV-09／10；RV-14 僅 R5／R7）矛盾。
- 修改：`permissions.json` 新增結構化欄位 `verifier_must_not_be`（registrant、case_owner、case_owner_delegate）與矩陣 `transition_limits`（R4＝RV-09、RV-10；R7＝RV-09、RV-10、RV-14）；`tools/gen_permissions.py` 新增 `verify_note`、`verifier_allowed`、`limit_phrase`、`derived_resource_notes`，政策檢查要求結構欄位與狀態機操作者完全一致，且矩陣、API、P9 的文字必須等於衍生文字（任意 note 覆蓋會被抓）。生成區塊已重產；ARCHITECTURE 驗證 API 錯誤欄補「代班責任人」。**未增權**：只收緊與結構化既有限制；R4 仍不可 RV-14。
- 反例（`test_checks.py::test_n04_counterexamples`）：note 改成「責任人也可驗證」→抓到；移除任一排除項／整欄→抓到；`verifier_allowed` 對登錄人、責任人、代班責任人皆拒絕，另一位第二人允許（合法控制）；R4 限制擴大到 RV-14→抓到；狀態機把 RV-14 給 R4→抓到；P9 與 transitions API 舊文字還原→抓到；R4 有編輯權但無結構限制→抓到。
- 缺口：`verifier_allowed` 是參考判斷，非產品授權行為測試（T-19、T-32～T-35、T-50、T-51 待 WP-08）。

### N-05 ControlRecord envelope／payload
- 根因：schema 只認舊的扁平 `type` 且無必要欄位檢查；文件欄位（seq、prev_hash、recorded_at、consent_id）被視為未知鍵；模擬以 `consent` 而非 `consent_id`。
- 修改：`schemas/control_record.schema.json` 改為 envelope（seq、prev_hash、hash、recorded_at、payload）＋四種 payload（oneOf，各自必要欄位、型別、未知鍵拒絕、purposes／fields 非空、reason 列舉）；`ref_control.py` 以同一 schema 驗證，加目標存在、不重複、欄位存在、APPLIED.ref 指向較早非 APPLIED 紀錄；`control_cases.json` 的 `consent`→`consent_id`；OPERATIONS §1.3.3、DATA_MODEL ControlRecord 列同步。
- 反例：`test_checks.py::test_n05_schema_counterexamples`（18 種不合法 payload、6 種不合法 envelope、1 組合法控制）、`check_examples.py::test_control_log_envelope`、CS-21（16 種不合法請求→422 且不寫任何東西，隨後合法請求 200）。
- 缺口：schema_lite 不支援跨欄位語意，語意由 `ref_control.py` 驗證。

### N-06 聲明範圍
- 修改：收窄 `ARCHITECTURE.md` §6（原「權限矩陣每格都有自動化測試」→ 僅文件政策檢查，產品授權測試尚不存在）與 `BUILD_PLAN_AND_ACCEPTANCE.md` §4.2（原「文件之間自洽」→ 僅檢查已列出的對應關係）。歷史回覆（R1／R2／R2_REPAIR_RESPONSE、GPT 紀錄）不改寫。
- 更正：GPT_REPAIR_REVIEW_02935F5 的 APPROVED 只涵蓋 F-01／F-03／F-07 差異；本回覆**不**宣稱所有缺口關閉——N-02～N-06 的關閉與否由 GPT 對固定 head 獨立判定。R2_RESPONSE 各節「完成」同理僅指當時檢查範圍。

## 驗證命令（repo 根目錄；數字見交付留言的實際輸出）
```
python3 docs/platform/examples/check_examples.py
python3 docs/platform/tools/check_docs.py
python3 docs/platform/tools/gen_state_machines.py --check
python3 docs/platform/tools/gen_permissions.py --check
python3 docs/platform/tools/test_checks.py
git diff origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
```
not-run：check_report_format.py（NOT_FOUND）；遠端 CI（repo 無）；產品測試（無產品）。

## 未決與限制
- 見證確認的逾時值、重試退避、R7／資料責任人處理「見證領先」的 SOP 屬 WP-09 之後實作決定，未訂。
- 小彙總再識別門檻、備份保存碼等仍待 U-23／負責人決定；本包未改任何 D-3xx。
