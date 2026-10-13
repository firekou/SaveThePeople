# Claude 剩餘缺口修補 Prompt

你是 SaveThePeople 執行端，GPT 是獨立 Reviewer。任務 STP-PLATFORM-PLAN-001-REMAINING-GAPS-20261007。這是新修補包的準備稿，不延長或重置上一個已用完的修補包，不代表已收到遠端派工。

起始成果：02935f528b42a35b3a793d1dec370a5091691288。可信 main：9a7bd1295e20837786acc45bdab7fb94f5a1b012。PR #1 此包準備時為 af19c9983620ed248de5e13196162a16297aed21。先讀所有 live refs、最新工單、claim、治理決策；存在新內容或競爭 claim 就停並回報，不沿用舊 session 身分限制。平台允許的成果分支可交付，必須固定結果 SHA；不要求推到受限制分支。

先讀 GPT_R2_RECONCILIATION_20261007.md 和 reconcile_probe_20261007.py。兩者由本次 GPT 交付，若遠端尚無此檔，需從本 Prompt 提供者取得檔案，不得假稱讀過。

只改 docs/platform 的必要規格、schema、參考模擬、檢查與新 revisions 回覆。四份基線不改；不改 GPT 歷史報告、R1/R2 作者歷史；不增權；D-311/D-312、外部 AI 文件處理仍未啟用；沒有真實個案、聯絡資料、憑證、產品程式、部署、支出、main merge 或原 PR 分支整合。

一次有界修補，最多90分鐘、外部成本0；不足就交部分結果與 BLOCKED，不擅自派第二輪。

請修：
1. N-02：定義 where.in_school 未提供=無篩選、true=在學、false=不在學；若因規格範圍不支援 false，明確拒絕且說明，不能悄悄忽略。採支援時，H1 0～17歲 false 應 count=1，min_count=2 應 FAIL_UNCONFIRMED；8歲成員在學未知則 UNKNOWN。確認程度不能改成已確認不符合。其他篩選已確定排除者可不要求其在學資訊，但須定義與測試。
2. N-03：統一控制寫入確認、獨立持久見證、套用與回應的順序。定期見證不可保證尚未 flush 的尾端完整；未確認／超時／見證不可用維持隔離或明確失敗，不可放行。測試主庫失敗後控制尾端丟失、見證尚未更新、見證超時、控制鏈竄改、合法同步控制。這仍是文件與純邏輯模擬，不能宣稱真實備份演練。
3. N-04：驗證人不能是登錄人、案件責任人或代班責任人，寫成可檢查的結構化條件；補自我驗證反例及合法第二人控制。用明確 transition IDs 限定 R4 暫停 RV-09/10，不能用 P9「停用」暗示 RV-14 權限。既有角色不增權。
4. N-05：定義 ControlRecord envelope 與 payload，統一 consent/consent_id、prev/prev_hash、seq、hash、recorded_at。依 CONSENT_REVOKE/HARD_DELETE/REDACT/APPLIED 要求各自必要欄位；缺用途、缺目標、缺 fields、未知鍵、錯型別均拒絕。同步 schema、ControlLog、文件和案例，不用產品碼解決。
5. N-06：收窄現行文件「每格都有自動化測試」「文件之間自洽」等聲明到實際已測欄位／已知反例；保留历史，新增 REMAINING_GAPS_RESPONSE_20261007.md 說明本次更正。最新另一份 F-01/F-03/F-07 修補已通過的事實保留，不能從局部批准推成全部缺口已關閉。

驗收：每項有手算預期、正向控制、獨立反例與移除防護必失敗的 mutation。重新跑五項工具、四基線diff；實際 stdout/stderr/exit 全列出。更新工時僅必要時重新加總，不捏造預算或產品驗證。

命令：
python3 docs/platform/examples/check_examples.py
python3 docs/platform/tools/gen_state_machines.py --check
python3 docs/platform/tools/check_docs.py
python3 docs/platform/tools/gen_permissions.py --check
python3 docs/platform/tools/test_checks.py
git diff origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md

交付 fixed SHA、結果分支、compare、N-02～N-06逐項狀態、命令輸出、仍未知的限制。推送僅平台允許分支並讀回 SHA。READY_FOR_GPT_REVIEW 或 BLOCKED，不能自稱 APPROVED。不得自行啟動網站工程。GPT覆核新head後再進整合。
