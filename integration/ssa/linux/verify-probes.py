#!/usr/bin/env python3
"""Architectural U/S-mode probes; these do not replace Linux acceptance."""
import argparse,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--simulator',default='sims/verilator/simulator-chipyard-RocketConfig');p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True);root=pathlib.Path(__file__).resolve().parents[2];rows=[]
for name in ['sv39','user-csr','user-write','user-pool','supervisor-policy','user-class-read','user-class-write']:
 cmd=[a.simulator,'+permissive',f'+loadmem=ssa/linux/{name}.hex','+max-cycles=2000000','+permissive-off',f'ssa/linux/{name}.riscv'];begin=time.monotonic()
 with (a.out_dir/(name+'.txt')).open('w') as f:
  try:code=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=600).returncode
  except subprocess.TimeoutExpired:code=124
 rows.append(dict(name=name,command=cmd,exit_code=code,passed=code==0,seconds=time.monotonic()-begin));(a.out_dir/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,flush=True)
 if code:raise SystemExit(1)
