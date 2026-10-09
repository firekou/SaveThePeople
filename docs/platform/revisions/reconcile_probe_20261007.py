import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'docs/platform/examples'), str(ROOT/'docs/platform/tools')]
import ref_engine as E
import ref_control as C
import schema_lite as S
import gen_permissions as P

def read(path):
    return json.loads((ROOT/path).read_text())

res = read('docs/platform/examples/synthetic_resources.json')
scopes = {s['scope_key']: s for s in res['household_scopes']}
sources = {s['id']: s for s in res['sources']}
out = {}
r = copy.deepcopy(res['resources'][0])
r['rule']['combinator'] = 'CUSTOM'
r['rule']['expression'] = {'op': 'ALL', 'children': [c['criterion_id'] for c in r['rule']['criteria']], 'unseen_semantics': 'EXCLUDE_IF_UNKNOWN'}
out['N-01 unknown node key'] = E.recommendation_status(r, sources, '2026-10-03', scopes)
hh = read('docs/platform/examples/synthetic_households.json')['households'][0]
c = {'criterion_id':'REVIEW-COUNT', 'operator':'COUNT_MEMBERS_WHERE', 'scope_key':'SCOPE-CO', 'input_keys':['person.age','person.in_school'], 'threshold':{'where':{'age_between':[0,17], 'in_school':False}, 'min_count':2}, 'min_confirmation_for_fail':'C2'}
out['N-02 false filter'] = E.eval_criterion(c, hh, scopes, res['regions'])
hh = copy.deepcopy(hh)
hh['persons'][1]['facts']['person.in_school'] = {'unknown':True, 'confirmation_level':'C0'}
out['N-02 unknown school'] = E.eval_criterion(c, hh, scopes, res['regions'])
initial = read('docs/platform/examples/control_cases.json')['initial_state']
class PeriodicWitness(C.Witness):
    def report(self, seq):
        self.pending_seq = seq  # documented periodic update has not flushed yet
for wt in (C.Witness, PeriodicWitness):
    log, wit = C.ControlLog(), wt()
    code, status, st = C.request_control(C.new_state(initial), log, wit, {'type':'CONSENT_REVOKE','consent':'c1','purposes':['REMINDERS','REFERRAL_SHARE']}, db_fail=True)
    log.entries.clear()
    recovered = C.recover(initial, log, wit)
    out['N-03 '+wt.__name__] = {'request':[code,status], 'quarantined':recovered['quarantined'], 'reason':recovered['reason'], 'notification':recovered['state']['notifications']['n1']['status'], 'referral':recovered['state']['referrals']['r1']['status']}
perm = P.load()
machines = read('docs/platform/state_machines.json')['machines']
out['N-04 baseline policy'] = P.policy_problems(perm, machines)
for api in perm['api']:
    if api['endpoint'].endswith('/verify'):
        api['note'] = 'R4 可驗證自己登錄的成果；責任人也可驗證'
out['N-04 self verification note mutation'] = P.policy_problems(perm, machines)
out['N-04 P9'] = [p for p in perm['pages'] if p['page']=='P9']
out['N-05 incomplete control'] = S.validate({'type':'CONSENT_REVOKE'}, S.load_schema('control_record'))
out['N-05 documented envelope fields'] = S.validate({'type':'CONSENT_REVOKE','consent_id':'c1','seq':1,'prev_hash':'0'*64,'recorded_at':'2026-10-07T12:00:00Z','purposes':['REMINDERS']}, S.load_schema('control_record'))
print(json.dumps(out, ensure_ascii=False, indent=2))
