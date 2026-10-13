# D1_ENVIRONMENT repair3 最後一次有界修補
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content8920a79d71eccfdac9ab9ed0cb06cefb5a4513ab；base/main9a7bd1295e20837786acc45bdab7fb94f5a1b012；exact handoff由PR通知提供；source為ancestor且原response843行bytes不改。mismatch/競爭claim停，不能猜最新head。
分支claude/tender-allen-c9p5u1、PR1/base main；沿用合法session，接手另記來源與對帳；先核對claims後追加完整claim（work/task/stage/session/source/handoff/scope/開始UTC/限額/能力/交付位置）。non-force，不push main。

## 明確決策與範圍
GPT按Frank有限技術續作委託增repair_round_limit2→3、repair_rounds_used2保留，本次最後3/3；額外15分鐘、一次交付、外部成本0；exact UTC deadline2026-10-12T06:00:00Z不變。initial1/1、readiness1/1、N3/3不清除。沒有第四輪預授權；再次失敗不續修此腳本，安全停留並交替代方案。
scope_paths僅docs/platform/revisions/D1_ENVIRONMENT_RESPONSE_20261012.md末尾追加repair3；原843行、作者其他程式/測試/證據/GPT治理/四基線不改。隔離tmp標準函式庫/bash合成stub與既存venv/wheelhouse/私人socketPG16允許。excluded產品/.github/依賴lock/二進位/部署/外部AI/真實個案。
禁止新下載/網頁查核/外部API/鏡像/全域包/OS新user/提權/Docker/cloud/session/費用/Secret/真實資料；缺既存runtime交partial，不換SQLite或重建下載。既有下載偏差保持原文。

## 最小動作與驗收
1. 同ENV-01修freeze/程序查詢錯誤：捕原命令exit，通過後才sort或count；pgrep0/1與>=2分開，只有1代表已成功查到無process。查詢錯誤（含127工具缺失）不得視為0程序、不得刪pgdata/socket/log，exit9/partial。檢查ss/ownership等關鍵命令亦需實際exit通過，不把空輸出當成功；如果不用ss，採明確可證明的無TCP控制，不能默默省略。
2. 正常與cleanup共享stop_attempts，每task總最多2次（正常fast一次+cleanup補一次；inject未正常stop時亦總2），額度用完仍未確認停止則保留資料、exit9，不kill無關process。所有fault原因/原exit與cleanup結果分開，不能覆蓋第一失敗。
3. 新獨立合成fault至少：freeze印合法清單但exit1；pgrep2與127；pgrep1真無程序；ss查詢錯誤或替代核對失敗；stop持續失敗且總呼叫不得超2。預期前者非0、查詢/停止不明exit9且保留。原17項genuine0/注入7/負向5拒絕/stop保留/initdb/config/start/install/version/hash拒絕全保留，expected/actual/原因全部稽核；不是任意失敗充數。
4. 實際既存PG正常與煙霧注入兩路，失聯負向與cleanup記command/output/exit。沒有工具就明記NOT_RUN/partial，不以stub升級runtime。交完整v3/fixture腳本正文或可重建獨立命令、位置與保留容量；private/socket與is_synthetic=true維持；不跑產品migration/HTTP。
5. 五必要命令：python3 docs/platform/examples/check_examples.py；python3 docs/platform/tools/gen_state_machines.py --check；python3 docs/platform/tools/gen_permissions.py --check；python3 docs/platform/tools/test_checks.py；python3 docs/platform/tools/check_docs.py。四基線git diff base到result空、原843行不變/只append；全SHA、命令/輸出/exit交回PR1一次DELIVERY。結果標AUTHOR_EVIDENCE，GPT覆核。
stop_conditions：source/claim不符、scope/15min/deadline超限、新權限/費用/外部依賴；先安全cleanup，未確認停止不得刪，交partial/資源位置/最小恢復；無限重試禁止。不追加第四輪或新ID重置。next_actor GPT exact-head覆核，通過再具體化D1開工條件；不是產品/main merge/部署/真實資料授權。POSTED非ACK/STARTED，沒有launcher證據，不要求Frank搬運。
