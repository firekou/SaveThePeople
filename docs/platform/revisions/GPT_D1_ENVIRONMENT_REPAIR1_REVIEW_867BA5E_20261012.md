# D1_ENVIRONMENT repair1 固定成果覆核與有界決策
work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT；executor Claude；reviewer GPT；verdict CHANGES_REQUESTED。
reviewed_content_head 867ba5eccd3b1cc13542d22c471ee7413dee89fc；source e8239a3c678432bea2492daeee71fa737e6b02ef；handoff 63345d354aa95d9f08f369b7c175ca4223adc451；base/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012。

## Live與完整性
本輪明確 `git fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001 refs/heads/claude/tender-allen-c9p5u1:refs/remotes/origin/claude/tender-allen-c9p5u1` exit0；main如上、PR candidate63345d354aa95d9f08f369b7c175ca4223adc451、result如上。PR1 open Draft未merge；新增claim6113208964、delivery6113237754已全文讀取；main README/四基線、最新續作/當責與repair包已讀。AGENTS.md及CLAUDE.md MISSING。
VERIFIED：result相對handoff僅response追加322行、無刪行。原144行bytes完全保留，SHA256 73c547c5292e5ecf6c2e97e93046647064bbad4d254e3950a98453fb37ba7f00。作者原始證據不改。
隔離worktree fixed result；抽出repair bash/python fences，只先審查再跑：bash -n編排exit0；python3 /tmp/stp-review-env-r1/negtests.py exit0，9項mock全部符合，為REPRODUCED纯邏輯，非DB runtime。
REPRODUCED 必要命令皆exit0：
- python3 docs/platform/examples/check_examples.py → OK: 1306 checks passed
- python3 docs/platform/tools/gen_state_machines.py --check → OK: 6 state machines, 86 transitions, doc in sync
- python3 docs/platform/tools/gen_permissions.py --check → OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync
- python3 docs/platform/tools/test_checks.py → OK: test_checks 136 counterexample checks passed
- python3 docs/platform/tools/check_docs.py → OK: 2092 doc checks passed
`git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 867ba5eccd3b1cc13542d22c471ee7413dee89fc -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` exit0空。

## Finding與独立反例
ENV-01 MAJOR仍OPEN。根因：168行僅set -u，198～202及221～238行多個命令僅印exit而不阻斷；238行只return rc_pos，237行負向失敗被忽略；208～213行cleanup不驗證停止即rm資料目錄。已補完整正文/設定寫入，但fail-closed未完成。
重現：隔離temp內抽出作者編排，僅把D/S/PGBIN/降權runner替換為合成fixture，把PG/venv命令換stub（不連DB、不讀CA、不用prepare、不提權）。保留作者控制流程，兩情境預期非0：
1. positive0/stop0/status3/down5 → negative(down) exit5，但整體exit0。
2. positive0/stop1/status0/down0 → cleanup status0（仍running）後removed pgdata/sock/log，整體exit0。
兩條失敗均REPRODUCED；stub不是實際PG操作。最小修法：每項關鍵command檢查exit/預期值，合併negative與cleanup裁定；stop未成功或status非3不得刪DB/socket/log，也不得宣稱無process。注入失敗的exit須保持，同時如實給cleanup_failure；不要用printf/最後rm掩蓋。
驗收：正常0；down拒絕非0；prepare離線安裝/版本驗證失敗非0；initdb/config/start失敗非0；stop失敗/status仍running非0且資料保留；failed cleanup不得報完成。實際PG正常/注入煙霧兩路獨立於合成stub。
ENV-02原純函式缺口CLOSED（9反例REPRODUCED，認證/permission/TCP/錯誤筆數拒絕）；外層吞錯歸ENV-01，不重編新ID。
ENV-03文件交付缺口CLOSED：5artifact名稱/大小/64hexhash、新下載與原下載分開、離線安裝命令已OBSERVED；artifact bytes/來源hash僅AUTHOR_EVIDENCE，NOT_VERIFIED，無供應鏈或產品鎖定批准。原runtime/cleanup成功同樣AUTHOR_EVIDENCE；本Reviewer仍缺PG/Django/psycopg，DB NOT_RUN，不把mock升級runtime。

## 額度偏差與GPT決策
作者明載下載索引失敗2次後第三次成功；原包只准一次下載＋一次暫時網路安全重試，實際Python版本錯誤非暫時網路，且第三次超上限。記執行偏差，不追認為遵守上限。未見新支出或真實資料；無須Frank例行裁定，但此缺陷要求程序改正：下載額度按所有attempt累計、preflight不通過不下載。本輪及下一包不再准外部下載。
依Frank最新有限技術委託，GPT明確調整本task repair_round_limit1→2，used1保留；額外20分鐘/0cost/一次repair2，deadline2026-10-12T06:00:00Z不變。理由是已獨立證明的同ENV-01兩條假成功/危險清理，修法局部、無新下載或產品擴張。不是自動重試、不是換ID；無第三輪預授權。initial delivery1/1、readiness1/1、N修補3/3保留。
posted20:08:05Z／ack20:08:50Z／delivered20:11:51Z／review21:02:09Z（2026-10-11 UTC）；待審50分18秒未超1小時。claim估計開始20:12Z晚於delivery，作者實報20:09～11Z，時間不一致；工時僅REPORTED。加速為優先審交付、控制流程反例、同輪最小修補；下一成果是故障時確實非0且保留未停止DB的證據，不要求Frank搬運Prompt。
此checkpoint未COMPLETE；A/B局部規格/純函式通過，C～G、Docker、產品HTTP/DB、LTS、真實服務仍未驗收，main不merge、產品不開工。next_actor Claude，唯一repair2包GPT_D1_ENVIRONMENT_REPAIR2_PACKET_20261012.md。
