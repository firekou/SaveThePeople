# SaveThePeople 唯一續作入口
更新：2026-10-10 Asia/Singapore。work_id STP-PLATFORM-PLAN-001。
本入口是此次建立的最小協調文件，不宣稱main已有Controller帳本；位於PR #1候選，main四份基線不變。

## 有效狀態
- goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。
- source_main：9a7bd1295e20837786acc45bdab7fb94f5a1b012。
- source_content：02935f528b42a35b3a793d1dec370a5091691288。
- reviewed_content：7bd0c69705bfda2562a81f7fa751be0e21a4981b（claude/tender-allen-sko8pq，已fetch及獨立重現）。
- work_packet：R2_N_FOLLOWUP_WORK_PACKET_20261010.md revision1，handoff599a25b8882a5a4671d79443670364f127202a9c。
- verdict：CHANGES_REQUESTED；N-01保持關閉，N-02/N-04/N-05/N-06本缺口A/B關閉，N-03仍OPEN（hash補記失敗後重寫可放行；timeout未轉503）。舊局部F批准保留。
- stage：R2_N_FOLLOWUP；status：BLOCKED_FRANK_DECISION。一次交付已用1/1，不自动派第二輪；deadline2026-10-12T18:30:00Z不變。
- next_actor：Frank；next_action：決定是否增加一次僅N-03修補交付，額外最多30分鐘、外部成本0、同task/stage且保留已用次數；具體決策包見下述獨立覆核報告。未授權前Claude不續修。
- owner_needed_now_for_repair：是，僅修補輪次例外，不需重寫Prompt或搬運報告。
- website_start：NOT_AUTHORIZED；本輪不整合Claude成果、不merge main、不開工、不部署。
- latest_review：[GPT_N_FOLLOWUP_REVIEW_7BD0C69_20261010.md](GPT_N_FOLLOWUP_REVIEW_7BD0C69_20261010.md)，含全部命令、反例與可審閱最小決策包。
- review_record_head：由PR通知提交回執提供；merge_candidate_head：未建立本輪新候選。過往本機候選僅歷史準備，不代表已發布。
- claim/交付：issuecomment-6086870316／6086976385；session_01XocTQm3iUWNbtArN7PpZTV；ACKNOWLEDGED、DELIVERED已觀察；作者約10分鐘REPORTED，成果已獨立驗證，非永久launcher驗證。

## 唯一工單與證據
[有效工作包](R2_N_FOLLOWUP_WORK_PACKET_20261010.md)取代歷史準備稿。
[剩餘缺口核對](GPT_R2_RECONCILIATION_20261007.md)與[Reviewer反例](reconcile_probe_20261007.py)。
[第一網站開工決策](SYNTHETIC_WEBSITE_START_DECISION_20261010.md)。
舊F包期限2026-10-06T08:00Z、一次修補已使用且結案，不續期。本N包deadline2026-10-12T18:30Z、90分鐘、一次交付、外部成本0，旧額度不清除。

## 交接能力
現有GPT排程已觀察enabled、每小時，最近查到last_run_time=2026-10-09T18:01:56Z；不是成功派工證明，未更改排程。
曾有Claude claim→固定成果→Reviewer的單輪往返，尚不能證明永久自動喚醒。当前工具没有可调用Claude launcher；本輪只發GitHub通知，不冒稱已啟動。
POSTED/ACKNOWLEDGED/STARTED/DELIVERED分别記錄。只用既存授權方式，不新增session/付費API/永久排程。
下次排程固定讀PR #1最新有效此入口与全部新留言，不能只讀旧「等Frank」報告而忽略後續指示。若尚無ACK，明記WAITING_PEER；最晚2026-10-11T18:30Z仍無接單則記BLOCKED_CAPABILITY（不是自動重發/重置），提供现有Claude接收端讀本包的最小恢復動作。只有有新狀態才通知，避免每小時重複。
Frank已有可貼給Claude的執行Prompt；不要求其搬運覆核。平台未證明launcher可用，不宣稱背景自主修補。

## 續作規則
新claim核對唯一source/scope/額度與平台允許分支；換session可接手但不重置額度。
固定結果→GPT exact-head覆核→通過後核對候選整合與D1啟動條件。Reviewer不改作者實作或自批。
無新內容可以去重，但必須先查未送工單、未回寫結果或失敗通知；不得把本機完成當遠端交付。
成果層次：文件/參考模擬已有；產品/DB/合成網站E2E/真實服務/取得成果均未驗收。服務P0～P3無新增證據，工程D1～D4未開始。

## 歷史執行端缺包回報（已由新claim/交付解決）
Claude於2026-10-09T18:20Z回報PACKET_NOT_AVAILABLE（issuecomment-6086760059），已核對GitHub但未claim／修改／push。平台分支ccr-dd86219c-ijac1h可交付（dry-run屬作者證據，非已推送）。本次遠端包補齊缺欄位，task_id=STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP；不要求修補先等候選整合授權。這是收到舊缺包回報與回填，不是Claude已讀新包。其無自動輪詢／本次無可用launcher，next_actor仍Claude，下次喚醒讀固定新工單。

## 本次覆核與續作
2026-10-10 GPT已完成固定7bd0c697覆核；5工具exit0、4基線diff空，但獨立反例仍發現N-03。只回寫Reviewer與治理；作者檔案不改。沒有新授權／新固定成果則去重，不重跑、不留言。Claude交付已到，不能再把舊PACKET_NOT_AVAILABLE當当前阻擋。批准輪次例外後再核發最小工單；尚未批准則本checkpoint不能COMPLETE。

## 前一版有效狀態歷史（已被上方更新取代）
2026-10-10 工單派送時狀態
- goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。
- source_main：9a7bd1295e20837786acc45bdab7fb94f5a1b012。
- reviewed_content：02935f528b42a35b3a793d1dec370a5091691288。
- local_merge_candidate_content：50d2c56ac1e223dc2afdfe50f17e4ffb9fea6c75（保留原Claude与Reviewer祖先；未推送，遠端候選尚未包含12檔修補）。
- local_review_record：27f575518e77b97807d7b746c03434265baef2d3。命令列push缺登入失敗，改由GitHub connector只回寫治理文件；遠端handoff exact SHA見PR通知。source_content保持02935f5，不把本機commit當遠端起點。
- verdict：CHANGES_REQUESTED（N-01已解；N-02～05未解；N-06部分解）。局部F修補批准保留，不能推成所有缺口關閉。
- stage：R2_N_FOLLOWUP；status：READY（工作包已具體化，遠端可讀與POSTED由通知回執確認）。
- next_actor：Claude；next_action：依唯一工作包接單修補；没有claim/STARTED不稱EXECUTING。
- owner_needed_now_for_repair：否；不要求Frank重寫驗證Prompt或回舊session。
- website_start：NOT_AUTHORIZED，開工提案已備；不阻擋修補。

