# GPT D1-A 修補恢復獨立覆核（2026-10-17）
work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-A-CATALOG。
Verdict **CHANGES_REQUESTED**；Reviewer GPT，未修改作者產品、測試或既有證據。
reviewed_head **9581541cf40fef0382b98c2632131710e1c21106**，PR #3 Draft，base為原產品914216cabdb7760f749265fee718b243764cee2b；可信main9a7bd1295e20837786acc45bdab7fb94f5a1b012。
協調PR1 head b360d77e6a0811f8b215318f98470c24815759c3。API live head已核對；git fetch取得成果、detached worktree checkout exit0，source祖先檢查exit0。
原始Frank/GPT執行指示在本對話可見，本次明確接手/本機運行/依賴安裝授權已核對，不再把作者轉錄來源當作本輪阻擋。37764f6既有README/governance額外差異保留待整合對帳，非本輪修補新增，未追認main採用。
讀取：PR1完整52則相關交接、PR3 metadata、22檔差異、作者回覆、匯入/模型/頁面/測試/啟停/收證原碼。沒有部署/merge或真實資料。

## 逐項裁定
|ID|結果|證據與界線|
|---|---|---|
|D1A-01|CLOSED，指定缺口|遞迴檢查明示旗標及明確ORM傳值；獨立20個逐筆旗標反例拒絕；9匯入回歸與原22測試合計31在SQLite替代環境通過，含回滾/DB CHECK；不是PG16驗證。|
|D1A-02|部分解決，MINOR殘留|原後綴、userinfo、scheme反例現正確拒絕，但省略scheme的network-path reference被當普通文字接受。|
|D1A-03|部分解決，MAJOR殘留|wildcard/LAN已在spawn前拒絕，foreign PID核對與保留紀錄改善；首次啟動成功分支仍未核對自己程序及完整紀錄。|
|收證彙總|改善，未全面批准|已累積FAILS，不能再被末尾date掩蓋；負向任意非零與部分未檢查pipeline仍非精確拒絕原因證明，作者58步維持AUTHOR_EVIDENCE。|

## D1A-02：省略scheme繞過（MINOR）
位置 product/catalog/importer.py:76–81 source_ref_problem。
重現 source_ref_problem('//example.invalid.attacker.invalid/a')及'//attacker.invalid/a'均回None；urlsplit可辨識其netloc為外部主機。
原因：looks_like_url只識別scheme、://及www，未涵蓋//。
影響：合成來源外部URL白名單不完整；目前Source.is_link只識別小寫http/https，這兩字串顯示為純文字，**不宣稱已發出外連或造成XSS**。
修法：拒絕network-path reference，或辨識後要求明確http(s)與exact host；保留既有合成電話說明。加合法控制與空/已填DB無變更測試。

## D1A-03：死程序仍回啟動成功（MAJOR）
位置 product/scripts/serve.sh:133–145。
獨立隔離反例：STP_PYTHON=/bin/false（立刻退出），STP_CURL=/bin/true（模擬同port其他服務200），其餘指向任務臨時目錄；執行原serve.sh start。
實際exit0、stdout「serving http://127.0.0.1:8765/ (pid 13)」、stderr空，控制紀錄start為空。
這不依賴Reviewer /proc可見性：子程序確定立即退出。沒有開listener，沒有向外來PID送訊號。
合法對照：wildcard及LAN各exit2且原因為only loopback。正常活程序正向需在有一致/proc的Linux環境重跑。
根因：只檢查HTTP成功，不確認首次啟動自己程序的identity/read_record；空START亦寫紀錄。
修法：啟動成功前必須完整讀回控制紀錄、確認所啟動程序身分與存活，健康成功不能替代；啟動失敗時有界清理本程序，不能留下無法解析的成功紀錄。只處理此可重現缺口，不擴大平台重構。
驗收：死child+健康200非零；活但身分不可核實非零；正常own-child成功；失敗清理、異常PID、kill失敗及原bind/foreign控制不退化。不可用刪預期或跳過測試解決。

## 環境與獨立證據
初始Python3.12.14，Django/psycopg/playwright缺少，PG16二進位不存在。
本次在隔離venv實際pip安裝Django5.2.18、psycopg/psycopg-binary3.3.6成功，相關依賴asgiref3.12.1/sqlparse0.6.0/typing_extensions4.16.0。作者版本Python3.11及PG16.14未冒稱相同。
原產品PG測試實際嘗試exit1：指定本機socket無DB，不能宣稱跑過PG。未安裝系統PG或瀏覽器。
31測試使用Reviewer程序內settings.DATABASES覆寫為SQLite記憶體，**作者檔案零修改**；exit0，31 tests OK。Django測試client不是實際socket HTTP，無手機/實際PG/真實服務驗收。
原12啟停測試用真正Django runner執行exit1，5failures/6errors；本環境子程序PID和可讀/proc不一致，/proc/<pid>/stat FileNotFound，屬BLOCKED_CAPABILITY，不將全部失敗誤判為作者缺陷；作者12PASS不在本環境獨立重現。前一unittest shim診斷亦同類限制，非第二次產品驗收。不在能力不相容的環境修作者測試。
獨立死child反例另以/bin/false固定行為證明，與以上環境限制分開。
git status --porcelain空。作者43tests、實機PG/HTTP/手機8截圖維持AUTHOR_EVIDENCE。

