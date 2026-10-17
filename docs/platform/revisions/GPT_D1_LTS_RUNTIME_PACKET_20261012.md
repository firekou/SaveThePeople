# D1 LTS 版本實檔與隔離runtime驗證工作包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-LTS-RUNTIME；stage D1_LTS_RUNTIME；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content0622fbf1035c6d9fa1375f7d122ebb1c218d7e83；base/main9a7bd1295e20837786acc45bdab7fb94f5a1b012；exact handoff由PR回執提供；source ancestor/兩份原response bytes相同，不符HEAD_MISMATCH先停。分支claude/tender-allen-c9p5u1、PR1/base main、non-force、不push main；沿合法session，claim核對競爭與在途動作，完整work/task/stage/session/source/handoff/scope/開始UTC/deadline/限額/能力/交付位置後執行。

## GPT決策與範圍
採Django5.2.18 LTS，官方download/FAQ/database及PyPI metadata已由GPT獨立核對，見本輪review；Python3.13/PG16/psycopg3.3.6最低條件符合，但新版本runtime未驗。
scope_paths僅新增docs/platform/revisions/D1_LTS_RUNTIME_RESPONSE_20261012.md；隔離/tmp新增LTS venv、wheel與合成DB/script允許；excluded作者原程式/測試/證據、治理歷史、四基線、產品/.github/lock/二進位/部署檔。不要改環境原1286行或stack142行，引用歷史與新版本差異分開。
exact UTC deadline2026-10-12T06:00:00Z；30分鐘、成本0、一次交付、repair_round_limit0/used0；stackdelivery1/1、環境repair3/3、readiness1/1、N3/3保留。這是LTS版本相容性驗證，不是第四輪編排修補，不改其控制流程/安全邊界。
只允許標準PyPI/其官方files.pythonhosted.org下載django-5.2.18-py3-none-any.whl（8316071 bytes，SHA25692ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c）；不解析/下載任何其他套件/版本，不改鏡像、不讀pip配置/Secret。最多一次download、僅暫時網路錯誤可加一次同請求重試；全部attempt記錄/累計，不因更改PATH重置。Python/已有依賴preflight先過，不過不得下載。官方出口政策拒絕不重試或繞過，partial交回。
禁止全域install/OS新user/提權/Docker/cloud/費用/session/外部AI/真實資料/通知/申請/main merge/部署/產品HTTP或migration；不建立永久服務。

## 動作與驗收
1. 檢查既存taskPython3.13、4依賴wheelhouse、PG16及既存非root降權能力；無則partial，不重建下載其他套件，不用SQLite。隔離新LTS task目錄umask077，不覆寫原venv/歷史。
2. 使用venv pip完整路徑--isolated、--no-deps下載指定wheel；確認檔名/大小/SHA256，任一不符停止且不install。用新taskvenv從該wheel與原4依賴wheel離線--no-index/--no-deps安裝，版本/freeze/import輸出與原exit核對。不得把metadatahash當實檔hash。
3. 僅隔離腳本副本更新PINS/EXPECT_FREEZE與新wheelhouse清單、task路徑；其餘v3控制流程不改。此新LTS脚本與差異交正文；pgrep查詢失敗保留、總stop≤2、空listen/private socket0700/非root/is_synthetic=true沿用。必要公共CA按既有合法方式處理不讀私鑰/列env，完成刪CA。
4. Django5.2.18→psycopg3.3.6→PG16實際正常路，transaction內1/rollback0/commit1/全synthetic；停止後指定socket unavailable負向；注入煙霧7與cleanup證據，均記實際command/output/exit/版本。finally停止確認status3/程序查詢成功無process才刪DB/socket/log；查詢/停止不明保留且partial，不kill無關process、不無限retry。
5. 必要5命令：python3 docs/platform/examples/check_examples.py；python3 docs/platform/tools/gen_state_machines.py --check；python3 docs/platform/tools/gen_permissions.py --check；python3 docs/platform/tools/test_checks.py；python3 docs/platform/tools/check_docs.py。base四基線diff空、僅新response；作者runtime與mock分開，列原文未改/保留路徑容量/下載attempt。一次固定result SHA交PR1，不自批。
stop：mismatch/競爭claim/超scope/30min/deadline、新權限/費用/套件/外部依賴/資料/政策拒絕，安全cleanup或保留交partial/最小恢复；無自動修補或下載替代版本。next_actor GPT exact-head覆核，再核對D1-A六條件與產品開工授權；本包不能讓PREPARED自動生效。POSTED非ACK/STARTED，無launcher，不要求Frank搬運。
