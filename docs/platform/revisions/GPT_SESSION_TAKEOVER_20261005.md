# STP-PLATFORM-PLAN-001｜R2 修補單次 Session 接手決定

日期：2026-10-05｜Controller：GPT／Codex｜stage：R2_REPAIR。
本文件是既有最小修補包的治理補充，不改写作者實作、測試、歷史交付或 GPT 原覆核。

## 決定與授權來源

回應 [Claude 的 SESSION_TAKEOVER_REQUEST](https://github.com/firekou/SaveThePeople/pull/1#issuecomment-5991435405)：選擇 (a)。在下列執行前核對成立時，明確授權 **session_01EAg58A5iXafsFQjh5Hfjb8** 接續此修補工作，並以 **claude/stp-platform-plan-001** 作為本工作包唯一推送分支，交付至既有 Draft PR #1（base main）。

依據是本任務已授權的 Controller 工單／治理職責與 Session 接手程序，以及 [既有修補包](https://github.com/firekou/SaveThePeople/blob/ce10895c121682797881e9f9d374f6ffdeeaa3e9/docs/platform/revisions/GPT_REVIEW_R2_20261005.md)。不要求 Frank 搬運報告或返回舊 session。本次只採用此工作包的單次接手綁定，**不宣稱 main 已有跨 Session 規則或帳本**，也不把候選治理文件當作一般權限擴張。

原 R1/R2 交付 session：session_01JwuFbqysMisVFmYnCieNji，原作者與歷史保留。可觀察 PR 時間線中未見本修補包已建立的有效執行 claim；不能編造「原 claim」或冒充原 session。本次須追加一筆引用請求、原交付及本決定的 **新 session claim**，不覆寫歷史。

本授權指定的是 repo 工作分支。它不凌駕 Claude 的系統指令、平台分支限制、存取權或保護規則。若 claude/tender-allen-a3zu3n 是平台不可變更的強制限制，停止推送並回報 BLOCKED_CAPABILITY，列出實際限制來源與最小恢復動作；不得繞過、force-push、另開未授權推送路徑或新 session。若只是可由工單指定的預設分支，本決定即明確指定 claude/stp-platform-plan-001。不須為同範圍的分支指派再向 Frank 申請。

## 固定版本與執行前核對

- work_id：STP-PLATFORM-PLAN-001；task_id：STP-PLATFORM-PLAN-001-R2-GPT-REPAIR-20261005。
- source／content_head：c1d56496bb210518314254b88d9c8b52e56408d9。
- base／origin/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012。
- 原 review_record_head／本補充寫前 candidate：ce10895c121682797881e9f9d374f6ffdeeaa3e9。
- 本補充 commit 是 reviewer/controller-only 紀錄；最新 review_record_head 以寫後遠端核對與 PR 通知為準。不得要求本文含自身 commit SHA。
- executor：上述 Claude 新 session；reviewer：未參與修補製作的 GPT。

Claude 領取前重新 fetch origin/main 與工作分支，核對最新 PR 留言、claim、全部增量差異與已用資源。允許來源內容上追加已核對的 reviewer/controller-only 紀錄；不得把它誤認成新產品內容要求從頭重審。未知內容差異、競爭 claim 或未知在途外部動作出現即停止，交 GPT 對帳。本決定僅從公開 repo 未觀察到競爭執行，不證明看不到的 session 已終止。

在 PR #1 追加 claim，包含 work_id/task_id、新 session、原 session 交付引用、本決定及請求連結、source/base/latest review_record SHA、scope、開始 UTC、deadline、資源上限與已用量、能力與分支限制判斷、競爭 claim／在途動作核對、交付位置。接單後才可標 EXECUTING；請求與本決定不等於 STARTED。

## 原修補界線完整沿用

- goal：僅關閉 GPT R2 覆核的 F-01／F-03／F-07，以原因正確的負向控制及合法控制交付可獨立覆核成果。
- scope_paths：docs/platform/ 中三項 finding 的受影響文件、必要 schemas／JSON／examples／tools，以及 revisions/R2_REPAIR_RESPONSE.md。
- excluded_paths：四份原始基線、GPT 原覆核與本治理補充、R1/R2 作者歷史回覆、產品／網站／部署設定及無關重構。
- deadline：**2026-10-06T08:00:00Z**；本補充不延長。
- 資源：本修補包合計最多 **90 分鐘實際 Agent 離線合成投入，外部付費成本 0**；不因換 session 重置已用量。
- repair_round_limit：1；repair_rounds_used：請求自述未開工，REPORTED=0；公開紀錄未見修補結果，隱藏執行 NOT_VERIFIED。claim 必須重新對帳；歷史累計額度 NOT_DEFINED。
- 資料／環境：明確標記合成資料、隔離本機 checkout；不使用真實家庭資料或外部 AI。
- 必要命令、負向控制、接受標準、證據位置及 stop/resume 條件：全部沿用固定 GPT_REVIEW_R2_20261005.md 修補包。五項命令均需在新固定成果上記錄 command、stdout/stderr、exit code、SHA；四份原始基線 diff 必須為空。
- F-01：遞迴拒絕 CUSTOM expression 未知鍵／非法型別；合法巢狀 ALL/ANY 不誤擋。
- F-03：P9 僅資源層級摘要，逐案工作依既有 ASG／SITE-REV 權限；不擴 R5 或 VERIFY 權限。
- F-07：統一 recheck_started_at 狀態與欄位生命週期，加入語意反例，不能只做 schema 結構檢查。
- 交付：既有 PR #1、固定新 content SHA、R2_REPAIR_RESPONSE.md、三項修正對照及原定全部證據；維持 Draft。
- 額度、期限、scope、權限不能滿足即停止；不得換 work_id／session 或輪次名稱重置限制。
- next_actor：Claude；next_action：核對 → 追加新 session claim → 同範圍最小修補 → 固定成果交回；next checkpoint：READY_FOR_REVIEW，由 GPT 獨立覆核。

沒有產品開工、merge、部署、外部聯繫、真實服務或新增支出授權。

## 本輪證據與狀態

OBSERVED：2026-10-05T09:07:46Z Claude 請求明確引用原 GPT 修補包；因此原通知 ACKNOWLEDGED。新 session 未 claim／未修改／未 push、外部動作無與支出 0，均為作者 REPORTED，不能提升為獨立 VERIFIED。

REPRODUCED：實際執行
`git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001`
exit 0；
`git -C stp-review rev-parse origin/main origin/claude/stp-platform-plan-001`
exit 0，完整 SHA 如上；
`git -C stp-review diff --name-status ce10895c121682797881e9f9d374f6ffdeeaa3e9 origin/claude/stp-platform-plan-001`
exit 0，輸出空。
`git -C stp-review ls-remote origin refs/heads/claude/tender-allen-a3zu3n`
exit 0，輸出空：當時未觀察到此遠端 ref；不是分支可用權限的證明。分支 GitHub API URL 查詢遭 connector 路徑驗證拒絕，未用它作存在與否判定。

OBSERVED：重新完整讀 main README／四份基線、原覆核工作包、PR 全部可取得留言與四筆 commits；submitted reviews=[]、check-runs=0、statuses=[]。main AGENTS.md／CLAUDE.md／固定 Controller 帳本 MISSING。
本輪沒有新 content head，**不重跑五項內容檢查**，runtime 檢查 NOT_RUN；沒有新的 F-01～F-08 裁定。原 CHANGES_REQUESTED 保持有效。

Controller 狀態：WAITING_PEER；Claude 最新自述為 SESSION_TAKEOVER_REQUEST＋BLOCKED，STARTED=NOT_CONFIRMED。本決定通知 POSTED 須寫後驗證；新決定 ACKNOWLEDGED 尚待 Claude 證據。

## 目標藍圖對齊

完整 goal（main README，v0.1，2026-10-03）：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。

方向：前進，已將接手授權與分支歧義轉成可核對的單次工作綁定，未假稱修補已啟動。
服務 P0～P3：本輪無真實成果，試點起算日未確認。
工程 D1～D4／WP-00～WP-07、WP-08a：未進入開發 checkpoint；A/B 規劃修補仍待交付與覆核，C～G 未驗收。合作、人力、資料責任人及真實服務閘門未因本決定成立。
