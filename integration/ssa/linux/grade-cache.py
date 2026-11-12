#!/usr/bin/env python3
"""Directed real Cache Linux acceptance, retaining version1 export oracles."""
import argparse,json,pathlib,subprocess
from export_results import parse,normalize
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',required=True,type=int);p.add_argument('--users',required=True,type=pathlib.Path);p.add_argument('--out-dir',required=True,type=pathlib.Path);a=p.parse_args();o=a.out_dir;o.mkdir(parents=True,exist_ok=True);src=pathlib.Path(__file__).parent
u=json.loads(a.users.read_text());u['events']=u['init'];roles=o/'event-user-roles.json';roles.write_text(json.dumps(u,indent=2)+'\n');cmds=[]
for script,extra,users,out in [('grade-events.py',['--profile','cache','--no-baseline'],roles,o/'event'),('grade-export.py',['--fixture-role','regress','--no-regression'],a.users,o/'export')]:
 cmd=['python3',str(src/script),str(a.log),'--exit-code',str(a.exit_code),'--users',str(users),'--out-dir',str(out),*extra];r=subprocess.run(cmd);cmds.append({'command':cmd,'exit_code':r.returncode})
q=parse(a.log.read_text());(o/'results.json').write_text(json.dumps(q,indent=2)+'\n');checks={'real_cache_event_and_lifecycle':cmds[0]['exit_code']==0,'complete_export_fixture':cmds[1]['exit_code']==0,'twelve_owned_sessions':q['valid'] and len(q['sessions'])==12 and all(s['released'] for s in q['sessions']),'configured_profile_identified':q['valid'] and all(s['header']['profile']==('dcache_a_transactions' if s['header']['abi']==2 else 'base') for s in q['sessions'])};
# Fresh Cache boot: audit ALL four counter identities, not only the new event.
import re
text=normalize(a.log.read_text())
def rows(tag):
 out=[]
 for l in text.splitlines():
  if not l.startswith(tag+' '):continue
  out.append({k:int(v,16) if k in {'S','R','delta','original','final','off','recorded','raw'} else int(v) if v.isdigit() else v for k,v in re.findall(r'(\w+)=(\S+)',l)})
 return out
exports=[x for x in rows('SSA_EXPORT') if x['test'] in (9,10)];sw=rows('SSA_SWITCH');samples=rows('SSA_SAMPLE');accounts=rows('SSA_ACCOUNT');by={x['header']['session']:x for x in q['sessions']}
checks['four_task_sampling_protocol']=len(exports)==4
for e in exports:
 sid=e['session'];active={x['event'] for x in sw if x['pid']==e['pid'] and x['depth']>=2 and x['rid']==2};rr=by[sid]['records'];record=next((x for x in rr if x['id']==2),{})
 for i,key in enumerate(['cycle','instret','time','cache']):
  mask=(1<<(40 if i==3 else 64))-1;ss=[x for x in samples if x['pid']==e['pid'] and x['event'] in active and x['counter']==i];ac=[x for x in accounts if x['pid']==e['pid'] and x['counter']==i]
  checks[f'session{sid}_counter{i}_samples']=bool(ss) and all((x['R']-x['S'])&mask==x['delta'] for x in ss)
  ok=False
  if len(ac)==1 and key in record:
   z=ac[0];d=(z['final']-z['original'])&mask;off=sum(x['delta'] for x in ss)&mask
   ok=z['valid']==1 and z['off']==off and d==(0 if e['legacy'] else off) and z['recorded']==record[key] and z['raw']==(record[key]+d)&mask
  checks[f'session{sid}_counter{i}_record_identity']=ok
r={'passed':all(checks.values()),'scope':'one actual singlehart Rocket Linux Cache boot; directed timer/exec/export, not another complete historical stage4 run','checks':checks,'dependencies':cmds,'sessions':len(q['sessions']),'records':sum(len(s['records']) for s in q['sessions'])};(o/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
