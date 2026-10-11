# GPT決策與N-03第二輪有效修補工單
決策日期：2026-10-12 Asia/Taipei。狀態 READY。
## 授權與判斷
Frank於本次對話明確將本事項決策交給GPT，要求GPT負責決策與續作，取消把本技術修補輪次例外交回Frank。GPT據此批准以下有界修補。
理由：N-03有獨立重現、影響已承諾用途撤回的還原完整性；修法已界定，僅離線合成模擬、零外部成本，適合Controller直接承擔。歷史BLOCKED_FRANK_DECISION保留，但已被本決策解除。
此決策適用本修補；其他下一步由GPT先核對既有授權、依賴與風險後決定，不把一般技術判斷推回Frank。不能據此宣稱新增部署、真實資料、支出或外部通知已獲授權。

## 工單
- work_id: STP-PLATFORM-PLAN-001
- task_id: STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP
- stage: R2_N_FOLLOWUP
- revision: 2
- source_content: 7bd0c69705bfda2562a81f7fa751be0e21a4981b
- base: 9a7bd1295e20837786acc45bdab7fb94f5a1b012
- review_source: 51677b8a6b0edf3d1f807c2f9021594208169137 的 GPT_N_FOLLOWUP_REVIEW_7BD0C69_20261010.md
- executor Claude; independent reviewer GPT
- repair_round_limit: 2; repair_rounds_used: 1; 本次round: 2
- deadline: 2026-10-12T18:30:00Z（台灣10/13 02:30），不變
- additional_time_cap: 30分鐘，含自檢；external_cost_cap: 0
- 舊90分鐘與第一輪交付歷史保留；舊F包不重開、不清除已用額度。
- result_branch: 優先沿用claude/tender-allen-sko8pq；若平台強制新分支，允許本repo平台指定結果分支，claim列明實際名稱並保留source祖先。禁止推main或PR候選分支，non-force。
- evidence: 新增 docs/platform/revisions/R2_N_FOLLOWUP_ROUND2_RESPONSE.md；PR #1交付固定result SHA與實際命令輸出。
- next_actor: Claude
- next_action: 核對live工單、唯一claim與結果，接續僅N-03修補；交付後GPT exact-head獨立覆核，不需Frank提供驗證Prompt。

## 範圍
只限 docs/platform/OPERATIONS_AND_PRIVACY.md、ARCHITECTURE.md必要順序文字、examples/ref_control.py、examples/control_cases.json、examples/check_examples.py、tools/test_checks.py、新第二輪回覆。
排除README、四份原始基線、權限放寬、既有作者回覆與Reviewer歷史、治理工單、產品、部署、Secret、真實資料、外部聯絡。

## N-03根因與最小修法
seq確認而hash補記可失敗，還原只比對存在的hash，缺錨仍放行。合法撤回REMINDERS及REFERRAL_SHARE、主庫失敗後，注入hash補記失敗，縮減用途並重算合法鏈，可使還原quarantined=false且轉介仍SENT。另Witness.report TimeoutError未轉503。
確認必須綁定seq及控制內容hash，或以持久pending令未完成hash確認在還原時一律隔離。不能以只驗已存在hash保護全部內容。清楚定義主庫套用及200/202前的持久確認；timeout回未確認503。文件、模擬與案例同步。保留其他已關閉N項。

## 驗收
自行使用合法新payload重現，不靠schema422通過。包含同步200、主庫失敗202與重套、未flush、timeout、hash確認失敗、尾端遺失、缺錨後改寫、合法重試、REDACT與HARD_DELETE；逐項核對正確拒絕或隔離原因。合法控制亦須通過；移除防護的mutation須被抓到。
repo根目錄執行並附stdout、stderr、exit：
python3 docs/platform/examples/check_examples.py
python3 docs/platform/tools/gen_state_machines.py --check
python3 docs/platform/tools/check_docs.py
python3 docs/platform/tools/gen_permissions.py --check
python3 docs/platform/tools/test_checks.py
git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
最後diff必空。證據僅AUTHOR_EVIDENCE，不能自行APPROVED或稱產品/DB/備份整合驗收。

## 接手及停止
沿用原task及claim歷史；新session可追加接手聲明，不冒充原session、不重置次數，核對無競爭或在途成果後直接執行，不需再等同一授權確認。
到期、30分鐘超限、需scope外變更或未知競爭成果時保留PARTIAL交GPT；GPT負責判斷最小下一步，不靜默等待Frank、不自動無限重試。
只有既有接收方式；GitHub POSTED不等於Claude STARTED。沒有callable launcher就如實記錄，不新增付費API、永久排程或session。
通過後GPT接續候選整合與網站D1開工條件核對，準備並決定授權內下一checkpoint，不再產生泛泛報告。
