# GPT 第三輪獨立覆核與候選整合記錄
work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP；stage R2_N_FOLLOWUP；round 3/3。
verdict **APPROVED，僅本次 N-03 兩條控制意圖繞過的文件／純邏輯修補差異**；N-03該缺口 CLOSED。非全產品或真實備份整合批准。
executor Claude session_01MvUGYirGBtHVdHk3mYxAkh；reviewer GPT，未製作或修改原始實作/作者證據。
base/origin/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012；source c563865173a402c71af4c2b3ad3c46edac771200；reviewed_content_head ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9；candidate_before_write 286f2960590f4ab26625a3b99feb34760facf28c；review_at 2026-10-11T18:06:00Z。review_record_head/merge_candidate_head另由交接回執提供，不要求正文含自身SHA。

## 調查與重現
已fetch origin/main、claude/stp-platform-plan-001、claude/tender-allen-c9p5u1、claude/tender-allen-sko8pq（exit0）；rev-parse 分別確認 main上述base、PR286f2960590f4ab26625a3b99feb34760facf28c、result上述head。指令：
```sh
git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001 refs/heads/claude/tender-allen-c9p5u1:refs/remotes/origin/claude/tender-allen-c9p5u1 refs/heads/claude/tender-allen-sko8pq:refs/remotes/origin/claude/tender-allen-sko8pq
git -C stp-review rev-parse origin/main origin/claude/stp-platform-plan-001 origin/claude/tender-allen-c9p5u1
git -C stp-review worktree add --detach ../stp-round3-review ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9
git -C stp-review diff c563865173a402c71af4c2b3ad3c46edac771200 ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9 --stat
```
已讀 main README與四份v0.1基線、最新續作入口/當責規則/round3工單、PR全部20則留言與 reviews空，source→result 7檔diff、第三輪回覆及必要腳本/依賴。AGENTS.md、CLAUDE.md MISSING，git show各exit128。隔離測試無新增依賴、費用、外部政策蒐集、Secret或真實資料。

| 實際命令（stp-round3-review） | exit | stdout | stderr |
|---|---:|---|---|
| `python3 docs/platform/examples/check_examples.py` | 0 | OK: 1306 checks passed | 空 |
| `python3 docs/platform/tools/gen_state_machines.py --check` | 0 | OK: 6 state machines, 86 transitions, doc in sync | 空 |
| `python3 docs/platform/tools/gen_permissions.py --check` | 0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | 空 |
| `python3 docs/platform/tools/test_checks.py` | 0 | OK: test_checks 136 counterexample checks passed | 空 |
| `python3 docs/platform/tools/check_docs.py` | 0 | OK: 2009 doc checks passed | 空 |
| `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` | 0 | 空 | 空 |

以上為REPRODUCED，未复制作者1306/136等自述。check-runs exact result API total_count=0；遠端CI NOT_RUN，產品/DB/真實備份/法律 NOT_VERIFIED。

## N-03 裁定與邊界
原始意圖由見證於寫入前將seq→完整payload摘要綁定；同seq不同payload拒絕且不覆寫。補錨點先比對此獨立綁定；還原含APPLIED也比對。縮減用途→無關合法請求、APPLIED偽裝，皆503 INTENT_MISMATCH且不新增紀錄/變更主庫；還原INTENT_MISMATCH_AT_1隔離。缺原始綁定亦隔離。正常200、已錨定DB失敗202、原始完整意圖合法重試後r1 CANCELLED，TimeoutError轉503均重現。
17個独立斷言17符合，包含將模擬見證持久欄位重建至新Witness的caller重啟控制；這不是實際程序/獨立服務/DB持久性證明。獨立移除兩道原始意圖檢查的mutation重現200、還原放行、r1 SENT，命中正確舊漏洞，非以任意例外充數。
作者CS-23 reason由缺錨改為更早意圖不符與mutation覆蓋調整，語意合理；未弱化預期。payload綁定保護控制內容，不宣稱已驗證完整envelope時間戳的獨立持久綁定或供應商不可覆寫能力；這些留產品安全驗收。受控恢復SOP、見證保留/權限、DB原子性、真實備份、U-23法律仍未驗收。此批准不能解除G/AS真實資料閘門。

