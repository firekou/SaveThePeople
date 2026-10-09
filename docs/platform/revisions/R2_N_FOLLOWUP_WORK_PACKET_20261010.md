# R2 剩餘缺口後續修補工作包
work_id: STP-PLATFORM-PLAN-001
task_id: STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP
stage: R2_N_FOLLOWUP
revision: 1
status: READY
executor: Claude
reviewer: GPT（未修改作者實作）
next_actor: Claude
next_action: 讀取本包、核對 refs 與競爭 claim，接單後修 N-02～N-06。

## 授權、歷史與固定起點
Frank於2026-10-10要求恢復交接、回寫必要工單、獨立覆核及候選整合準備。此包具體化既有離線文件與參考模擬修補；不是產品開工或main merge授權。
可信main/base: 9a7bd1295e20837786acc45bdab7fb94f5a1b012。
原Claude修補: 02935f528b42a35b3a793d1dec370a5091691288。
原PR #1 reviewer head: af19c9983620ed248de5e13196162a16297aed21。
已準備候選整合: 50d2c56ac1e223dc2afdfe50f17e4ffb9fea6c75（一般merge，保留兩方歷史）。
本機歷史核對紀錄: 27f575518e77b97807d7b746c03434265baef2d3（未推送，不能用它作遠端起點）。
實際source_content=02935f528b42a35b3a793d1dec370a5091691288；從此遠端成果以平台允許分支接續。工單在PR #1的Reviewer-only紀錄head，通知列出固定handoff SHA；它與source_content分開，不從main重做。

旧F-01/F-03/F-07包于2026-10-06T08:00:00Z截止，一次修補已使用且結案，本包不續期、不增加舊包額度。此包針對後來具體核對的N缺口，仍沿同一work_id，保留舊Finding及證據，不把原問題改名當成已修。
本次後續修補上限：1次交付、90分鐘實作、自檢包含在90分鐘內、外部成本0；deadline=2026-10-12T18:30:00Z。claim時記開始與累計投入。deadline到期／額度不足交部分成果與BLOCKED；GPT不能自動重發或展延。
repair_round_limit=1；repair_rounds_used=0（本次新stage；旧stage=1另列且不變）。同stage最多1個有效claim。不是無限續作。

## 唯一有效工作包與必要閱讀
本包取代CLAUDE_REMAINING_GAPS_PROMPT_20261007.md的「準備稿」作為實際派工；歷史稿保留。
讀 [核對報告](GPT_R2_RECONCILIATION_20261007.md)、[反例腳本](reconcile_probe_20261007.py)、最新治理決策、BATCH1_EXECUTION_PACK及受影響規格。
反例腳本只印診斷，不以exit0代表缺口通過。N-03 PeriodicWitness是文件時序的注入模型，不能當作原同步實作失敗。

## 範圍
scope_paths：docs/platform的ARCHITECTURE、DATA_MODEL_AND_STATE_MACHINES、RESOURCE_AND_ELIGIBILITY_ENGINE、PRODUCT_REQUIREMENTS、USER_JOURNEYS_AND_SCREENS、OPERATIONS_AND_PRIVACY、BUILD_PLAN_AND_ACCEPTANCE必要一致性；examples/、schemas/、tools/；permissions.json（只收緊與結構化既有限制）、state_machines.json必要一致性；新增revisions/R2_N_FOLLOWUP_RESPONSE.md。
excluded_paths：四份原始基線、README、GPT歷史與治理紀錄、R1_RESPONSE/R2_RESPONSE/R2_REPAIR_RESPONSE、既有Reviewer反例腳本與本工作包；所有產品程式、部署、credentials、真實資料。
不增權、不改人日估算或基線。D-311/D-312未啟用、外部AI文件處理未啟用。

## 修補與驗收
N-01：保留遞迴未知鍵防護，合法巢狀ALL/ANY仍可用。
N-02：where.in_school未提供無篩選、true在學、false不在學；若選擇明確不支援false須拒絕並列規格限制。不得truthiness忽略。支援時H1 0～17歲false count=1，min_count2為FAIL_UNCONFIRMED；8歲在學未知應UNKNOWN。補合法控制、false、未知及確定排除成員案例，來源確認程度不提升。
N-03：統一外部控制寫入確認、獨立持久見證、主庫套用、回應與還原隔離。見證更新失敗／超時／未確認、主庫失敗後控制尾端遺失均不可不加判斷地恢復服務；明確何時200/202/503與隔離。補合法同步、未flush、见證不可用、鏈竄改、重播、REDACT/HARD_DELETE控制。只驗純模擬，不宣稱實際備份演練或法律合規。
N-04：verify人不可為登錄人、責任人或代班責任人，以結構化條件與反例驗證；補合法第二人控制。P9的R4僅允許RV-09/10，RV-14仍R5/R7；限制文字由結構化規範衍生，不增權。note矛盾要抓到或禁止任意note覆蓋規範。
N-05：定義ControlRecord envelope/payload與統一欄位；每類動作必要欄位、型別、未知鍵、空用途、空遮蔽fields、目標與APPLIED關聯均驗證。文件、schema、模擬一致，別只驗type。
N-06：現行「每格都有測試／全面自洽」限定到實際檢查範圍；保留歷史，在新回覆更正局部批准與全部缺口關閉的差別。
預期值須手算並寫來源；每項負向與合法控制；移除關鍵防護的mutation應以預期原因失敗。既有SUPPLEMENTARY、重播授權、撤回、三值邏輯與角色限制不得退化。

## 命令與證據
python3 docs/platform/examples/check_examples.py
python3 docs/platform/tools/gen_state_machines.py --check
python3 docs/platform/tools/check_docs.py
python3 docs/platform/tools/gen_permissions.py --check
python3 docs/platform/tools/test_checks.py
以可信base對新成果核對四份基線diff空。
每項列實際stdout/stderr/exit；實作工時與外部成本如為自述標REPORTED；不能複製舊數字。

## 接單、交付與停止
接單：PR #1引用本包固定handoff SHA、自己的session、平台允許分支、起點、scope、競爭claim核對、deadline與投入；session可不同，不冒充原session、不要求Frank回到舊對話。
結果：本次Claude已回報平台指定分支ccr-dd86219c-ijac1h，可於此交付；若後續指定不同分支須在claim明載且核對無競爭成果。從02935f5保留祖先接續，不要求先整合PR #1，候選整合批准不是修補前置。平台允許的本repo成果分支（不強求原PR分支）；non-force，保留祖先與作者。推送後讀回完整result SHA；回PR #1列compare、exact-head回覆連結、逐項狀態、命令與未驗項。
READY_FOR_GPT_REVIEW或BLOCKED；不能自稱APPROVED。
未知新差異、競爭claim、期限／額度不足、存取受阻立即具體回報，不force、不繞平台。
固定成果後next_actor=GPT，獨立覆核N缺口；有新反例需另核對剩餘額度，不默認第二次修補。
網站工程本包不啟動。第一可見成果與開工決策見[展示決策包](SYNTHETIC_WEBSITE_START_DECISION_20261010.md)。
