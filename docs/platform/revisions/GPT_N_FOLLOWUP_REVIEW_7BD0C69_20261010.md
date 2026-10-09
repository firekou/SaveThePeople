# GPT R2_N_FOLLOWUP 固定成果獨立覆核
日期：2026-10-10（Asia/Taipei）；Reviewer：GPT，未修改 Claude 的實作、測試或作者證據。
work_id：STP-PLATFORM-PLAN-001；task_id：STP-PLATFORM-PLAN-001-R2-N-FOLLOWUP；stage：R2_N_FOLLOWUP；evidence_revision：1；round：1/1。
裁定：**CHANGES_REQUESTED**。續作狀態：**BLOCKED_FRANK_DECISION**（一次交付已使用，不自動核發第二輪）。

## 固定座標與授權
- main/base：9a7bd1295e20837786acc45bdab7fb94f5a1b012。
- source_content：02935f528b42a35b3a793d1dec370a5091691288。
- work_packet/handoff：599a25b8882a5a4671d79443670364f127202a9c 的 R2_N_FOLLOWUP_WORK_PACKET_20261010.md revision 1。
- reviewed content_head：7bd0c69705bfda2562a81f7fa751be0e21a4981b；成果分支 claude/tender-allen-sko8pq。
- PR #1 寫入前 head：599a25b8882a5a4671d79443670364f127202a9c；open、Draft、未 merge；它尚未包含兩次 Claude 成果。
- review_record_head：由提交回執與 PR 通知提供，不要求本文自含自己的 commit SHA。merge_candidate_head：未建立本輪整合候選。
- 作者 claim：issuecomment-6086870316；session_01XocTQm3iUWNbtArN7PpZTV；交付：issuecomment-6086976385。
- packet deadline：2026-10-12T18:30:00Z；90 分鐘、一次交付、外部成本 0；repair_rounds_used=1/1。作者約10分鐘為 REPORTED，不能當獨立工時驗證。
- 本輪僅覆核一個新內容 head；不整合作者成果、不 merge main、不啟動網站工程、不使用真實資料或外部 AI。

## 讀取與環境
實際執行 git fetch，非 API ref 冒稱 fetch：
```
git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001 refs/heads/claude/tender-allen-89joyz:refs/remotes/origin/claude/tender-allen-89joyz
```
exit 0；PR 分支 af19c9983620ed248de5e13196162a16297aed21 → 599a25b8882a5a4671d79443670364f127202a9c。
```
git -C stp-review fetch origin refs/heads/claude/tender-allen-sko8pq:refs/remotes/origin/claude/tender-allen-sko8pq
```
exit 0；新取得成果分支。rev-parse exit 0，四 refs 分別為上述 main、handoff、source_content、reviewed content_head 完整 SHA。
隔離 checkout：`git -C stp-review worktree add --detach /workspace/scratch/655bdfd430b7/stp-n-review 7bd0c69705bfda2562a81f7fa751be0e21a4981b` exit 0。
`git merge-base --is-ancestor 02935f528b42a35b3a793d1dec370a5091691288 7bd0c69705bfda2562a81f7fa751be0e21a4981b` exit 0：保留成果祖先。
main README 與四份基線全文讀取；AGENTS.md、CLAUDE.md：MISSING（git show exit128）。讀取新增七份治理檔、工作包、作者回覆、15檔差異、受影響規格、schema、腳本及依賴；只使用標準函式庫，腳本 mutation exec 僅編譯本 repo 隔離副本；未安裝依賴。
PR 全部12則協調留言、claim、delivery 已讀，16 commits核對；review submissions=[]。API核對成果 check_runs=[]；commit status=pending、statuses=[]（不是 CI 綠燈）；PR治理head check_runs=[]。本輪無遠端 CI 或產品 runtime，NOT_RUN。

