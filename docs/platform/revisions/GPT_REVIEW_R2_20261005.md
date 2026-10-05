# STP-PLATFORM-PLAN-001｜R2 GPT 獨立差異覆核

日期：2026-10-05｜Reviewer：GPT／Codex｜裁定：**CHANGES_REQUESTED**。

## 固定範圍與版本

| 欄位 | 值 |
|---|---|
| repository | firekou/SaveThePeople（公開） |
| PR | [#1](https://github.com/firekou/SaveThePeople/pull/1)，open／Draft／unmerged |
| base／origin/main | `9a7bd1295e20837786acc45bdab7fb94f5a1b012` |
| R1 content head | `45e7034114a7ae27f8e9743033d901b8466dc199` |
| reviewed_head／R2 content head | `c1d56496bb210518314254b88d9c8b52e56408d9` |
| candidate at review start | 與 reviewed_head 相同 |
| review_record_head | 本報告寫入後，以 GitHub 回傳及遠端 ref 為準；正文不包含自身 commit SHA |
| 工作 | R2 的 F-01～F-08 差異與必要反例；不重審全部歷史規劃、不重搜政策 |
| 作者 | Claude，PR 交付宣告與三筆 commit 可直接讀到；本輪啟動 NOT_CONFIRMED |
| 人類參與 | 本輪未觀察到新 Frank 決策或機構／專業核定 |

main 只有 README 與四份原始基線；AGENTS.md、CLAUDE.md、固定 Controller 帳本為 MISSING。已讀 main 五檔、R1／R2 回應、平台文件的 R2 差異與受影響段落、JSON／schema／參考程式與檢查工具。**本報告不是整份平台重新全面批准。**

GitHub API 開始核對：PR head、base 正確；discussion comments 與 submitted reviews 均為空。R2 的作者回報不是 Reviewer 批准。API exact-head check-runs=0、workflow_runs=0、commit statuses=[]：沒有遠端 CI 成功證據，不把「沒有檢查」稱為「綠燈」。PR 三筆 commits 為 d523bb6…、45e7034…、c1d5649…。實際 checkout 與 runtime 已執行。

## Git 與命令證據

隔離位置為本輪暫存 checkout；不使用真實家庭資料，不操作外部 AI、部署、送件或通知。

```text
git ls-remote https://github.com/firekou/SaveThePeople.git refs/heads/main refs/heads/claude/stp-platform-plan-001
exit 0
c1d56496bb210518314254b88d9c8b52e56408d9 refs/heads/claude/stp-platform-plan-001
9a7bd1295e20837786acc45bdab7fb94f5a1b012 refs/heads/main

git clone --no-checkout --single-branch --branch main https://github.com/firekou/SaveThePeople.git stp-review
git -C stp-review fetch origin main claude/stp-platform-plan-001
git -C stp-review checkout --detach c1d56496bb210518314254b88d9c8b52e56408d9
combined command exit 0
From https://github.com/firekou/SaveThePeople
 * branch main -> FETCH_HEAD
 * branch claude/stp-platform-plan-001 -> FETCH_HEAD
HEAD is now at c1d5649 docs(platform): R2 revision for STP-PLATFORM-PLAN-001 (F-01..F-08)

git rev-parse HEAD origin/main
exit 0
c1d56496bb210518314254b88d9c8b52e56408d9
9a7bd1295e20837786acc45bdab7fb94f5a1b012
```

先審查 imports、入口、檔案寫入與 subprocess：只用標準函式庫；check_docs 子程序為本 repo 的 gen_permissions／gen_state_machines／test_checks；產生器使用 --check，不寫作者原始文件。未安裝依賴。Reviewer 探針在 checkout 外建立，僅對記憶體深拷貝做反例，不更動作者程式與原證據。

以下均為 **REPRODUCED**，不是複製作者數字：

| 實際 command（repo 根目錄） | stdout | exit |
|---|---|---:|
| `python3 docs/platform/examples/check_examples.py` | `OK: 910 checks passed` | 0 |
| `python3 docs/platform/tools/gen_state_machines.py --check` | `OK: 6 state machines, 86 transitions, doc in sync` | 0 |
| `python3 docs/platform/tools/gen_permissions.py --check` | `OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync` | 0 |
| `python3 docs/platform/tools/test_checks.py` | `OK: test_checks 50 counterexample checks passed` | 0 |
| `python3 docs/platform/tools/check_docs.py` | `OK: 1962 doc checks passed` | 0 |

全部 stderr 為空。以上五項通過**不抵銷**下列獨立發現。

```text
git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 c1d56496bb210518314254b88d9c8b52e56408d9 -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
stdout empty; stderr empty; exit 0

git diff 45e7034114a7ae27f8e9743033d901b8466dc199 c1d56496bb210518314254b88d9c8b52e56408d9 -- docs/platform/revisions/R1_RESPONSE.md
stdout empty; exit 0

git status --short
stdout empty; exit 0 (author checkout unchanged after checks/probes)
```

## F-01～F-08 判定

「完成」只指本輪 A 文件／政策或 B 純邏輯參考層級，不代表產品與真實服務完成。

| ID | 本輪判定 | 證據與限制 |
|---|---|---|
| F-01 | **部分完成，未關閉** | 缺 rule.status 與後置非法 operator 已拒絕；但 CUSTOM expression 未知鍵通過推薦，schema 與實際推薦入口不一致，見下方 P1 finding。 |
| F-02 | 完成（B，REPRODUCED） | age_between 明確 UnsupportedError；未知口徑鍵明確 ValidationError，核對原因；年齡／就學／服役／推估所得仍未實作。 |
| F-03 | **部分完成，未關閉** | P11 的 R5 轉介及 ASG 自驗政策反例均被具體攔截；VERIFY 單筆摘要界線已明列。P9 主要操作与引擎 §8.2 仍承諾逐案內容，與禁止個案讀取衝突，見下方。沒有產品授權行為證據。 |
| F-04 | 完成（A／B，REPRODUCED） | 先寫失敗503且主庫不變；主庫失敗202後可還原套用；紀錄短於見證水位維持隔離且原因 LOG_INCOMPLETE；HARD_DELETE／REDACT 差异由既有情境重跑確認。不是 DB／備份整合演練，U-23 不下法律结论。 |
| F-05 | 完成（A／B，VERIFIED／REPRODUCED） | P2／CP-05／CP-25／API 的伺服器草稿界線一致；本文欄位遭拒；當下 FORBIDDEN→403、GONE→410且無內容。真實瀏覽器與T-56未驗收，resolver 的產品授權實作未證明。 |
| F-06 | 完成（A／B，REPRODUCED） | 合法 SUPPLEMENTARY 的 AP-06 返回 ok，新增同種進行中關聯件返回 DUPLICATE_RELATED；依 kind、同家庭／資源／期間、排除自身均具規格與既有負向案例。DB競態／R4身份驗證未實作。 |
| F-07 | **部分完成，未關閉** | effective_unknown 一致性與缺 recheck 起算攔截成立；但「其他狀態必空」與「RV-09暫停保留」矛盾，PUBLISHED帶舊起算仍回 FORMAL，需統一生命週期規範。schema 結構不等於語意通過。 |
| F-08 | 完成（A，VERIFIED） | 人工核對 PRD PR-07→D-310（營運門檻）及 D-106→引擎§6.6（排序）語意相符；工具反例重跑。啟發式檢查不能證明所有引用正确，未做全面歷史引用重審。 |

Reviewer 另執行20項探針：18項與預期相符、2項不符（F-01推薦漏拒、F-07狀態／欄位矛盾）。探針 command 為 `python3 stp_independent_probes.py stp-review`，exit 0；**該0僅代表蒐證程式正常結束，並非20項驗收通過**。完整腳本與逐項輸出見附錄。

## 保留原 ID 的未關閉 findings

### F-01｜P1：CUSTOM 的未知語意鍵被忽略，仍正式推薦

- 根因：`examples/ref_engine.py:237–251` 的 `_expr_problems` 只讀 op／children，未拒絕其他鍵；`recommendation_status:543–569` 並未在此入口做完整 schema 結構驗證。引擎文件§5.4:157–166承諾整份規則的鍵與型別完整驗證，schema 的 node 也拒絕額外欄位。
- 重現：合法 baseline 規則補 `rule_version=1.0.0`、設 CUSTOM，expression=`{"op":"ALL","children":["C1"],"not":true}`。schema 回 `$.expression: must match exactly one of oneOf (matched 0)`；同份規則呼叫 recommendation_status 卻為 `{"status":"FORMAL","reasons":[]}`。
- 影響：未知欄位所表達的限制遭靜默忽略，不能據此宣告「完整結構驗證通過」。不需要認定 not 是支援功能；正確行為是拒絕未知键。
- 最小修法：遞迴驗證每個 expression 節點的允許鍵與型別，並使推薦入口使用這份完整驗證；保留合法巢狀 ALL／ANY，不靠額外獨立 schema 自檢代替入口拒絕。
- 驗收：根與深層 expression 加未知鍵、空鍵名、錯型別等須 `NOT_RECOMMENDED/RULE_INVALID`，validate_rule 須具體 ValidationError；合法巢狀仍 FORMAL，既有五項檢查通過。不得只測「某個錯誤讓程式崩潰」。

### F-03｜P2：P9 的逐案影響顯示與資料權限矛盾

- 根因：`USER_JOURNEYS_AND_SCREENS.md:196–204` 以R5為主要使用者，主要操作列「查看受影響案件」，同頁又寫「個案內容一律不可見」；`RESOURCE_AND_ELIGIBILITY_ENGINE.md:260` 寫「在P9顯示每案處理進度」。permissions.json／產生器只覆蓋頁面的權限行及結構化 grant，沒有驗證這兩項語意承諾。
- 重現：對照上述兩行與 PRD§4.3「R5不得存取任何個案內容」及P9權限；五項工具仍全部exit0。因此不能宣告矩陣、頁面、API全部一致。
- 最小修法：維持現有禁個案權限；P9僅呈現資源層級影響摘要，明確不含逐案ID、家庭或每案處理進度。逐案工作交P7／P8的ASG／SITE-REV，相關後端任務仍可生成；不替R5新增個案權限。
- 驗收：P9主要操作、引擎§8.2、permissions與API規格一致；負向檢查能抓回「R5/P9逐案清單」這個具體矛盾。只補文字／政策檢查，不要求本輪啟動產品或真实帳號測試。

### F-07｜P2：recheck_started_at 狀態生命週期不一致

- 根因：`DATA_MODEL_AND_STATE_MACHINES.md:164` 要求非NEEDS_RECHECK必空；同檔:194卻要求RV-09進SUSPENDED時保留；RV-11恢復及其他退出路徑的清除未統一。`ref_engine.py:568–599` 只在NEEDS_RECHECK使用起算，沒有驗證狀態／起算欄位一致性。
- 重現：baseline PUBLISHED加入 `recheck_started_at="2026-01-01"`，recommendation_status仍為FORMAL；這違背第164行，且第194行本身又與第164行矛盾。此反例證明規範未統一，不表示產品已發生故障。
- 最小修法：統一當前欄位與稽核歷史的分工。建議NEEDS_RECHECK保留有效起算；離開時清空當前欄位，歷史保留於AuditEvent；若採保留於SUSPENDED，須明確列合法狀態與恢復清除條件。沿現有權限與業務語意選定一套，不改14天暫行門檻。
- 驗收：RV-07、RV-08、RV-09、RV-10、RV-11與欄位表一致；重複進入複查取得新起算，缺／未來／無效起算及不合法狀態組合被具體拒絕，合法流程不誤擋。補狀態×欄位的語意反例，不只schema結構測試。

## 最小修補工作包與交接

以下為本輪在既有「規劃／合成／參考檢查修補」授權內新增的具體界線，不冒稱歷史工單已有期限或額度。

| 欄位 | 工作包 |
|---|---|
| work_id | STP-PLATFORM-PLAN-001（沿用，不重置任務） |
| task_id | STP-PLATFORM-PLAN-001-R2-GPT-REPAIR-20261005 |
| goal | 修閉本報告F-01、F-03、F-07，取得A／B層規劃與參考檢查批准 |
| stage／status | R2差異覆核後修補／CHANGES_REQUIRED；本報告裁定CHANGES_REQUESTED |
| executor／reviewer | Claude／未參與修補製作的GPT Reviewer |
| source content head | c1d56496bb210518314254b88d9c8b52e56408d9 |
| base／PR base | 9a7bd1295e20837786acc45bdab7fb94f5a1b012／main |
| 工作分支／交付 | claude/stp-platform-plan-001／既有PR #1，維持Draft |
| scope_paths | docs/platform/內上述三findings受影響文件、state_machines.json、permissions.json（僅一致性必要修改，禁止增權）、schemas/、examples/、tools/；新增修補回覆可放revisions/R2_REPAIR_RESPONSE.md |
| excluded_paths | 四份原始基線、GPT本覆核原紀錄、R1/R2作者歷史回覆、產品目錄／網站／部署設定；無關重構 |
| exact UTC deadline | 2026-10-06T08:00:00Z（本次新增修補期限，非历史原期限） |
| 資源上限 | 一次離線／本機合成修補，Agent實際投入最多90分鐘，外部付費成本0；不換算人日已消耗 |
| repair_round_limit／used | 本次最小修補包1次／0；歷史累計額度NOT_DEFINED，R2名稱不視為已耗用兩次 |
| 資料／環境 | 明確合成資料；隔離本機checkout，標準函式庫，不開外部AI／雲端／真實初篩入口 |
| 必要命令 | 五項原必跑命令＋四份基線diff＋本報告指定負向控制；記command/stdout/stderr/exit及固定content SHA |
| acceptance | 三findings逐項原因與修法對應；負向原因正确、合法控制不誤擋、五項檢查通過、基線不變；不宣稱產品完成 |
| 證據位置 | revisions/R2_REPAIR_RESPONSE.md及examples/／tools/內必要回歸測試；Reviewer蒐證與作者原證據分開 |
| claim | 執行前在PR #1追加work_id、session、來源content SHA、review_record SHA、scope、開始/期限/資源、能力及無競爭claim確認；不得冒充舊session |
| stop_conditions | 版本產生非reviewer-only未知差異、競爭claim、超過期限/資源/一次修補、需真實資料/新增權限/外部操作；不自行重置限制 |
| resume | 同scope且有效授權內對帳後續作；超額或增權交Frank單一決策包 |
| next_actor／next_action | Claude讀本報告→claim→僅修三項→固定結果SHA及補件證據交PR #1；GPT下一輪只審固定新content head |
| next checkpoint | 修補READY_FOR_REVIEW；尚未進D1開發、合併或真實試點 |

目前沒有固定Controller帳本：**提出**以PR #1 conversation作唯一協調入口、docs/platform/revisions/的GPT_REVIEW檔作裁定來源。這是本次治理採用提案，不假稱main早有帳本或已核准新制度；不為此另建第二PR或直接改main。後續reviewer-only更新先查diff，再標content_head與review_record_head；不要求重審報告自身產生的新SHA。

GitHub通知只有寫入成功才為POSTED；Claude讀取ACKNOWLEDGED、實際STARTED均需後續證據。目前不能由PR存在推定Claude已啟動。不要求Frank搬運報告或回到原session。

## 藍圖與下一階段條件

完整goal（main README，v0.1基線）：**讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。** 核心成果為新增實際取得幫助的家庭數，同時追蹤等待時間、服務成本及續辦結果。

- 服務P0～P3：main明列尚未确认合作或服務真實家庭；試點啟動日未定，90天不自行起算；本輪沒有接觸／同意／送件／核准／實際取得成果。
- 工程D1～D4／WP：目前只有候選v0.4-draft規劃與參考模擬。Batch1寫「已備妥，本輪不開工」；本輪未獨立批准，工程人力D-307未決，repo分支規範待指定。推薦堆疊可逆，不表示工程已開工。47～68／107～161人日仍是估算。
- A／B：檢查重現與部分修正成立，但整體仍需三項修補；C真實產品／DB、D產品合成E2E、E真實初篩、F真實工作台／服務、G取得成果均NOT_VERIFIED／未驗收。
- G1～G8、AS-1～AS-6沒有本輪通過證據；不存在合併或部署新增授權。本輪不讀真實資料、不新增合作或法律结论。
- 方向：**前進**。從作者自報提高為獨立重現，找出綠色檢查未覆蓋的推薦漏拒與文件矛盾，交接縮到三項可驗收修補。距離家庭真正取得幫助，仍需產品／閘門、地區／據點／人力及真實服務驗證。

現在：Claude〔修補待claim，啟動NOT_CONFIRMED〕；GPT〔R2差異覆核完成，待固定修補成果〕；Frank〔本修補不需行動〕。

## 附錄：Reviewer探針與實際輸出

此蒐證腳本只呼叫既有參考程式與對深拷貝施加合成反例；不是新增產品、不是替Claude修復，也不是作者證據。

```python
import copy
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root / 'docs/platform/examples'), str(root / 'docs/platform/tools')]
import ref_engine as R
import ref_control as C
import schema_lite as S
import gen_permissions as G

cases = R.load_json('engine_cases.json')
base = cases['recommendation_base']
def recommend(resource):
    return R.recommendation_status(resource, cases['recommendation_sources'], cases['recommendation_as_of'], cases['recommendation_scopes'])
rows = []
def record(name, actual, expected):
    rows.append({'probe': name, 'actual': actual, 'expected': expected, 'matches': actual == expected})
def error(fn):
    try:
        fn()
    except Exception as e:
        return type(e).__name__ + ': ' + str(e)
    return 'NO_ERROR'

record('F01 valid baseline', recommend(copy.deepcopy(base)), {'status':'FORMAL','reasons':[]})
x = copy.deepcopy(base); del x['rule']['status']
record('F01 missing rule.status', recommend(x), {'status':'NOT_RECOMMENDED','reasons':['RULE_STATUS_MISSING']})
x = copy.deepcopy(base); x['rule']['criteria'].append(dict(x['rule']['criteria'][0], criterion_id='C2', operator='BAD_OPERATOR'))
record('F01 illegal last criterion', recommend(x), {'status':'NOT_RECOMMENDED','reasons':['RULE_INVALID']})
x = copy.deepcopy(base); x['rule']['rule_version'] = '1.0.0'; x['rule']['combinator'] = 'CUSTOM'
x['rule']['expression'] = {'op':'ALL','children':['C1'],'not':True}
record('F01 unknown expression key schema rejection', bool(S.validate(x['rule'], S.load_schema('eligibility_rule'))), True)
record('F01 unknown expression key recommendation rejection', recommend(x), {'status':'NOT_RECOMMENDED','reasons':['RULE_INVALID']})
for key in ['age_between', 'unrecognized_scope_constraint']:
    scopes = copy.deepcopy(cases['recommendation_scopes']); sk = next(iter(scopes))
    scopes[sk]['member_inclusion'][key] = [0,17]
    actual = error(lambda: R.validate_scope(scopes[sk]))
    rows.append({'probe':'F02 '+key,'actual':actual,'expected':'UnsupportedError mentioning age_between' if key=='age_between' else 'ValidationError mentioning unrecognized_scope_constraint','matches':key in actual and actual.startswith('UnsupportedError' if key=='age_between' else 'ValidationError')})
d = G.load(); machines = json.loads((root/'docs/platform/state_machines.json').read_text())['machines']
x = copy.deepcopy(d)
for page in x['pages']:
    if page['page']=='P11':
        for section in page['sections']:
            if section['class']=='referral': section['grants'].append('R5·INT')
record('F03 P11 unauthorized R5 specifically rejected', any('R5 must not see case referrals' in p for p in G.policy_problems(x,machines)), True)
x = copy.deepcopy(d)
for api in x['api']:
    if api['endpoint'].endswith('/verify'): api['grants'].append('R3·ASG')
record('F03 ASG verification specifically rejected', any('verification must not be granted to the case owner' in p for p in G.policy_problems(x,machines)), True)
ctrl = R.load_json('control_cases.json'); initial = ctrl['initial_state']; consent = next(iter(initial['consents']))
rec = {'type':'CONSENT_REVOKE','consent':consent,'purposes':['REMINDERS']}
log = C.ControlLog(); wit = C.Witness(); log.fail_next=1
code, why, st = C.request_control(C.new_state(initial),log,wit,rec)
record('F04 log unavailable leaves main unchanged', [code,why,st==C.new_state(initial)], [503,'NOT_RECORDED',True])
log = C.ControlLog(); wit=C.Witness(); code,why,st=C.request_control(C.new_state(initial),log,wit,rec,db_fail=True)
out=C.recover(st,log,wit)
record('F04 pending control recovered', [code,why,out['quarantined'], 'REMINDERS' in out['state']['consents'][consent]['revoked']], [202,'RECORDED_PENDING_APPLY',False,True])
log.entries.pop(); out=C.recover(st,log,wit)
record('F04 missing tail quarantines for exact reason', [out['quarantined'],out['reason'].startswith('LOG_INCOMPLETE:')], [True,True])
store = R.IdempotencyStore(); store.begin('reviewer-synthetic','key','hash')
shape = {'status_code':201,'resource_ref':{'type':'demo','id':'demo-id'},'shape_version':1}
store.complete('reviewer-synthetic','key',shape)
for verdict,code in [('FORBIDDEN',403),('GONE',410)]:
    record('F05 replay '+verdict, list(store.replay('reviewer-synthetic','key','hash',lambda actor,ref:(verdict,None))), [code,None])
bad=copy.deepcopy(shape);bad['body']={'synthetic_only':True}
msg=error(lambda: store.complete('reviewer-synthetic','key',bad))
record('F05 response body specifically rejected', msg.startswith('ValidationError: idempotency response must be exactly'), True)
fixture = copy.deepcopy(cases['application_ready_cases'][0]); apps=fixture['existing']
record('F06 legitimate supplementary', list(R.application_ready_check(apps,fixture['app_id'])), [True,'ok'])
duplicate=copy.deepcopy(apps[-1]);duplicate['id']='synthetic-duplicate';apps.append(duplicate)
record('F06 duplicate supplementary', list(R.application_ready_check(apps,fixture['app_id'])), [False,'DUPLICATE_RELATED'])
x=copy.deepcopy(base);x['version']['effective_unknown']=True
record('F07 inconsistent effective_unknown',recommend(x),{'status':'NOT_RECOMMENDED','reasons':['VERSION_INVALID']})
x=copy.deepcopy(base);x['version']['status']='NEEDS_RECHECK'
record('F07 missing recheck start',recommend(x),{'status':'NOT_RECOMMENDED','reasons':['RECHECK_START_MISSING']})
x=copy.deepcopy(base);x['version']['recheck_started_at']='2026-01-01'
record('F07 PUBLISHED stale recheck start rejected under row 164',recommend(x),{'status':'NOT_RECOMMENDED','reasons':['VERSION_INVALID']})
for row in rows: print(json.dumps(row,ensure_ascii=False))
print(json.dumps({'matching_probes':sum(r['matches'] for r in rows),'mismatches':sum(not r['matches'] for r in rows),'notice':'Evidence probes; mismatches are open findings, not passing acceptance.'}))
```

```text
{"probe": "F01 valid baseline", "actual": {"status": "FORMAL", "reasons": []}, "expected": {"status": "FORMAL", "reasons": []}, "matches": true}
{"probe": "F01 missing rule.status", "actual": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_STATUS_MISSING"]}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_STATUS_MISSING"]}, "matches": true}
{"probe": "F01 illegal last criterion", "actual": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]}, "matches": true}
{"probe": "F01 unknown expression key schema rejection", "actual": true, "expected": true, "matches": true}
{"probe": "F01 unknown expression key recommendation rejection", "actual": {"status": "FORMAL", "reasons": []}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["RULE_INVALID"]}, "matches": false}
{"probe": "F02 age_between", "actual": "UnsupportedError: SCOPE-OK: member_inclusion.age_between is not supported by this runner", "expected": "UnsupportedError mentioning age_between", "matches": true}
{"probe": "F02 unrecognized_scope_constraint", "actual": "ValidationError: SCOPE-OK: unknown member_inclusion key 'unrecognized_scope_constraint'", "expected": "ValidationError mentioning unrecognized_scope_constraint", "matches": true}
{"probe": "F03 P11 unauthorized R5 specifically rejected", "actual": true, "expected": true, "matches": true}
{"probe": "F03 ASG verification specifically rejected", "actual": true, "expected": true, "matches": true}
{"probe": "F04 log unavailable leaves main unchanged", "actual": [503, "NOT_RECORDED", true], "expected": [503, "NOT_RECORDED", true], "matches": true}
{"probe": "F04 pending control recovered", "actual": [202, "RECORDED_PENDING_APPLY", false, true], "expected": [202, "RECORDED_PENDING_APPLY", false, true], "matches": true}
{"probe": "F04 missing tail quarantines for exact reason", "actual": [true, true], "expected": [true, true], "matches": true}
{"probe": "F05 replay FORBIDDEN", "actual": [403, null], "expected": [403, null], "matches": true}
{"probe": "F05 replay GONE", "actual": [410, null], "expected": [410, null], "matches": true}
{"probe": "F05 response body specifically rejected", "actual": true, "expected": true, "matches": true}
{"probe": "F06 legitimate supplementary", "actual": [true, "ok"], "expected": [true, "ok"], "matches": true}
{"probe": "F06 duplicate supplementary", "actual": [false, "DUPLICATE_RELATED"], "expected": [false, "DUPLICATE_RELATED"], "matches": true}
{"probe": "F07 inconsistent effective_unknown", "actual": {"status": "NOT_RECOMMENDED", "reasons": ["VERSION_INVALID"]}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["VERSION_INVALID"]}, "matches": true}
{"probe": "F07 missing recheck start", "actual": {"status": "NOT_RECOMMENDED", "reasons": ["RECHECK_START_MISSING"]}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["RECHECK_START_MISSING"]}, "matches": true}
{"probe": "F07 PUBLISHED stale recheck start rejected under row 164", "actual": {"status": "FORMAL", "reasons": []}, "expected": {"status": "NOT_RECOMMENDED", "reasons": ["VERSION_INVALID"]}, "matches": false}
{"matching_probes": 18, "mismatches": 2, "notice": "Evidence probes; mismatches are open findings, not passing acceptance."}
stderr: ''
exit: 0
```