## 必要命令：實際stdout/stderr/exit
```json
[
  {
    "command": "python3 docs/platform/examples/check_examples.py",
    "stdout": "OK: 1306 checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_state_machines.py --check",
    "stdout": "OK: 6 state machines, 86 transitions, doc in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/check_docs.py",
    "stdout": "OK: 2209 doc checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_permissions.py --check",
    "stdout": "OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/test_checks.py",
    "stdout": "OK: test_checks 136 counterexample checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md",
    "stdout": "",
    "stderr": "",
    "exit_code": 0
  }
]
```

## SQLite替代驗證完整輸出（不是PG產品批准）
命令：隔離venv python，設定DJANGO_SETTINGS_MODULE=stp_catalog.settings，載入settings後將DATABASES改為sqlite3 :memory:，django.setup()；DiscoverRunner(verbosity=2).run_tests(['catalog.tests.test_import_repair','catalog.tests.test_catalog'])，以bool(failures)作exit。exit0。
```text
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 31 test(s).
Operations to perform:
  Apply all migrations: catalog
Running migrations:
  Applying catalog.0001_initial...test_explicit_false_or_illegal_flag_rejected_on_empty_db (catalog.tests.test_import_repair.PerRecordSyntheticFlagTests.test_explicit_false_or_illegal_flag_rejected_on_empty_db) ... ok
test_explicit_false_rejected_on_populated_db_without_any_change (catalog.tests.test_import_repair.PerRecordSyntheticFlagTests.test_explicit_false_rejected_on_populated_db_without_any_change) ... ok
test_explicit_true_per_record_is_accepted (catalog.tests.test_import_repair.PerRecordSyntheticFlagTests.test_explicit_true_per_record_is_accepted) ... ok
test_original_fixture_is_unchanged_and_still_imports (catalog.tests.test_import_repair.PerRecordSyntheticFlagTests.test_original_fixture_is_unchanged_and_still_imports) ... ok
test_orm_default_cannot_relabel (catalog.tests.test_import_repair.PerRecordSyntheticFlagTests.test_orm_default_cannot_relabel) ... ok
test_accepted_references (catalog.tests.test_import_repair.SourceUrlTests.test_accepted_references) ... ok
test_reason_for_each_rejected_reference (catalog.tests.test_import_repair.SourceUrlTests.test_reason_for_each_rejected_reference) ... ok
test_rejected_url_writes_nothing_on_empty_and_populated_db (catalog.tests.test_import_repair.SourceUrlTests.test_rejected_url_writes_nothing_on_empty_and_populated_db) ... ok
test_validator_makes_no_network_calls (catalog.tests.test_import_repair.SourceUrlTests.test_validator_makes_no_network_calls) ... ok
test_category_filter_and_empty_state (catalog.tests.test_catalog.CatalogViewTests.test_category_filter_and_empty_state) ... ok
test_database_failure_shows_safe_page (catalog.tests.test_catalog.CatalogViewTests.test_database_failure_shows_safe_page) ... ok
test_expired_resource_direct_link_is_history (catalog.tests.test_catalog.CatalogViewTests.test_expired_resource_direct_link_is_history) ... ok
test_first_screen_under_300kb (catalog.tests.test_catalog.CatalogViewTests.test_first_screen_under_300kb) ... ok
test_food_box_shows_unknown_period_needs_manual_check (catalog.tests.test_catalog.CatalogViewTests.test_food_box_shows_unknown_period_needs_manual_check) ... ok
test_internal_and_suspended_statuses (catalog.tests.test_catalog.CatalogViewTests.test_internal_and_suspended_statuses) ... ok
test_list_shows_five_and_hides_expired (catalog.tests.test_catalog.CatalogViewTests.test_list_shows_five_and_hides_expired) ... ok
test_missing_resource_is_404_page (catalog.tests.test_catalog.CatalogViewTests.test_missing_resource_is_404_page) ... ok
test_not_yet_effective_is_listed_with_date_note (catalog.tests.test_catalog.CatalogViewTests.test_not_yet_effective_is_listed_with_date_note) ... ok
test_public_api_matches_list (catalog.tests.test_catalog.CatalogViewTests.test_public_api_matches_list) ... ok
test_region_filters (catalog.tests.test_catalog.CatalogViewTests.test_region_filters) ... ok
test_status_query_cannot_bypass_visibility (catalog.tests.test_catalog.CatalogViewTests.test_status_query_cannot_bypass_visibility) ... ok
test_unknown_region_or_category_gives_empty_state_not_500 (catalog.tests.test_catalog.CatalogViewTests.test_unknown_region_or_category_gives_empty_state_not_500) ... ok
test_changed_version_content_is_rejected_without_partial_import (catalog.tests.test_catalog.ImportTests.test_changed_version_content_is_rejected_without_partial_import) ... ok
test_database_rejects_inconsistent_effective_unknown (catalog.tests.test_catalog.ImportTests.test_database_rejects_inconsistent_effective_unknown) ... ok
test_database_rejects_non_synthetic_row (catalog.tests.test_catalog.ImportTests.test_database_rejects_non_synthetic_row) ... ok
test_external_source_url_is_rejected (catalog.tests.test_catalog.ImportTests.test_external_source_url_is_rejected) ... ok
test_import_is_idempotent_and_keeps_history (catalog.tests.test_catalog.ImportTests.test_import_is_idempotent_and_keeps_history) ... ok
test_mid_file_failure_rolls_back_everything (catalog.tests.test_catalog.ImportTests.test_mid_file_failure_rolls_back_everything) ... ok
test_new_version_label_adds_history_without_overwriting (catalog.tests.test_catalog.ImportTests.test_new_version_label_adds_history_without_overwriting) ... ok
test_non_synthetic_flag_is_rejected_and_nothing_written (catalog.tests.test_catalog.ImportTests.test_non_synthetic_flag_is_rejected_and_nothing_written) ... ok
test_rules (catalog.tests.test_catalog.VisibilityUnitTests.test_rules) ... ok

----------------------------------------------------------------------
Ran 31 tests in 0.917s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
 OK
System check identified no issues (0 silenced).

```