## Findings 與關閉範圍
| ID | 裁定 | 證據與範圍 |
|---|---|---|
| N-01 | 保持 CLOSED | 遞迴未知 expression key 仍 NOT_RECOMMENDED；既有合法巢狀／SUPPLEMENTARY／三值語意回歸工具通過。 |
| N-02 | CLOSED（本缺口，A/B） | false count=1、min2 FAIL_UNCONFIRMED；8歲就學未知 UNKNOWN；缺鍵無篩選 PASS；C3 與 true 控制由必要工具重現。 |
| N-03 | OPEN，MAJOR | 未 flush、尾端遺失、同步合法控制已改善；**雜湊補記失敗仍可回202，重寫鏈後還原放行**；實際 TimeoutError 未轉為規範503。詳見下列反例。 |
| N-04 | CLOSED（本缺口，A/B） | 結構化排除登錄／責任／代班責任人；合法第二人允許；note矛盾、R4 RV-14擴權抓到；矩陣/API/P9同步。不是產品授權驗收。 |
| N-05 | CLOSED（本缺口，A/B） | 合法 envelope/payload 通過；缺欄位、空用途／fields、錯型別、未知目標、外部 APPLIED拒絕且無寫入；APPLIED關聯以正確原因拒絕。 |
| N-06 | CLOSED（声明修正，A） | ARCHITECTURE §6、BUILD §4.2收窄現行聲明；作者回覆明確局部F批准≠全部缺口關閉，保留歷史。 |

舊 F-01/F-03/F-07 固定差異批准保留；本次 N-03 證據不抹除局部通過，也不能被局部批准遮蔽。

### N-03：雜湊見證缺漏與逾時（沿用原 ID）
嚴重度：MAJOR（還原可遺失已承諾用途撤回）；逾時回應子問題 MINOR。
位置：examples/ref_control.py:120–123（record_hash盡力而為）、273–285（只確認seq、append後無雜湊确认）、333–344（只比對存在hash，缺漏仍放行）；OPERATIONS_AND_PRIVACY §1.3.3 還原步驟3。逾時：request_control捕捉 WitnessUnavailable，未處理 TimeoutError（約273–277）。
根因：持久seq只保護紀錄數量；它不能綁定控制內容。hash補記失敗被允許且没有coverage／pending隔離條件，`verify_controls`又使用被改寫後的紀錄作為驗證基準。現有 CS-18 只測「hash成功記下」的重寫，沒有覆蓋記hash失敗。
重現（下附完整 Reviewer 腳本，使用合法新 payload，不以 schema 422 當見證成功）：
1. NoHash見證沿原 Witness.report持久確認seq；只注入record_hash補記失敗（其原文允許盡力而為）。
2. 合法撤回 c1 的 REMINDERS＋REFERRAL_SHARE；db_fail=True →202 RECORDED_PENDING_APPLY，主庫未套用。
3. 將已記錄payload縮成只撤REMINDERS，重算hash；seq、鏈與schema均合法。
4. recover→quarantined=false、reason=null、referral r1仍SENT；原已承諾停止分享遺失。
正向控制：同樣重寫、原Witness成功記hash時→quarantined=true、LOG_REWRITTEN_AT_1。不是任意錯誤造成失败。
另注入Witness.report拋 TimeoutError：實際向外拋例外，未回(503,WITNESS_UNCONFIRMED)。狀態未寫入，但不符合本包明確逾時回應。
最小修法：將確認綁定到seq＋控制內容hash，或對未完成hash見證的紀錄保留可持久的pending狀態，還原缺锚一律隔離；不得以只比對已存在hash宣稱整段重寫防護。主庫套用／200或202之前清楚定义hash確認與失敗回應；APPLIED非必要标记不能造成對控制意圖安全性誤判。同步文件、參考模擬及案例；timeout明確轉成未確認／503。
驗收證據：合法同步200、主庫失敗202後重套、未flush／timeout／hash確認失敗、尾端遺失、hash缺漏後重寫（目的撤回不得消失）、合法重試與REDACT/HARD_DELETE；每項核對正確隔離原因。移除缺锚／確認防護，反例須按預期變成放行；不能靠不合法payload422通過。全部五工具與四基線diff重跑。

## 有界續作決策包（PREPARED，非 READY 派工）
唯一問題：是否授權同一 task/stage **增加一次僅 N-03 的最小修補交付**？
建議：將本 stage repair_round_limit 由1提高到2，已用1保留；額外最多30分鐘、自檢含在内、外部成本0；deadline仍2026-10-12T18:30:00Z，不延長舊F包。不更名work_id重置次數。
source固定7bd0c69705bfda2562a81f7fa751be0e21a4981b；只限OPERATIONS_AND_PRIVACY、ARCHITECTURE必要順序文字、examples/ref_control.py、control_cases.json、check_examples.py、tools/test_checks.py與本stage作者補充回覆。排除四基線、README、既有Reviewer證據、產品／部署／權限放寬／真實資料／Secret／外部聯絡。Claude執行、GPT非作者覆核；保留non-force祖先，結果分支在claim明載、交PR #1固定SHA。
風險／成本：只文件與純模擬，未驗真實供應商；需要一次輪次例外，無金錢成本。未授權則保持BLOCKED_FRANK_DECISION，不要求Claude擅自補第二輪。
停止／恢復：授權需明確涵蓋本task、N-03、次數、30分鐘與既有期限；授權后GPT核對live refs/競爭claim再具體化READY工單；新內容、本期限到期、資源超限或外部能力需求均停止。網站D1另有未授權提案，本次唯一必要決策不綁定網站開工。

