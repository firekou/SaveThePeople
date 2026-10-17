# R2 修補交付路徑修正｜STP-PLATFORM-PLAN-001

日期：2026-10-05｜Controller：GPT／Codex｜stage：R2_REPAIR。
回應 [2026-10-05T10:28:10Z 能力阻擋](https://github.com/firekou/SaveThePeople/pull/1#issuecomment-5992647350)。

## 決定

本工作包改採 **Claude 在平台已允許的 session 指定分支製作並交付固定成果，PR #1 保留唯一協調與覆核入口**。不要求 Claude 推送受限制的 claude/stp-platform-plan-001，不要求 Frank 重啟舊 session 或放寬平台分支限制。

这是同一三項離線合成修補的交付路徑調整，依既有 Controller 工單／治理授權執行。它取代 GPT_SESSION_TAKEOVER_20261005.md 中本修補「唯一推送分支」與單一指定 session 綁定要求；其他 scope、驗收、期限、資源、一次修補、禁止事項及原裁定完整保留。歷史文件與請求不改寫，main 沒有新增治理制度。

目前回報的平台指定分支為 **claude/tender-allen-lm0coc**；允許既有執行 session 在其平台已允許的此分支工作。若既有已授權喚醒方式下一次提供不同的 session／指定分支，也只允許它在 **本 repo、該 session 自身已允許且在 claim 完整記錄的指定分支** 接續。此條款不授權自行新增 session、觸發機制、任意分支、費用或外部操作。

每次接手都須先檢查全部 PR #1 留言、競爭 claim、已登記結果分支與已用額度／在途動作。**同一修補包只允許一個有效 executor claim 與一條有效成果線**。已有人 claim／工作未對帳時不得另起並行修補。先前未被領取的指定 session 邀請由本調整取代；若發現未知已啟動工作，停止交 GPT 對帳。

Claude 請求未提供 exact session ID，這欄目前 UNKNOWN；claim 必須補上真實 ID，不可用「本次喚醒」代替。公開時間線未見有效修補 claim 或修補 commit；未開工、外部0與支出0仍為作者 REPORTED，不證明隱藏環境未執行。

## 工作包沿用與版本

- work_id：STP-PLATFORM-PLAN-001。
- task_id：STP-PLATFORM-PLAN-001-R2-GPT-REPAIR-20261005。
- goal：關閉 F-01／F-03／F-07，取得 A/B 層規劃與參考檢查批准。
- executor：符合上述接手條件並完成 claim 的 Claude；reviewer：未參與修補製作的 GPT。
- source content head：c1d56496bb210518314254b88d9c8b52e56408d9。
- base／origin/main／PR #1 base：9a7bd1295e20837786acc45bdab7fb94f5a1b012／main。
- 本調整寫前 review_record head：057f156f5011af590b7ec16758208f2551b3273a；本調整寫後 exact head 由 PR 通知與遠端核對記錄，正文不要求自身 SHA。
- scope_paths／excluded_paths：完整沿用 [固定修補包](https://github.com/firekou/SaveThePeople/blob/ce10895c121682797881e9f9d374f6ffdeeaa3e9/docs/platform/revisions/GPT_REVIEW_R2_20261005.md)；僅三項必要 docs/platform 文件／schema／JSON／examples／tools／R2_REPAIR_RESPONSE，禁止增權、改四份基線、改作者歷史與 reviewer 紀錄、產品／部署或無關重構。
- deadline：**2026-10-06T08:00:00Z**。
- 資源上限：本修補包合計90分鐘實際 Agent 離線合成投入、外部成本0；不因 session／分支变化重置。
- repair_round_limit：1；used：目前作者 REPORTED=0，執行前對帳；歷史累計 NOT_DEFINED。
- 資料與環境：僅標示合成資料、隔離本機 checkout；不讀真實家庭資料，不使用外部 AI、部署、通知或申請。

## 領取、執行與交付

1. 重新 fetch origin/main、PR #1 分支及已登記結果分支。先確認 main SHA；PR #1 最新 head 相對 source 僅含已核對 reviewer/controller-only 追加文件。未知內容差異或 HEAD_MISMATCH 停止，不能默默改審最新內容。
2. 核對平台指定分支與存取能力。只將已確認的 PR #1 候選歷史接到平台允許的本 session 本機分支；不要在 main 空樹上重做或丟失原規劃。保留祖先與原作者歷史；不 force、不覆寫未知既有遠端分支。如果平台連本機準備／指定分支推送也禁止，停止並回報實際限制，不繞過。
3. PR #1 追加 claim：work/task、exact session ID、指定結果分支、source/base/review_record SHA、引用原交付／阻擋／本決定、scope、開始 UTC、原 deadline／資源上限及已用量、能力、無競爭 claim／未知在途動作核對、交付位置。有效 claim 後才執行；不得先做後補。
4. 只修 F-01／F-03／F-07。先審查原腳本／依賴，執行原定五項命令與指定負向控制、合法控制、四份基線 diff；逐項保留 command、stdout/stderr、exit、fixed SHA，不複製作者歷史數字當新結果。
5. 在平台允許的 claim 分支 non-force 推送固定成果，遠端讀回 exact SHA 與內容後，將 **結果分支、固定新 content/result SHA、完整 compare／commit 連結、R2_REPAIR_RESPONSE.md exact-head 連結與證據** 交回 PR #1。不用另建空 PR；PR #1 維持 Draft。本路徑交付可供覆核，但**PR #1 本身的 head 不會因此等於結果 SHA**。
6. GPT 依已登記結果分支與 claim／交付固定 SHA 核對 live result ref；相同才覆核此一新內容 head。差異以最後已審 content 與初始 result base 分層核對，reviewer-only 文件不重跑內容。結果不是 PR #1 head 的情形明記，不作虚假 HEAD_MATCH。
7. 結果覆核通過後，另核對整合／合併授權與平台能力；**本文件不授權 merge、跨分支推送整合、部署或產品開工**。不能因交付路徑可用就宣布主線已採用修補。

stop/resume：原 deadline／90分鐘／一次修補、scope、競爭 claim、版本與資料界線全部沿用。超額或新權限才交 Frank 決策，不以新 work_id／分支重置。
next_actor：Claude；next_action：能力與競爭核對 → 新 session claim → 同一修補 → 指定分支固定成果交 PR #1。
next checkpoint：修補 READY_FOR_REVIEW，未進入開發或主線整合 checkpoint。

## 本輪核對

實際 `git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001` exit0；`git -C stp-review rev-parse origin/main origin/claude/stp-platform-plan-001` exit0，輸出為上列 main 與057f156f5011af590b7ec16758208f2551b3273a。
`git -C stp-review diff --name-status 057f156f5011af590b7ec16758208f2551b3273a origin/claude/stp-platform-plan-001` exit0、空輸出。
`git -C stp-review ls-remote origin refs/heads/claude/tender-allen-lm0coc` exit0、空輸出：當時未見該遠端 ref，不是推送能力證明。
完整重讀 main 五份基線與本輪治理工作包／全部四則 PR 留言；五筆 commits／parents 以 API 核對。submitted reviews=[]、check-runs=0。本輪沒有新內容 head，內容 runtime 檢查 NOT_RUN；CHANGES_REQUESTED／F-01、F-03、F-07保持未關閉。
先前接手決定已由 Claude 明確引用，ACKNOWLEDGED；修補 STARTED=NOT_CONFIRMED。本新調整的 ACKNOWLEDGED 待執行端回應。
工具無平台 session 設定操作能力，但仍可在已允許分支交付同scope工作，故未將全部 Controller 工作判為完全阻塞。

## 藍圖

goal（main README v0.1，2026-10-03）：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。

方向：前進，解除「交付必須推到受限制分支」的工單障礙，是否實際可執行仍待 claim 證據。
P0～P3 無新增真實服務成果；D1～D4／WP-00～WP-07、WP-08a未開工。規劃修補與產品／真實服務／實際取得各層分開，合作、人力、啟用閘門仍未因本調整成立。
