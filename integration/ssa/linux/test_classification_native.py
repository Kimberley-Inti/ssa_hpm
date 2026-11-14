#!/usr/bin/env python3
"""Semantic owner negative on a real completed Linux capture; no hardware rerun.
Swap A/B leaf category sums and repair sidecar checksums. Transport must remain
valid, while the workload/context oracle rejects the incorrect attribution.
"""
import argparse,pathlib,json,re,hashlib,importlib.util
from export_results import normalize,SEED,MASK
spec=importlib.util.spec_from_file_location('grade_classification',pathlib.Path(__file__).with_name('grade-classification.py'));oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
p=argparse.ArgumentParser();p.add_argument('--native-log',type=pathlib.Path,required=True);p.add_argument('--execution',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
raw=a.native_log.read_bytes();execution=json.loads(a.execution.read_text());code=execution['native_exit_code'];assert hashlib.sha256(raw).hexdigest()==execution['log_sha256']
s='\n'.join(normalize(raw.decode()).splitlines())+'\n';positive=oracle.grade(s,code);assert positive['passed'],positive['checks']
exports=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)} for l in s.splitlines() if l.startswith('SSA_EXPORT ')]
sids={x['role']:x['session'] for x in exports if x['role'] in (1,2)};sessions={x['header']['session']:x for x in positive['export']['classification_sessions']};cols=['total','warmup','scalar','stream','irregular'];original={role:{k:sessions[sid]['records'][2][k] for k in cols} for role,sid in sids.items()};changed=s
for role,sid in sids.items():
    swapped=original[3-role];row='SSA_MRECORD session='+str(sid)+' id=3 '+' '.join(k+'='+str(swapped[k]) for k in cols)
    changed,n=re.subn(r'^SSA_MRECORD session='+str(sid)+r' id=3 [^\n]*$',row,changed,flags=re.M);assert n==1
    h=SEED
    for record in sessions[sid]['records']:
        values=swapped if record['id']==3 else record
        for word in [record['id']]+[values[k] for k in cols]:h=((h^word)*1099511628211)&MASK
    changed,n=re.subn(r'^SSA_MEND session='+str(sid)+r' emitted=3 hash=[0-9a-f]+$',f'SSA_MEND session={sid} emitted=3 hash={h:016x}',changed,flags=re.M);assert n==1
negative=oracle.grade(changed,code);checks={'positive_actual_native_passed':positive['passed'],'wrong_owner_payload_still_valid_transport':negative['export']['valid'],'wrong_owner_rejected_by_semantic_oracle':not negative['passed'] and not negative['checks']['two_task_history_isolation']}
q={'passed':all(checks.values()),'coverage':'host-only semantic mutation of actual completed Linux capture; original log unchanged, no new faulty hardware run','source_log_sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'original_role_leaf_vectors':original,'negative_failed_gates':[k for k,v in negative['checks'].items() if not v]};a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2));raise SystemExit(0 if q['passed'] else 1)