## 目標與未證明事項
來源：origin/main @9a7bd1295e20837786acc45bdab7fb94f5a1b012，v0.1，2026-10-03。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。
方向：前進（四個N缺口可關閉，見證剩餘風險已具體化）；不是服務成果。P0～P3沒有新增真實服務證據；D1～D4/WP尚未開工。没有新增實際取得幫助家庭成果；試點起始日UNKNOWN。工程人日仍規劃估算，不当预算或已用Agent人日。
已證明：A文件政策對應與B參考純邏輯的指定範圍。C產品/DB、D合成網站E2E、E真實初篩、F真實個案服務、G實際取得、G1～G8、AS-1～AS-6皆未驗收；法律U-23与合作容量仍未確認。沒有main merge、網站開工、部署或真實資料授权。

## 附錄：實際必要命令（REPRODUCED）
stdout/stderr/exit依本輪獨立執行，不複製作者數字：

```json
[
  {
    "command": "python3 docs/platform/examples/check_examples.py",
    "exit_code": 0,
    "stdout": "OK: 1119 checks passed\n",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  },
  {
    "command": "python3 docs/platform/tools/gen_state_machines.py --check",
    "exit_code": 0,
    "stdout": "OK: 6 state machines, 86 transitions, doc in sync\n",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  },
  {
    "command": "python3 docs/platform/tools/gen_permissions.py --check",
    "exit_code": 0,
    "stdout": "OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync\n",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  },
  {
    "command": "python3 docs/platform/tools/test_checks.py",
    "exit_code": 0,
    "stdout": "OK: test_checks 113 counterexample checks passed\n",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  },
  {
    "command": "python3 docs/platform/tools/check_docs.py",
    "exit_code": 0,
    "stdout": "OK: 2009 doc checks passed\n",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  },
  {
    "command": "git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 7bd0c69705bfda2562a81f7fa751be0e21a4981b -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md",
    "exit_code": 0,
    "stdout": "",
    "stderr": "",
    "content_head": "7bd0c69705bfda2562a81f7fa751be0e21a4981b"
  }
]
```

