# D1 技術版本與最小驗收具體化工作包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-STACK-AND-ACCEPTANCE；stage D1_STACK_AND_ACCEPTANCE；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content09e19a2f800455685489a42b3c5e17303b115375；base/main9a7bd1295e20837786acc45bdab7fb94f5a1b012；handoff exact SHA由PR發布回執指定，source ancestor/原環境response bytes相同。live不符先HEAD_MISMATCH停止，不猜最新head。
工作分支claude/tender-allen-c9p5u1，PR1/base main；沿用合法session/接手保留claim，先核競爭claim與在途動作，再追加完整claim：work/task/stage/session/source/handoff/scope/開始UTC/deadline/資源/能力/交付位置。non-force，不push main。

## 授權、範圍與限額
GPT依Frank一般技術與工單規劃委託，具體化尚缺官方LTS選型與D1進場驗收；不是第四輪環境修補或產品開工。scope_paths僅新增docs/platform/revisions/D1_STACK_AND_ACCEPTANCE_RESPONSE_20261012.md；排除既有作者實作/測試/證據/治理歷史、四原始基線、產品/.github/依賴lock/二進位/部署。允許隔離/tmp純標準函式庫fixture預期核對，嵌入report即可，不改repo工具。
exact UTC deadline2026-10-12T06:00:00Z；40分鐘、成本0、一次交付；repair_round_limit0/used0，不自動修補；環境repair3/3、readiness1/1、N3/3完整保留。無採購、聘用、新服務/session/排程。
外部操作只公開唯讀技術官方來源：djangoproject.com/docs.djangoproject.com 的支援表/安裝相容性；pypi.org公開metadata；psycopg.org/docs、postgresql.org/docs只在相容性必要時。最多8個官方頁/metadata、來源失敗最多同請求一次安全重試；不擴成政府福利/法律/機構資源查核。禁止套件下載/安裝、DB啟動、新HTTP服務、產品檔、Secret/環境值、真實資料、外部AI、通知/申請/部署。

## 具體動作與驗收
1. 官方確認當期Django LTS系列與最新受支持patch、Python與PostgreSQL最低版本/支援期間，查核UTC日期、URL與必要短引句/頁節明列；別把作者現有6.1.2直接當LTS。推一個明確選型，說明與現有Python/PG16/psycopg版本的相容性、現有venv差異；metadata不存在或來源取不到標UNKNOWN，不編版本/供應鏈hash。
2. 六gate按BATCH1§1重核，逐欄VERIFIED/AUTHOR_EVIDENCE/UNKNOWN/NOT_AUTHORIZED。列source證據位置與現有差異批准范围，不把文檔或stub當產品批准；分支與Claude/GPT限定Agent分工明確，沒有真人工程配置/預算承諾。給GPT下一普通技術決策的唯一剩餘問題與建議，不要求Frank搬運/例行放行。
3. 同檔準備D1-A最小實作候選工單（PREPARED、未生效）：WP-00～03最小列表/詳情/篩選，僅6合成fixture，不開D2～D4；具體擬定source/base、branch/PRbase、scope/excluded、依賴清單與版本、UTC期限/有界工時0成本、停止/交付/nextActor。若LTS切換需下載授權，只列精確必要套件/版本/來源與預算，不自行執行。
4. 列出產品HTTP/DB的最小驗收命令與expected/negative，包含乾淨checkout、migrate/importsynthetic/test/speccheck、expired不在列表、effective_unknown只人工核對語意、非合成匯入拒絕、列層合成標示、API/HTML查核日期/地區/來源、360px可用/鍵盤/空態。沒有HTTP/DB實作就明記NOT_RUN，不宣稱成果。用既有reference引擎核對fixture預期，不重搜真實資源、不把6項全部PUBLISHED。
5. 交固定result SHA至PR1一次DELIVERY，report包含claim/source/handoff、官方來源版本與查核UTC、gate證據表、具體PREPARED工單、必要5命令輸出exit：python3 docs/platform/examples/check_examples.py；python3 docs/platform/tools/gen_state_machines.py --check；python3 docs/platform/tools/gen_permissions.py --check；python3 docs/platform/tools/test_checks.py；python3 docs/platform/tools/check_docs.py；四基線diff空/僅一新檔。作者不自批。
stop：mismatch/競爭claim/scope/40min/6UTC超限、新費用/權限/Secret/資料/外部下載需求，交partial與最小恢復；不得把PREPARED啟動條件默認批准。來源暫時不可達完成其餘fixture/gate/workpacket，不無限重試。
next_actor GPT exact-head覆核，依官方選型與gate核對做下一有限技術決策。POSTED不等ACK/STARTED，無launcher證據；不要求Frank回舊session。
