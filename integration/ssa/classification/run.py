#!/usr/bin/env python3
"""Run real classification RTL fixtures, record native exits and negative oracles."""
import argparse,pathlib,subprocess,json,time,hashlib,copy,re
from check_trace import check
p=argparse.ArgumentParser();p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--only',choices=['classification','classification-fault','classification-capacity','classification-patterns']);a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[2];out=a.out_dir.resolve();out.mkdir(parents=True,exist_ok=True);results=[]
for name in ([a.only] if a.only else ['classification','classification-fault','classification-capacity','classification-patterns']):
    elf=root/'ssa'/(name+'.riscv');log=out/(name+'.txt');cmd=[str(a.simulator.resolve()),'+permissive','+verbose','+loadmem='+str(elf.with_suffix('.hex')),'+max-cycles=5000000','+permissive-off',str(elf)];start=time.monotonic()
    with log.open('w') as f:code=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=900).returncode
    text=log.read_text();q=check(text,elf);q.update(command=cmd,exit_code=code,seconds=time.monotonic()-start,sha256={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [elf,log,a.simulator.resolve()]});q['passed'] &= code==0
    # Preserve the trace but corrupt category / context assignment. Both must fail.
    changed=re.sub(r'(SSA_MEM_OBS[^\n]*category=)\s*\d+',r'\g<1>3',text,count=1)
    swapped=re.sub(r'(SSA_MEM_OBS[^\n]*rid=)\s*2\b',r'\g<1>4',text,count=1)
    q['negative_category_detected']=not check(changed,elf)['passed'];q['negative_context_detected']=not check(swapped,elf)['passed'];q['passed'] &= q['negative_category_detected'] and q['negative_context_detected']
    (out/(name+'.json')).write_text(json.dumps(q,indent=2)+'\n');results.append(q);(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print(name,q['passed'],q['checks'],flush=True)
    if not q['passed']:raise SystemExit(1)