## 附錄：獨立反例結果（REPRODUCED）
27項觀察，25符合預期、2項不符合即N-03上述剩餘缺口。診斷腳本exit0不代表批准。
```json
[
  {
    "name": "N02 false min2",
    "observed": [
      "FAIL_UNCONFIRMED",
      1
    ],
    "expected": [
      "FAIL_UNCONFIRMED",
      1
    ],
    "passed": true
  },
  {
    "name": "N02 eligible age unknown school",
    "observed": "UNKNOWN",
    "expected": "UNKNOWN",
    "passed": true
  },
  {
    "name": "N02 absent filter",
    "observed": "PASS",
    "expected": "PASS",
    "passed": true
  },
  {
    "name": "N01 unknown recursive node",
    "observed": "NOT_RECOMMENDED",
    "expected": "NOT_RECOMMENDED",
    "passed": true
  },
  {
    "name": "N03 Witness response",
    "observed": [
      202,
      "RECORDED_PENDING_APPLY"
    ],
    "expected": [
      202,
      "RECORDED_PENDING_APPLY"
    ],
    "passed": true
  },
  {
    "name": "N03 Witness tail loss quarantine",
    "observed": true,
    "expected": true,
    "passed": true
  },
  {
    "name": "N03 Unflushed response",
    "observed": [
      503,
      "WITNESS_UNCONFIRMED"
    ],
    "expected": [
      503,
      "WITNESS_UNCONFIRMED"
    ],
    "passed": true
  },
  {
    "name": "N03 Unflushed tail loss quarantine",
    "observed": false,
    "expected": false,
    "passed": true
  },
  {
    "name": "N03 Witness rewrite after hash persistence failure",
    "observed": {
      "response": 202,
      "quarantined": true,
      "reason": "LOG_REWRITTEN_AT_1",
      "referral": "SENT"
    },
    "expected": {
      "response": 202,
      "quarantined": true,
      "reason": "LOG_REWRITTEN_AT_1",
      "referral": "SENT"
    },
    "passed": true
  },
  {
    "name": "N03 NoHash rewrite after hash persistence failure",
    "observed": {
      "response": 202,
      "quarantined": false,
      "reason": null,
      "referral": "SENT"
    },
    "expected": {
      "response": 202,
      "quarantined": true,
      "reason": "LOG_REWRITTEN_AT_1",
      "referral": "SENT"
    },
    "passed": false
  },
  {
    "name": "N03 actual timeout response",
    "observed": [
      "TimeoutError",
      "synthetic witness timeout"
    ],
    "expected": [
      503,
      "WITNESS_UNCONFIRMED"
    ],
    "passed": false
  },
  {
    "name": "N04 baseline",
    "observed": [],
    "expected": [],
    "passed": true
  },
  {
    "name": "N04 REG",
    "observed": false,
    "expected": false,
    "passed": true
  },
  {
    "name": "N04 OWN",
    "observed": false,
    "expected": false,
    "passed": true
  },
  {
    "name": "N04 SUB",
    "observed": false,
    "expected": false,
    "passed": true
  },
  {
    "name": "N04 PEER",
    "observed": true,
    "expected": true,
    "passed": true
  },
  {
    "name": "N04 note contradiction rejection",
    "observed": true,
    "expected": true,
    "passed": true
  },
  {
    "name": "N04 RV14 widening rejected",
    "observed": true,
    "expected": true,
    "passed": true
  },
  {
    "name": "N05 type only",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 empty purposes",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 wrong type",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 unknown target",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 empty fields",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 external APPLIED",
    "observed": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "expected": [
      422,
      "INVALID_CONTROL",
      0,
      0
    ],
    "passed": true
  },
  {
    "name": "N05 legal envelope",
    "observed": [],
    "expected": [],
    "passed": true
  },
  {
    "name": "N05 APPLIED relation reason",
    "observed": true,
    "expected": true,
    "passed": true
  }
]
```

