# D1環境與啟動條件核對工作包
status READY；此包只授權readiness核對與證據整理，不授權產品開發、main merge、部署或真實使用者輸入。
work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-READINESS；stage D1_READINESS；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1，2026-10-03）
本checkpoint輸出：核對可實際運行D1的最低環境，對BATCH1 §1六條件提供證據與缺口；GPT將已備妥的D1目錄/詳情提案化成下一有界執行包，不能無期限停在規劃。
source_content ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9；base origin/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012；candidate整合治理handoff SHA由發布comment指定，該SHA需有source為ancestor，作者22檔與source一致。source不符HEAD_MISMATCH停止、不換審。
工作分支：平台已允許分支，claim明載；從固定整合handoff non-force接續，保留雙parent與作者歷史；交付至既有PR #1協調，main不推送。

## 限制
- deadline 2026-10-12T06:00:00Z；最多45分鐘、外部成本0、一次交付。超限交partial，不自動追加；這是新readiness checkpoint，不重置N修補3/3歷史。
- 資料合成；環境只本任務checkout/隔離目錄。無Secrets、真實資料、對外聯絡/通知/申請、雲端、付費API、外部AI、session/排程或公開展示。
- scope：只新增 docs/platform/revisions/D1_READINESS_RESPONSE_20261012.md；允許隔離暫存診斷，不修改作者程式、治理歷史、README、原始基線、依賴/lock或部署檔。
- 必要讀：BATCH1_EXECUTION_PACK §1/2/3，BUILD_PLAN_AND_ACCEPTANCE §2/5，ARCHITECTURE §3/5，SYNTHETIC_WEBSITE_START_DECISION_20261010.md，最新CONTINUATION_STATUS/當責規則。

## 動作與驗收
1. 核對GitHub存取、唯一claim/source/candidate、平台允許分支；記實際命令exit與完整SHA。
2. 只做工具能力診斷：`python3 --version`、`docker --version`、`docker compose version`、`psql --version`，以Python import檢查Django是否已存在；不存在如實NOT_AVAILABLE，不安裝、不讀環境變數或帳號Secret。
3. Docker若可用可用`docker info --format '{{.ServerVersion}}'`確認daemon；不得列無關容器/專案、拉image或啟動新服務。診斷無法執行記stderr/exit，不能憑已安裝cli宣稱可啟動。
4. 六個gate逐項：獨立規劃批准範圍（N修補A/B批准非全產品）、本小包Claude/GPT責任配置（非真人工程到任）、推薦stack與實際可用環境、synthetic_resources標示與數量/狀態、repo分支規則。對任何仍要求明確產品開工的權限欄位記UNKNOWN/NOT_AUTHORIZED與來源；不能自己把PREPARED改READY產品包。
5. D1可見成果沿6項合成目錄/詳情、360px、來源/日期/有效狀態/空列表規格；提出本地實作的最小下一包（scope、命令、負向控制、時間與0成本）作為建議，不實作產品。
6. 失敗歸因到環境/權限/未決條件，列不受阻工作與最小恢復操作；只有帳號持有人操作才交Frank，不要求搬運Prompt。Docker不足可建議既存隔離runtime替代，但不得自行改PostgreSQL→SQLite或聲稱DB已驗證。

交付：固定新SHA、分支、claim、逐gate結果與實際command/output/exit至PR #1；AUTHOR_EVIDENCE不自批。next_actor GPT核對後作有限技術/續作決策；這不是再要求Frank例行批准。
claim必填 work/task/stage/session/source/handoff、scope、UTC開始與deadline、45min/0cost、能力、唯一分支與競爭claim、交付位置。新session保留原歷史追加綁定，不新增平台session或冒充原session。
stop：來源不符、競爭claim、未知在途操作、新費用/真實資料/Secret需求、超scope或期限；先交partial與具體缺口。恢復由GPT核對差異/資源，無自動重置。