REVIEWER_EVIDENCE原碼與輸出（合成）如下；腳本初版有縮排錯誤，修正的是GPT自己的隔離探針，未動作者檔案；以下最终成功执行exit0，17/17。
```python
"""GPT REVIEWER_EVIDENCE; synthetic fixtures; exact ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9."""
import sys,json,pathlib,copy,types
sys.path.insert(0,str(pathlib.Path('stp-round3-review/docs/platform/examples').resolve()))
import ref_control as R
initial=json.loads(pathlib.Path('stp-round3-review/docs/platform/examples/control_cases.json').read_text())['initial_state']
rec={'type':'CONSENT_REVOKE','consent_id':'c1','purposes':['REMINDERS','REFERRAL_SHARE']}; rows=[]
def check(name,want,got):rows.append(dict(name=name,expected=want,actual=got,matches=want==got))
def setup():return R.new_state(initial),R.ControlLog(),R.Witness()
def rechain(log):
 prev='0'*64
 for e in log.entries:e['prev_hash']=prev;e['hash']=R._hash(prev,R._body(e));prev=e['hash']
def restart(wit):
 fresh=R.Witness();fresh.max_seq=wit.max_seq;fresh.hash_at=copy.deepcopy(wit.hash_at);fresh.intent_at=copy.deepcopy(wit.intent_at);return fresh
for kind in ['reduced','APPLIED']:
 st,log,wit=setup();wit.hash_fail_next=1
 check(kind+' initial503',(503,'ANCHOR_UNCONFIRMED'),R.request_control(st,log,wit,rec)[:2])
 log.entries[0]['payload']=dict(rec,purposes=['REMINDERS']) if kind=='reduced' else {'type':'APPLIED','ref':0};rechain(log)
 wit=restart(wit);before=copy.deepcopy((st,log.entries,wit.hash_at,wit.intent_at,wit.max_seq))
 check(kind+' nextrequest',(503,'INTENT_MISMATCH'),R.request_control(st,log,wit,{'type':'HARD_DELETE','table':'objects','id':'doc1'})[:2])
 check(kind+' rejection no writes',True,before==(st,log.entries,wit.hash_at,wit.intent_at,wit.max_seq))
 out=R.recover(initial,log,wit);check(kind+' recover',(True,'INTENT_MISMATCH_AT_1','SENT'),(out['quarantined'],out['reason'],out['state']['referrals']['r1']['status']))
st,log,wit=setup();wit.hash_fail_next=1;R.request_control(st,log,wit,rec);wit=restart(wit)
code,why,st=R.request_control(st,log,wit,rec);out=R.recover(initial,log,wit)
check('legitimate caller restart retry',(200,False,'CANCELLED'),(code,out['quarantined'],out['state']['referrals']['r1']['status']))
for db_fail in [False,True]:
 st,log,wit=setup();code,why,st=R.request_control(st,log,wit,rec,db_fail=db_fail);out=R.recover(initial,log,wit)
 check('normal/DB-failed '+str(db_fail),(202 if db_fail else 200,False,'CANCELLED'),(code,out['quarantined'],out['state']['referrals']['r1']['status']))
for mode,status in [('timeout_next','WITNESS_UNCONFIRMED'),('hash_timeout_next','ANCHOR_UNCONFIRMED')]:
 st,log,wit=setup();setattr(wit,mode,1);code,why,new=R.request_control(st,log,wit,rec)
 check(mode,(503,status,True),(code,why,new==st))
st,log,wit=setup();log.fail_next=1;R.request_control(st,log,wit,rec);bound=copy.deepcopy(wit.intent_at)
check('reserved seq different intent',(503,'INTENT_CONFLICT'),R.request_control(st,log,wit,dict(rec,purposes=['REMINDERS']))[:2]);check('binding not overwritten',bound,wit.intent_at)
st,log,wit=setup();wit.hash_fail_next=1;R.request_control(st,log,wit,rec);wit.intent_at={};out=R.recover(initial,log,wit)
check('missing persistent binding',(True,'INTENT_MISMATCH_AT_1'),(out['quarantined'],out['reason']))
# Independent mutation: remove both intent guards, rerun combined A, ensure exact old unsafe outcome.
src=pathlib.Path('stp-round3-review/docs/platform/examples/ref_control.py').read_text()
src=src.replace('e["seq"] > wit.max_seq or wit.intent_at.get(e["seq"]) != intent_digest(e["payload"])','e["seq"] > wit.max_seq').replace('if wit.intent_at.get(e["seq"]) != intent_digest(e["payload"]):','if False:')
m=types.ModuleType('control_mut');m.__file__=R.__file__;exec(compile(src,R.__file__,'exec'),m.__dict__)
st=m.new_state(initial);log=m.ControlLog();wit=m.Witness();wit.hash_fail_next=1;m.request_control(st,log,wit,rec)
log.entries[0]['payload']=dict(rec,purposes=['REMINDERS']);rechain(log);code=m.request_control(st,log,wit,{'type':'HARD_DELETE','table':'objects','id':'doc1'})[0];out=m.recover(initial,log,wit)
check('removed guards reproduce correct unsafe reason',(200,False,'SENT'),(code,out['quarantined'],out['state']['referrals']['r1']['status']))
print(json.dumps(dict(head='ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9',checks=len(rows),matches=sum(x['matches'] for x in rows),results=rows),ensure_ascii=False,indent=2))
```
```json
{
  "head": "ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9",
  "checks": 17,
  "matches": 17,
  "results": [
    {
      "name": "reduced initial503",
      "expected": [
        503,
        "ANCHOR_UNCONFIRMED"
      ],
      "actual": [
        503,
        "ANCHOR_UNCONFIRMED"
      ],
      "matches": true
    },
    {
      "name": "reduced nextrequest",
      "expected": [
        503,
        "INTENT_MISMATCH"
      ],
      "actual": [
        503,
        "INTENT_MISMATCH"
      ],
      "matches": true
    },
    {
      "name": "reduced rejection no writes",
      "expected": true,
      "actual": true,
      "matches": true
    },
    {
      "name": "reduced recover",
      "expected": [
        true,
        "INTENT_MISMATCH_AT_1",
        "SENT"
      ],
      "actual": [
        true,
        "INTENT_MISMATCH_AT_1",
        "SENT"
      ],
      "matches": true
    },
    {
      "name": "APPLIED initial503",
      "expected": [
        503,
        "ANCHOR_UNCONFIRMED"
      ],
      "actual": [
        503,
        "ANCHOR_UNCONFIRMED"
      ],
      "matches": true
    },
    {
      "name": "APPLIED nextrequest",
      "expected": [
        503,
        "INTENT_MISMATCH"
      ],
      "actual": [
        503,
        "INTENT_MISMATCH"
      ],
      "matches": true
    },
    {
      "name": "APPLIED rejection no writes",
      "expected": true,
      "actual": true,
      "matches": true
    },
    {
      "name": "APPLIED recover",
      "expected": [
        true,
        "INTENT_MISMATCH_AT_1",
        "SENT"
      ],
      "actual": [
        true,
        "INTENT_MISMATCH_AT_1",
        "SENT"
      ],
      "matches": true
    },
    {
      "name": "legitimate caller restart retry",
      "expected": [
        200,
        false,
        "CANCELLED"
      ],
      "actual": [
        200,
        false,
        "CANCELLED"
      ],
      "matches": true
    },
    {
      "name": "normal/DB-failed False",
      "expected": [
        200,
        false,
        "CANCELLED"
      ],
      "actual": [
        200,
        false,
        "CANCELLED"
      ],
      "matches": true
    },
    {
      "name": "normal/DB-failed True",
      "expected": [
        202,
        false,
        "CANCELLED"
      ],
      "actual": [
        202,
        false,
        "CANCELLED"
      ],
      "matches": true
    },
    {
      "name": "timeout_next",
      "expected": [
        503,
        "WITNESS_UNCONFIRMED",
        true
      ],
      "actual": [
        503,
        "WITNESS_UNCONFIRMED",
        true
      ],
      "matches": true
    },
    {
      "name": "hash_timeout_next",
      "expected": [
        503,
        "ANCHOR_UNCONFIRMED",
        true
      ],
      "actual": [
        503,
        "ANCHOR_UNCONFIRMED",
        true
      ],
      "matches": true
    },
    {
      "name": "reserved seq different intent",
      "expected": [
        503,
        "INTENT_CONFLICT"
      ],
      "actual": [
        503,
        "INTENT_CONFLICT"
      ],
      "matches": true
    },
    {
      "name": "binding not overwritten",
      "expected": {
        "1": "0cb96b938cd2068a8d93544fcba7346a66a2a13959d32a85ac5b2e1b7f0d37c4"
      },
      "actual": {
        "1": "0cb96b938cd2068a8d93544fcba7346a66a2a13959d32a85ac5b2e1b7f0d37c4"
      },
      "matches": true
    },
    {
      "name": "missing persistent binding",
      "expected": [
        true,
        "INTENT_MISMATCH_AT_1"
      ],
      "actual": [
        true,
        "INTENT_MISMATCH_AT_1"
      ],
      "matches": true
    },
    {
      "name": "removed guards reproduce correct unsafe reason",
      "expected": [
        200,
        false,
        "SENT"
      ],
      "actual": [
        200,
        false,
        "SENT"
      ],
      "matches": true
    }
  ]
}
```