## 附錄：Reviewer重現腳本
將固定成果checkout放在stp-n-review，從其父目錄執行python3 stp_n_probes.py；stdout見上，stderr空，exit0。只在隔離副本／合成資料執行，沒有改作者證據。
```python
import sys,json,copy,types
from pathlib import Path
ROOT=Path('stp-n-review').resolve();sys.path[:0]=[str(ROOT/'docs/platform/examples'),str(ROOT/'docs/platform/tools')]
import ref_engine as E, ref_control as C, gen_permissions as P, schema_lite as S
read=lambda p:json.loads((ROOT/'docs/platform'/p).read_text())
out=[]
def check(name,got,want):
 out.append(dict(name=name,observed=got,expected=want,passed=got==want))
res=read('examples/synthetic_resources.json');scopes={s['scope_key']:s for s in res['household_scopes']};hh=read('examples/synthetic_households.json')['households'][0]
c={'criterion_id':'REVIEW','operator':'COUNT_MEMBERS_WHERE','scope_key':'SCOPE-CO','input_keys':['person.age','person.in_school'],'threshold':{'where':{'age_between':[0,17],'in_school':False},'min_count':2},'min_confirmation_for_fail':'C2'}
x=E.eval_criterion(c,hh,scopes,res['regions']);check('N02 false min2',[x['result'],x['derived']['count']],['FAIL_UNCONFIRMED',1])
h=copy.deepcopy(hh);h['persons'][1]['facts']['person.in_school']={'unknown':True,'confirmation_level':'C0'}
check('N02 eligible age unknown school',E.eval_criterion(c,h,scopes,res['regions'])['result'],'UNKNOWN')
cc=copy.deepcopy(c);del cc['threshold']['where']['in_school'];check('N02 absent filter',E.eval_criterion(cc,h,scopes,res['regions'])['result'],'PASS')
r=copy.deepcopy(res['resources'][0]);r['rule']['combinator']='CUSTOM';r['rule']['expression']={'op':'ALL','children':[k['criterion_id'] for k in r['rule']['criteria']],'unseen_semantics':'EXCLUDE_IF_UNKNOWN'}
check('N01 unknown recursive node',E.recommendation_status(r,{s['id']:s for s in res['sources']},'2026-10-03',scopes)['status'],'NOT_RECOMMENDED')
initial=read('examples/control_cases.json')['initial_state'];payload={'type':'CONSENT_REVOKE','consent_id':'c1','purposes':['REMINDERS','REFERRAL_SHARE']}
class Unflushed(C.Witness):
 def report(self,seq):self.pending_seq=seq
class NoHash(C.Witness):
 def record_hash(self,seq,h):pass # allowed best-effort hash persistence failure, seq is confirmed
class Timeout(C.Witness):
 def report(self,seq):raise TimeoutError('synthetic witness timeout')
for cls in [C.Witness,Unflushed]:
 log,w=C.ControlLog(),cls();code,why,st=C.request_control(C.new_state(initial),log,w,payload,db_fail=True)
 check('N03 '+cls.__name__+' response',[code,why],[202,'RECORDED_PENDING_APPLY'] if cls==C.Witness else [503,'WITNESS_UNCONFIRMED'])
 log.entries.clear();rec=C.recover(initial,log,w)
 check('N03 '+cls.__name__+' tail loss quarantine',rec['quarantined'],cls==C.Witness)
for cls in [C.Witness,NoHash]:
 log,w=C.ControlLog(),cls();code,why,st=C.request_control(C.new_state(initial),log,w,payload,db_fail=True)
 e=log.entries[0];e['payload']['purposes']=['REMINDERS'];e['hash']=C._hash(e['prev_hash'],C._body(e))
 rec=C.recover(initial,log,w)
 check('N03 '+cls.__name__+' rewrite after hash persistence failure',{'response':code,'quarantined':rec['quarantined'],'reason':rec['reason'],'referral':rec['state']['referrals']['r1']['status']},{'response':202,'quarantined':True,'reason':'LOG_REWRITTEN_AT_1','referral':'SENT'})
try:
 result=C.request_control(C.new_state(initial),C.ControlLog(),Timeout(),payload)
 got=list(result[:2])
except Exception as e:got=[type(e).__name__,str(e)]
check('N03 actual timeout response',got,[503,'WITNESS_UNCONFIRMED'])
d=P.load();machines=read('state_machines.json')['machines'];check('N04 baseline',P.policy_problems(d,machines),[])
a=next(a for a in d['api'] if a['endpoint'].endswith('/verify'))
record={'registrant':'REG','case_owner':'OWN','case_owner_delegates':['SUB']}
for who,want in [('REG',False),('OWN',False),('SUB',False),('PEER',True)]:check('N04 '+who,P.verifier_allowed(a,who,record)[0],want)
x=copy.deepcopy(d);next(a for a in x['api'] if a['endpoint'].endswith('/verify'))['note']='責任人可驗證'
check('N04 note contradiction rejection',any('note must equal' in p for p in P.policy_problems(x,machines)),True)
x=copy.deepcopy(d);x['matrix']['resource_internal']['R4'][0]['transition_limits'].append('RV-14');check('N04 RV14 widening rejected',any('lists RV-14' in p for p in P.policy_problems(x,machines)),True)
for p,label in [({'type':'CONSENT_REVOKE'},'type only'),(dict(payload,purposes=[]),'empty purposes'),(dict(payload,purposes='REMINDERS'),'wrong type'),(dict(payload,consent_id='NO_SUCH_SYNTHETIC'),'unknown target'),({'type':'REDACT','table':'objects','id':'doc1','fields':[]},'empty fields'),({'type':'APPLIED','ref':1},'external APPLIED')]:
 log,w=C.ControlLog(),C.Witness();code,why,st=C.request_control(C.new_state(initial),log,w,p)
 check('N05 '+label,[code,why,len(log.entries),w.max_seq],[422,'INVALID_CONTROL',0,0])
log=C.ControlLog();log.append({'type':'HARD_DELETE','table':'objects','id':'doc1'});log.append({'type':'APPLIED','ref':1})
check('N05 legal envelope',S.validate(log.entries[0],S.load_schema('control_record')),[])
try:log.append({'type':'APPLIED','ref':2});got='accepted'
except C.InvalidControl as e:got=str(e)
check('N05 APPLIED relation reason','earlier non-APPLIED' in got,True)
print(json.dumps(out,indent=2,ensure_ascii=False));Path('stp_n_probes.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))

```
