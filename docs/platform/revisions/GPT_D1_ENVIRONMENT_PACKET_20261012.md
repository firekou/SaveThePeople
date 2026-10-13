# D1隔離環境驗證工作包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT。
executor Claude；reviewer GPT；next_actor Claude；goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content 9dd0c5d3c9c1293f6995e42f44b4607661631996；base/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012；精確handoff由PR發布回執提供。需source為ancestor、作者readiness檔相同；live不同先HEAD_MISMATCH停止並交差異。不猜最新head。
branch平台已允許claude/tender-allen-c9p5u1，若平台更換依既有交付規則明記新綁定，不force、保留歷史；PR base main但不推main，交付固定SHA到PR1。

## 授權理由與上限
依Frank最新一般技術/安全替代委託，GPT選擇作者建議(a)。這是可逆隔離環境能力驗證；Django＋PostgreSQL技術方向不改，不批准產品功能或真實資料。Docker替代仅此次环境证明，不宣稱Docker验收通过。
deadline 2026-10-12T06:00:00Z；最多45分鐘，成本0、一次交付，repair_round_limit1/used0僅本checkpoint；readiness1/1及N修補3/3歷史保留。必要資源僅既存CPU/磁碟，不申請雲端、付費API或持久服務。
scope_paths：僅新增 docs/platform/revisions/D1_ENVIRONMENT_RESPONSE_20261012.md；允許本任務隔離/tmp目錄放venv、合成DB與煙霧腳本/輸出。excluded：作者既有程式/證據、治理歷史、原始基線、product/.github/deployment/依賴lock等repo實作檔。交付文件可附合成脚本和摘要但不能夾帶Secret/環境變數或無關系統資訊。

## 動作與驗收
1. 先讀最新當責/續作入口、本readiness回覆、BATCH1開工條件、架構。完整claim：work/task/stage/session/source/handoff、scope、開始UTC、deadline45min/0cost、能力、分支、競爭claim與交付位置；沿用session或明示合法接手，不新增平台session。
2. 只在本任務venv安裝Django与psycopg。以venv的pip --isolated跳過帳號設定與環境變數配置，允許標準PyPI套件下載，不改全域Python/系統包、不讀pip帳號或Secret、不傳個案資料；依賴來源/解析版本/hash和實際命令exit保存。不指定未核實最新版；先查現有cache，安裝一次，網路失敗最多一次安全重試且仍在45min內；禁止換不可信鏡像。不得下載Dockerimage或修改daemon。
3. 使用已存在PostgreSQL16執行檔在獨立目錄initdb。先確認既有非root身分能力，不新增OS使用者、不提權、不讀其私檔。若只能root且无法用已授權既有身分執行，立即partial，不能把執行檔存在當DB可用。
4. DB只本任務資料夾、私人Unix socket；listen_addresses空（不開TCP端口），umask077，禁止外部連線、不碰現有DB。安全地啟動，僅使用合成測試值、不接入產品；用腳本建立task限定測試表，插入合成標記，驗證Django資料庫backend可連線與transaction rollback後筆數0。不做產品migration/admin/users或家庭資料。
5. 記python/Django/psycopg/PostgreSQL版本、命令/output/exit，連線/回滾預期與實值。不把import成功當DB成功；負向控制：伺服器停止後連線必須因connection unavailable而失敗，不接受任意SyntaxError充數。
6. finally必定停止本任務DB並確認pg_ctl status為not running；刪本任務DB/socket與可重建暫存，venv可保留在隔離目錄供下一包使用但需位置與容量明載。不得kill無關process或留下永久daemon。交付可重現腳本、正常/負向/cleanup證據与可重建命令。

失敗partial也是有效交付：逐項真實失敗、最小恢復、負責人和可繼續工作；無DB不改SQLite。結論可能BLOCKED_CAPABILITY，不能自行宣告產品READY。
交付目錄/清單：上述唯一response包含claim引用、固定SHA、所有命令/exit/輸出、版本/套件hash、synthetic煙霧腳本、rollback/失聯負向/cleanup結果、未驗證事項。既有PR1一次DELIVERY；作者不自批。next_actor GPT exact-head覆核並依結果具體化D1下一checkpoint。
stop：競爭claim/source不符、新費用/Secret/真實資料/外部服務需求、無安全非root能力、超scope/時間或未知在途動作；cleanup後交partial。恢復需GPT核對具體缺口與限額，不自動追加。無可调用Claude launcher證據，POSTED不是STARTED。