## 候選整合：一般技術續作決策
依Frank 2026-10-12一般技術、可逆操作与有限續作委託，以及有效當責規則的通過後候選整合要求，GPT批准將歷史已審F修補與N修補整合到既有Draft PR候選；不merge main、不开auto-merge、不改保護/策略/部署。不是重新製作Claude內容。
已在隔離candidate_preview執行：
```sh
git -C stp-review worktree add --detach ../stp-candidate-preview origin/claude/stp-platform-plan-001
git -C stp-candidate-preview -c user.name='GPT Controller' -c user.email='<reviewer-noreply-placeholder>' merge --no-commit --no-ff ebfad3dd2c1ab9e9af1df8c9cd401a1bce3272d9
```
各exit0，無衝突。22個作者路徑逐位元與ebfad固定成果一致；候選上的全部治理文件保留。整合後相同5命令再跑exit0，輸出仍1306、6/86、25/143/42/12、136、2009。這是已審內容的整合檢查，不新增第二個未審內容head。原始作者 commits保留；遠端以雙parent提交（候選286f296、作者ebfad）與non-force expected-head更新。實際提交與遠端驗證見交接comment。

## 速度、輪次、下一checkpoint
派工POSTED 2026-10-11T17:06:51Z；ACK 17:07:49Z；DELIVERED 17:09:57Z；review_at18:06:00Z。待審56分03秒，未超1小時；作者預估開始17:10Z比實際交付晚，工時約20分鐘仍REPORTED，用GitHub時間對帳，不虛構已驗證工時。
repair_rounds_used 3/3保留，deadline2026-10-12T18:30:00Z前交付；不派第四輪、該有限修補checkpoint COMPLETE。N-01/02/04/05/06歷史局部關閉保留，不以此宣告整個平台通過。
已做加速：優先審未審成果、獨立重啟/組合/破壞控制、同輪試整合並具體化D1 readiness工作。最新工單 GPT_D1_READINESS_PACKET_20261012.md：下一負責人Claude，核對環境/六項開工條件而非無授權產品實作；交付後GPT決定技術缺口与有界下一步。不得把舊候選文件的人力/產品開工PREPARED狀態默認為已核准，仍須逐項證據。
服務P0～P3無新增證據；工程D1～D4/WP無產品交付；無家庭新增取得成果。無launcher可调用證據，不因GitHubPOSTED就宣稱STARTED。Frank本輪不需搬運Prompt或例行放行。

## GPT治理修正（2026-10-12）
D1交付指出本報告提交者地址觸發email樣式掃描。GPT獨立重現check_docs exit1（1/2086），是GPT自己的治理回歸，不是Claude失敗。上述歷史命令email值改以placeholder展示；原實際命令與本文歷史版本可由bf8c5ed commit取回，未改作者程式、測試或白名單。修正後完整五項結果見D1覆核與PR回執；不以此自批任何作者產品。
