#!/usr/bin/env python3
"""Host-only mutations of a completed native auto-launch capture, never a new RTL run."""
import argparse,pathlib,json,hashlib,re
from grade import grade,fields
from export_results import normalize,SEED,MASK
p=argparse.ArgumentParser();p.add_argument('--native-log',type=pathlib.Path,required=True);p.add_argument('--execution',type=pathlib.Path,required=True);p.add_argument('--users',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
raw=a.native_log.read_bytes();execution=json.loads(a.execution.read_text());assert hashlib.sha256(raw).hexdigest()==execution['log_sha256'];code=execution['native_exit_code'];users=json.loads(a.users.read_text());text='\n'.join(normalize(raw.decode()).splitlines())+'\n';good=grade(text,code,users);assert good['passed'],good['checks']
checks={};results={};pids=good['launch_pids'];static,disabled=pids[0],pids[3]
def reject(name,changed,gate,transport=True):
 q=grade(changed,code,users);checks[name]=not q['passed'] and not q['checks'][gate] and (q['exports']['valid'] if transport else not q['exports']['valid']);results[name]={'valid_transport':q['exports']['valid'],'failed_gates':[k for k,v in q['checks'].items() if not v]}
changed,n=re.subn(r'^SSA_AUTO_RESULT pid='+str(static)+r' [^\n]*\n','',text,count=1,flags=re.M);assert n==1;reject('missing_auto_hook_detected',changed,'ten_auto_sessions_exact')
changed,n=re.subn(r'^SSA_AUTO_RESULT pid='+str(static)+r' ',f'SSA_AUTO_RESULT pid={disabled} ',text,count=1,flags=re.M);assert n==1;reject('wrong_target_identity_detected',changed,'auto_enabled_links_to_owned_session')
auto=text.split('AUTO_SUITE_START',1)[1].split('AUTO_SUITE_END',1)[0];rows=fields(auto,'SSA_EXPORT');sids={x['role']:x['session'] for x in rows if x['role'] in [1,2]};side={s['header']['session']:s for s in good['exports']['classification_sessions']};cols=['total','warmup','scalar','stream','irregular'];original={role:side[sid]['records'][2] for role,sid in sids.items()};changed=text
for role,sid in sids.items():
 swapped=original[3-role];row=f'SSA_MRECORD session={sid} id=3 '+' '.join(k+'='+str(swapped[k]) for k in cols);changed,n=re.subn(r'^SSA_MRECORD session='+str(sid)+r' id=3 [^\n]*$',row,changed,flags=re.M);assert n==1;h=SEED
 for record in side[sid]['records']:
  v=swapped if record['id']==3 else record
  for word in [record['id']]+[v[k] for k in cols]:h=((h^word)*1099511628211)&MASK
 changed,n=re.subn(r'^SSA_MEND session='+str(sid)+r' emitted=3 hash=[0-9a-f]+$',f'SSA_MEND session={sid} emitted=3 hash={h:016x}',changed,flags=re.M);assert n==1
reject('rechecksummed_wrong_classification_owner_detected',changed,'dual_history_isolation')
cap=next(x for x in fields(auto,'SSA_AUTO_RESULT') if x['pid']==pids[-1])['session'];changed,n=re.subn(r'^SSA_XEND session='+str(cap)+r' [^\n]*\n','',text,flags=re.M);assert n==1;reject('missing_terminal_detected',changed,'complete_exports',False)
result={'passed':all(checks.values()),'coverage':'host-only semantic mutations of the same actual native log; no faulty-kernel or second RTL execution','source_log_sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'details':results};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
