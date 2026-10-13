# D1_ENVIRONMENT 固定成果獨立覆核
work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT；executor Claude；reviewer GPT。
verdict CHANGES_REQUESTED；原交付保留，環境整體未批准。reviewed_content_head e8239a3c678432bea2492daeee71fa737e6b02ef；source/handoff edd0df68bf9323d4677251ddf9300652a73290b3；main/base 9a7bd1295e20837786acc45bdab7fb94f5a1b012。

## 證據與層次
OBSERVED：PR1 claim6112649232、delivery6112685437及144行作者回覆；handoff為ancestor、差異僅新增D1_ENVIRONMENT_RESPONSE_20261012.md。作者DB成功、停止與清理皆AUTHOR_EVIDENCE，沒有冒稱獨立DB重現。
本輪command `git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001 refs/heads/claude/tender-allen-c9p5u1:refs/remotes/origin/claude/tender-allen-c9p5u1` exit0。main 9a7bd1295e20837786acc45bdab7fb94f5a1b012；candidate edd0df68bf9323d4677251ddf9300652a73290b3；result e8239a3c678432bea2492daeee71fa737e6b02ef。不是API代替fetch。
隔離worktree固定在result；腳本未新增差異，已核對imports與subprocess只調既有檢查器；AGENTS.md及CLAUDE.md MISSING。
REPRODUCED（命令均exit0，輸出如下）：
- python3 docs/platform/examples/check_examples.py → OK: 1306 checks passed
- python3 docs/platform/tools/gen_state_machines.py --check → OK: 6 state machines, 86 transitions, doc in sync
- python3 docs/platform/tools/gen_permissions.py --check → OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync
- python3 docs/platform/tools/test_checks.py → OK: test_checks 136 counterexample checks passed
- python3 docs/platform/tools/check_docs.py → OK: 2087 doc checks passed
`git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 e8239a3c678432bea2492daeee71fa737e6b02ef -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` exit0輸出空。規格檢查不是產品驗收。
Reviewer能力：`command -v pg_config` exit1；`test -x /usr/lib/postgresql/16/bin/postgres` exit1；python3 importlib.find_spec(django/psycopg)均False。DB runtime NOT_RUN，沒有安裝全域包、下載DB或提權。可繼續做靜態/隔離mock覆核與有界證據修補，不把跨runtime缺口交Frank例行放行。

## Findings
ENV-01 MAJOR／OPEN：作者回覆54～66行只是摘要；61行設定是註解，沒有建立sock目錄、實際寫入設定或finally/trap。照摘要啟動不能保證私人socket、無TCP或故障清理。根因是只交smoke正文，未交完整編排。重現：讀shell摘要可見設定僅註解、start到stop沒有失敗trap；不在不安全預設下實際啟動。最小修法：追加可執行完整編排，非root、umask077、唯一task目錄、明確空listen_addresses、socket0700、所有exit和trap/finally清理；原144行保留。验收：正常與注入煙霧失敗兩路皆停止/清理，實際設定及命令輸出可稽核。
ENV-02 MEDIUM／OPEN：作者86～94行任何OperationalError都exit0。根因缺預期原因判斷。Reviewer抽出作者python fence，以合成django模組讓cursor拋OperationalError('password authentication failed for user stp_smoke')，執行down分支；預期拒絕、實際exit0且NEGATIVE_OK，反例REPRODUCED（mock，非DB）。最小修法：停止後先確認指定socket不存在，只接受指定socket的connection unavailable；認證/權限/其他錯誤非0。正向unix_only也加入成功斷言。验收：實際停止負向成功，認證/permission合成反例拒絕，TCP/no_tcp_peer=False拒絕；不能任意錯誤充數。
ENV-03 MEDIUM／OPEN：19～25行僅dist-info/RECORD hash，不是下載artifact hash；15～16行安裝命令摘要未固定venv pip路徑。來源/解析版本/hash驗收未完整。最小修法：task隔離wheelhouse內取得固定版本artifacts SHA256、名稱/來源/大小，明記新增下載與原安裝證據不同；使用venv完整路徑與固定版本，離線安裝核對，禁止聲稱追回原下載hash。驗收：artifact清單hash實測、安裝輸出及實際版本一致，不提交二進位/環境設定/Secret或產品lock。

## 當責、延遲與決策
派工19:10:05Z；ACK19:10:40Z；DELIVERED19:13:48Z；review20:07:15Z（2026-10-11 UTC，報告落筆時間）。待審53分27秒，未超1小時；作者開始19:11Z與claim估計19:12Z不同，工時僅REPORTED，不當消耗人日。checkpoint本輪未通過，原因是可重現編排與負向/來源證據缺口，非等待Frank。
依Frank一般技術/有限續作委託，GPT自行核發同task的第一次且最後一次修補，額外30min/0cost、deadline2026-10-12T06:00:00Z不變、repair_round_limit1/used0，本次1/1。原initial delivery已用1/1、readiness1/1及N修補3/3完整保留。見GPT_D1_ENVIRONMENT_REPAIR_PACKET_20261012.md。不能以新ID重置或自動下一輪。
加速：本輪立即審固定交付、獨立錯誤原因反例、同輪派最小修補。下一可見成果是完整可執行編排、嚴格負向和artifact hashes；之後GPT核對本機合成D1開工條件，不用再次向Frank索取例行放行。
A/B局部檢查通過；C產品/DB獨立runtime、D合成E2E、E真實初篩、F服務、G取得成果均未驗收。main未merge，產品未開工，部署/支出/真實資料未授權。
