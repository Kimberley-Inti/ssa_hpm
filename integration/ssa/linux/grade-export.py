#!/usr/bin/env python3
"""Accept full-result export on actual Rocket Linux, then unchanged stage6 gates."""
import argparse,json,pathlib,subprocess
from export_results import parse,normalize
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',type=int,required=True);p.add_argument('--users',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();o=a.out_dir;o.mkdir(parents=True,exist_ok=True)
s=normalize(a.log.read_text(errors='replace'));q=parse(s);(o/'results.json').write_text(json.dumps(q,indent=2)+'\n');c={};check=lambda k,v:c.update({k:bool(v)})
check('native_exit_powerdown',a.exit_code==0 and 'reboot: Power down' in s and 'FAIL' not in s and 'Kernel panic' not in s)
check('all_exports_valid',q['valid']);check('all_pools_released',q['sessions'] and all(x['released'] for x in q['sessions']))
check('all_four_counters_identified',{x['header']['abi'] for x in q['sessions']}=={1,2})
start=s.find('SSA_RESULT_EXPORT_SUITE_START');end=s.find('SSA_RESULT_EXPORT_SUITE_END');check('fixture_boundaries',start>=0 and end>start and s[start:end].count('SSA RESULT CASE PASS')==4)
users=json.loads(a.users.read_text());sy=users['init']['symbols'];exports={}
for line in s[start:end].splitlines():
 if line.startswith('SSA_EXPORT '):
  import re
  d={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)};exports[d['test']]=d
check('four_target_sessions',set(exports)=={11,12,13,14});by={x['header']['session']:x for x in q['sessions']}
for test,count,abi,reason in [(11,41,2,'exit'),(12,2,1,'stop'),(13,0,1,'stop'),(14,2,2,'exit')]:
 if test not in exports:continue
 e=exports[test];x=by.get(e['session']);check(f'test{test}_parsed',x is not None)
 if x is None:continue
 h=x['header'];rr=x['records'];check(f'test{test}_count_identity',h['total']==count and len(rr)==count and h['abi']==abi and h['reason']==reason and h['pid']==e['pid'] and x['released'])
 check(f'test{test}_ordered_ids',[r['id'] for r in rr]==list(range(1,count+1)))
 if test==11:
  check('beyond_old32_limit',x['complete'] and x['chunks']==3 and count>32)
  check('large_exact_tree',len(rr)==41 and rr[0]['parent']==0 and rr[0]['callee']==sy['export_parent'] and all(r['parent']==1 and r['callee']==sy['leaf%02d'%i] and r['open']==0 and r['instret']>0 for i,r in enumerate(rr[1:])))
  check('repeated_context_reused',len(rr)==41 and rr[1]['instret']>=max(r['instret'] for r in rr[2:]))
 elif test==12:check('small_explicit_stop_tree',x['complete'] and len(rr)==2 and [r['parent'] for r in rr]==[0,1] and [r['callee'] for r in rr]==[sy['export_small'],sy['leaf00']])
 elif test==13:check('zero_clean_terminal',x['complete'] and x['chunks']==0 and not rr)
 else:check('open_not_fabricated_return',not x['complete'] and h['status']==1 and h['depth']==1 and len(rr)==2 and rr[0]['open']==1 and rr[0]['instret']==0 and rr[0]['dtlb']==0 and rr[1]['open']==0 and rr[1]['instret']>0 and [r['callee'] for r in rr]==[sy['export_open'],sy['leaf00']])
# The same boot runs original stage6 event/exec/process fixture after the prefix.
# Preserve actual boot profile and remove only the separately accepted new fixture.
base=o/'regression';base.mkdir(exist_ok=True)
if start>=0 and end>start:
 f=base/'console.txt';f.write_text(s[:start]+s[end+len('SSA_RESULT_EXPORT_SUITE_END'):]);code=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('grade-events.py')),str(f),'--exit-code',str(a.exit_code),'--users',str(a.users),'--out-dir',str(base)]).returncode
 check('stage6_event_lifecycle_process_regression',code==0)
else:check('stage6_event_lifecycle_process_regression',False)
r={'passed':all(c.values()),'checks':c,'source_log':str(a.log),'results':'results.json','sessions':len(q['sessions']),'target_sessions':exports};(o/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':len(c),'failed':[k for k,v in c.items() if not v]},indent=2));raise SystemExit(0 if r['passed'] else 1)
