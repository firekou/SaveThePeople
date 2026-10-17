# D1-A 具體候選工單與唯一新增權限決策
status PREPARED／NOT_AUTHORIZED_TO_START；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-A-CATALOG；stage D1_A；executor提案Claude；reviewer GPT；next_actor GPT（授權及gate核對），未發執作claim。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1，2026-10-03）
source/base：source_contentd755256040b1fb8ff5c3a6a48d2be3b7afd6f0c5，main/base9a7bd1295e20837786acc45bdab7fb94f5a1b012；candidate handoff由本輪遠端回執記，不要求本文自己的SHA。分支claude/tender-allen-c9p5u1、PR1 Draft/base main、non-force、不push main。

## 一次具體決策，不再增加無限準備包
建議批准「Claude實作、GPT非作者覆核、本機隔離合成資源目錄D1-A」的小範圍產品開工與僅此範圍角色配置。唯一新增權限問題：是否明確允許這個此前NOT_AUTHORIZED_TO_START的產品範圍？本文件為PREPARED決策材料，不自行授權，不要求Frank搬Prompt/選技術/例行加輪。
已完成證據：N修補3/3與ENV控制流程3/3結案、LTS官方技術選型、作者LTS實檔/PG煙霧、GPT6檔hash/原文/語法與3反例驗證。未證明：獨立DB runtime、產品HTTP/DB/360px與全部開工gate。批准不等驗收/merge/部署；GPT負責關閉技術gate後再發READY，而非讓Frank代查技術。
不批准或無明確答覆：保持PREPARED、保留現有證據，不再例行派環境文件工單；不進D2。批准且gate足夠：GPT以exact候選SHA啟用本工單並發布一次去重交接。產品權限與Reviewer缺執行環境分開。

## 有界產品範圍（僅提案，尚不生效）
scope_paths新增product/與docs/platform/revisions/D1_A_RESPONSE_20261012.md；Django骨架/catalog模型/遷移、合成匯入、列表/詳情/GET篩選、測試與README啟動停止命令、spec-check入口。WP-00～03最小子集，不算完整D1/WP完成，不改CI/保護設定。
excluded四基線、既有docs/spec/tools/examples/作者及GPT證據、.github、供應鏈lock、部署檔、二進位、D2～D4、問答/家庭工作台/聯絡表單/上傳/外部AI/通知/申請/轉介。僅6項既有合成資源與來源、2口徑；各資源資料列標is_synthetic=true。
技術採GPT已決定Django5.2.18 LTS、psycopg3.3.6、PG16、Python3.13；純server-rendered GET、D1-A不用HTMX；已有/tmp LTS環境offline/noindex/nodeps，不新增下載；wheel缺失停止。私人PG socket0700/listen空、HTTP只loopback短時，無永久daemon/雲端/public exposure/Secret/新帳號/費用；全合成不接受真實輸入。
提案資源：120分鐘、成本0、一次交付、repair_round_limit0/used0，exact UTC deadline2026-10-12T06:00:00Z。這不是已核准預算或完整17～25人日D1工期；若啟用時剩餘不足120min，GPT重核發有界期限，不默認逾時放行。歷史ENV/N3/3及各delivery原數保留。

## 開工gate／恢復方式
1 規劃：現有APPROVED限差異；GPT須核对本最小D1-A模型/API/可見性/驗收與源規格，未核完不寫全規格APPROVED。
2 人力：只提案Claude/GPT此120min工作，不假造真人聘用/全MVP配置；需上述限定產品權限。
3 堆疊：GPT可逆技術決定已記錄，不再交Frank選版本。
4 環境：作者替代PG16證據與可提取腳本具備；GPT獨立DB能力缺口保留。執行端verify不過停止，Reviewer另用合法具備依賴的隔離環境重現產品驗收；不能用作者自檢取代。
5 合成：既有fixtures檔案已驗，列層true與拒絕false須產品測試，不改真實資料標籤。
6 repo：沿已觀察功能分支/Draft/非作者覆核/non-force，不寫main，不更改保護或宣稱required checks通過；未知保護UNKNOWN，不merge。
沒有Claude launcher，claim完整記session/work/source/candidate/scope/start UTC/deadline/資源/能力/競爭核對/交PR1。未知在途或競爭停；不能冒用session或永久新session。

## 必要驗收與固定交付
1 乾淨checkout依README extraction/PG init/start＋manage.py migrate＋migrate --check＋import_synthetic_catalog，實際command/output/exit/版本；DB6資源/6來源/2口徑；重複匯入冪等、不覆蓋歷史。
2 manage.py test：拒絕任何非合成row，失敗無部分新增；未知期限與effective_to一致；T-04可見性/T-21期限語意；保留來源/地區/最後查核日期/版本/合成標示。
3 GET /api/public/resources與列表回5項，FOOD-005標生效期間未知需人工確認，RENT-006不進列表，直接歷史詳情標已過期；?status=EXPIRED不能繞列表；地區不存在回理解空態非500。FORMAL不顯示政府已核准，不新增真實規則查核。
4 HTTP僅loopback，curl證據與DB查詢各記exit，資料庫停止負向回可理解錯誤無traceback/連線字串。360px實際截圖與Tab操作/無水平捲動/首屏≤300KB；瀏覽器能力缺失標NOT_RUN/partial，不下載瀏覽器替代。
5 五repo命令各記exit/output：check_examples.py、gen_state_machines.py --check、gen_permissions.py --check、test_checks.py、check_docs.py。原四基線/歷史證據diff空；所有產品差異交固定head，不把5文件命令当产品验收。
6 evidence在D1_A_RESPONSE：claim/來源/command完整輸出/產品測試/HTTP/DB/手機證據/資源/NOT_RUN/停止清理結果。PNG如合成截圖可置product/evidence/，不得binary wheel/真實資料。安全finally HTTP停止/PG停止≤2/確認無task程序才清理，查詢不明保留partial；不kill無關程序。
stop：未獲產品權限/未完成gate/HEAD_MISMATCH/競爭claim/環境缺失/120min/deadline、Secret/費用/新下載/真實資料/外部依賴/公開部署；保留歷史與partial，不自動repair或進D2。next checkpoint GPT exact-head產品驗收，未獨立驗收不approve/merge。
