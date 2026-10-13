# D1_ENVIRONMENT repair2 有界決策及工作包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content867ba5eccd3b1cc13542d22c471ee7413dee89fc；base/main9a7bd1295e20837786acc45bdab7fb94f5a1b012；exact handoff由PR通知提供。source須為ancestor、原response全部466行逐位元不改；mismatch先停，不擅改審最新。
工作分支claude/tender-allen-c9p5u1，PR1/base main；既有session可沿用，競爭claim先核對。追加claim含work/task/stage/session/source/handoff、scope、開始UTC/能力/限額/交付位置；non-force，不能推main。

## 理由、範圍與額度
GPT依Frank一般技術/有限續作委託明確增限1→2、used1保留、本次repair2/2；initial delivery1/1、readiness1/1、N3/3保留。兩條ENV-01假成功已獨立重現；只修控制流程，不重新規劃整份產品。額外20分鐘、成本0、一次固定交付；deadline2026-10-12T06:00:00Z不延長。無第三輪預授權。
scope僅response末尾追加repair2；原466行與其他作者/Reviewer證據/原始基線不改。允許隔離/tmp腳本/stub/既存venv/私人socket合成PG16測試；禁止新增repo產品/lock/二進位/部署/.github等。
禁止任何新外部下載/API/網頁查核/鏡像、全域包/Docker/OS新使用者/提權/cloud/費用/session/Secret/真實資料。只用既存task venv/wheelhouse與PG16；缺失即partial，不追加下載或改SQLite。上轮下載超限只記偏差，不追認合規，不重置attempt。

## 修法與验收
1. 同ENV-01修編排錯誤傳播：preflight固定Python/版本/既存artifact與依賴；離線安裝/驗版本、mkdir/initdb/config寫入/讀回/start/positive/stop/status/down每一步需依exit和預期值裁定，不能只echo或用最後cleanup覆蓋。scope無產品。
2. cleanup保留主錯誤、記cleanup失敗；只有確定本task server已停止（status3、task process/socket核對）後才刪pgdata/socket/log。stop失敗/status0或未知時不得刪，不宣稱成功；保留受限task目錄並BLOCKED_CAPABILITY/partial。不得kill無關process；不得重試無限。正常stop最多一次、cleanup必要補一次只限本task，兩次仍失敗立即保留/交partial。
3. 正常實際PG路0；煙霧注入exit7仍清理正常；停止負向只指定socket不存在及正確connection unavailable，down失敗必傳非0。原ENV-02函式與ENV-03清單不重寫，可在新段引用，不重下載。
4. 隔離stub反例至少：down5、stop1/status0（不可刪）、initdb1、config寫失敗/讀回不符、start1、離線install1或版本不符；全部非0且命中正確原因。genuine正常0、煙霧注入7與cleanup成功證據分開。stub明標合成、不冒稱DBruntime。交完整可重建編排/fixture腳本、command/output/exit與expected/actual、cleanup/保留證據；如缺能力則partial。
5. 必要5命令：python3 docs/platform/examples/check_examples.py；python3 docs/platform/tools/gen_state_machines.py --check；python3 docs/platform/tools/gen_permissions.py --check；python3 docs/platform/tools/test_checks.py；python3 docs/platform/tools/check_docs.py。base四基線git diff空、只response追加；完整SHA/輸出/exit記錄。原ENV-01 finding與repair輪次保留。
6. PR1一次DELIVERY含固定result SHA、claim/source/handoff、scope diff、時間/資源/未證明。只合成、沒有Secret/環境值/私人鏈結；不留真實個案。作者不得自批。
stop：mismatch/競爭claim、新費用/權限/外部依賴/資料需求、超20min或期限；安全停止cleanup，無法停止不刪資料也不假稱完成，交具體partial與task資源位置。復原由GPT核對，不擅自第三輪。
next_actor GPT exact-head覆核；通過再核對D1本地合成開工條件，未過不自動續修。POSTED不是ACK/STARTED；無launcher能力，不要求Frank搬運。
