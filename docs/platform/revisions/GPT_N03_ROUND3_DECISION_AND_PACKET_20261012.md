# GPT N-03 第三輪決策與最小修補包

本文件依 Frank 2026-10-12 最新指示與 GPT_ACCOUNTABILITY_AND_PROGRESS_20261012.md，由 GPT 做一般技術與有限續作決策。只提高既有 N-03 task 的一次有界修補額度，不批准成果、產品開工、merge、部署或真實資料。

- work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP；stage R2_N_FOLLOWUP；work_packet revision 3；status READY。
- goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main README / 四份基線 v0.1，2026-10-03）
- 本checkpoint：只消除 N-03 缺錨記錄由下一請求補記及 APPLIED 偽裝導致的還原放行。finding原ID不變。
- executor Claude；reviewer GPT（未參與製作）。next_actor Claude；next_action 核對唯一claim/source/額度後追加claim，僅修本缺口，固定SHA交PR #1；delivery後next_actor GPT做exact-head覆核。
- source/base：content c563865173a402c71af4c2b3ad3c46edac771200；origin/main / PR base main @ 9a7bd1295e20837786acc45bdab7fb94f5a1b012；review record起點 PR #1 claude/stp-platform-plan-001 @ 41ef99ad5384005ec4f6d0adfd0de631f7cc0e7d（治理寫入後以交接comment給固定handoff SHA）。result != PR候選，不自行merge。
- 工作分支：沿 claude/tender-allen-c9p5u1 若本session有權；平台強制其他分支可於claim明載唯一分支，從source保留祖先、non-force，仍交PR #1協調，不推main/候選、不開空PR。
- repair_round_limit **3**（歷史1→2保留，本次GPT依最新明確委託增加一次）；repair_rounds_used **2**；本次 **3/3**。不同session不得重置。歷史F包不重开。
- deadline **2026-10-12T18:30:00Z**（不延長）；本次額外上限 **30分鐘、0外部成本、一次固定成果交付**。round1約10分鐘、round2約25分鐘均作者REPORTED；不可把agent次數當人日。超上限停止，交已用時間與partial證據，不自動第四輪。
- 資料與環境：只合成、隔離離線參考模擬；實際新增fixture標 is_synthetic=true。不得真實個案、Secret、外部AI、政策重搜、對外聯繫、通知/申請、雲端/部署/付費啟動/新增session或排程。
- scope_paths：docs/platform/examples/ref_control.py、control_cases.json、check_examples.py；docs/platform/tools/test_checks.py；docs/platform/OPERATIONS_AND_PRIVACY.md §1.3.3、ARCHITECTURE.md 撤回寫入順序必要文字；新增 docs/platform/revisions/R2_N_FOLLOWUP_ROUND3_RESPONSE.md。
- excluded_paths：README、四份main原始基線、permissions/state_machines、既有Claude/GPT證據與歷史、其他規劃重寫、產品與部署路徑。

## 已驗證根因與最小修法
讀 GPT_N03_ROUND2_REVIEW_C563865_20261012.md 的逐行位置、探針原碼與實際輸出。N-03兩條OPEN：缺錨點→縮減用途重算鏈→另一合法HARD_DELETE→還原放行；缺錨點→改APPLIED/ref0重算→直接還原放行。不是timeout問題重開。
推荐：在可信見證/獨立pending狀態將seq與原始完整envelope hash不可覆寫綁定，後續確認與重試只可比對該原始綁定；type/APPLIED ref也包含其中。絕不可從可能被改寫的log自動建立原始可信錨點。若30分鐘内無法安全建構，可以採缺錨點不自動解除、受控恢復需可信原始證據的保守方案，將恢復流程與限制寫清楚，正常無故障控制仍工作。

## Acceptance / 負向與正向控制
1. 缺錨縮減用途→無關合法新請求→recover仍隔離；不能用無關422或uncaught exception充數。記預期與實際reason、見證、log、主庫、轉介結果。
2. 缺錨偽裝APPLIED及錯誤ref不能繞過原始意圖綁定／有效關聯；重算完整鏈亦拒絕。
3. 若支援自動合法重試，證明只重試可信原始完整用途，重啟caller亦不能丟失pending；若保守禁止，明確reason和受控恢復前提，不能把盲目補錨稱恢復。
4. 正常200完整撤回、已錨定DB失敗202可重套且r1 CANCELLED、seq/hash逾時503且主庫不變、尾端遺失隔離、HARD_DELETE不存在与REDACT列保留遮蔽全部保留。
5. 移除原始綁定/缺錨停止保護的人為破壞須由上述組合情境抓到；移除後放行是明確預期失败原因。
6. 不弱化既有安全預期；如果合法重試语意因選擇保守策略調整，逐項列理由、測試與受控恢復條件，由GPT獨立審，不悄悄改成任意失敗即可通過。

必要命令：先審腳本/依賴，在隔離副本執行，記command、exit、stdout、stderr、exact SHA：
```sh
python3 docs/platform/examples/check_examples.py
python3 docs/platform/tools/gen_state_machines.py --check
python3 docs/platform/tools/gen_permissions.py --check
python3 docs/platform/tools/test_checks.py
python3 docs/platform/tools/check_docs.py
git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
```

證據位置：R2_N_FOLLOWUP_ROUND3_RESPONSE.md（AUTHOR_EVIDENCE），含兩條攻擊與正向/破壞測試、所選恢復策略、未證明項、時間成本、變更清單，及PR #1 DELIVERY固定完整SHA/分支/claim連結。作者不得寫GPT批准；純邏輯不是DB備份整合或法律驗證。

claim：work/task/stage/round、session、source SHA、handoff SHA、scope、開始UTC、deadline/30min/0cost、能力、branch、交付位置、競爭claim/歷史資源對帳。沿原claim歷史追加新session綁定，不冒充舊session；未知在途動作先對帳。
停止：source不等本SHA→HEAD_MISMATCH，不改審新head；競爭claim、scope/期限/時間超限、費用/真實資料需求、工具無能力→停止並具體回報。恢復：GPT核對差異/唯一責任/可用資源，限定一次本輪，不重新開始计數。

next_checkpoint：本成果exact-head獨立覆核；通過才具體化候選整合及D1本地合成資源目錄/詳情的啟動條件。不依此包宣稱已授權開發或已服務家庭。
通知：GitHub POSTED不等Claude ACK/STARTED；未有可调用launcher證據。先使用既存授權接收途徑讀本包，2小時無ACK做能力根因核對，不重複空通知或要求Frank搬運Prompt。只有帳號持有人操作才交Frank。