## 可直接重現的獨立啟動反例
命令 python3 stp958_independent.py，診斷腳本exit0不代表驗收通過。原serve start實際exit0為反例失敗。
```python
import os,tempfile,subprocess,json
from pathlib import Path
root=Path('/workspace/scratch/d285ff1a543a/stp-review-958');p=Path(tempfile.mkdtemp(prefix='stp958_dead_'));(p/'manage.py').write_text('raise SystemExit(1)\n')
# No listener or long-lived child: /bin/false exits immediately, /bin/true simulates unrelated HTTP 200.
env=dict(os.environ,STP_PRODUCT_DIR=str(p),STP_PIDFILE=str(p/'pid'),STP_SERVER_LOG=str(p/'log'),STP_PYTHON='/bin/false',STP_CURL='/bin/true',STP_HEALTH_TRIES='1',STP_STOP_WAIT='1')
r=subprocess.run(['bash',str(root/'product/scripts/serve.sh'),'start'],env=env,text=True,capture_output=True)
print(json.dumps({'case':'dead child plus unrelated health success','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'record':(p/'pid').read_text()},ensure_ascii=False))
# Pure bind legal/negative control, no server.
for bind in ['0.0.0.0:8765','192.168.2.1:8765']:
 env['STP_BIND']=bind;env['STP_PIDFILE']=str(p/'unused');q=subprocess.run(['bash',str(root/'product/scripts/serve.sh'),'start'],env=env,text=True,capture_output=True);print(json.dumps({'bind':bind,'exit':q.returncode,'stderr':q.stderr}))

```

## 下一個有效有界修補包
status READY；同work/task，recovery revision2；source固定9581541cf40fef0382b98c2632131710e1c21106。
GPT依Frank已明確委託一般技術決策，批准恢復包後追加一次最小修補，最多45分鐘含自檢、外部新增成本0、deadline **2026-10-18T14:00:00Z**；新claim必須預留完整45分鐘。原10/13未開工過期包與本恢復一次交付歷史保留，不改ID、不清除N3/3及ENV3/3。
scope product/catalog/importer.py、product/scripts/serve.sh、必要現有測試、product/README.md局部、追加product/evidence/repair-recovery-r2/、新增D1_A_REPAIR_RECOVERY_R2_RESPONSE.md。排除四基線、原作者/GPT證據、fixtures、治理、部署、新功能。
只修D1A-02/03以上殘留；D1A-01維持關閉。允許在已有授權本機隔離環境依賴/PG/loopback/瀏覽器測試；不放寬真實資料、外部AI、費用、公開部署或main merge。
Claude核對live與競爭claim後在平台允許功能分支接續，保留958祖先non-force；沿PR3能推則沿用，不能推則新Draft修補PR清楚連回，PR1協調。新session可接手不冒用舊session，不要求Frank找舊對話。
交固定SHA、逐finding原反例/正向/錯誤原因、5命令與四基線diff；產品DB/HTTP/UI分開，有環境缺口如實PARTIAL，不能以作者舊證據代替新自檢。原文與原evidence不可覆寫。45分鐘或deadline到即交partial，無無限加輪。
next_actor Claude；next_action本包最小修補。交付後GPT exact-head覆核；D2仍前置未過，不新增資料蒐集/平台功能。GPT負責驗收能力替代方案，不要求Frank搬Prompt。
距離可操作合成網站：已具實作、31替代測試通過，但啟停成功與來源邊界尚未完整；沒有main merge/部署/真實家庭取得成果。
