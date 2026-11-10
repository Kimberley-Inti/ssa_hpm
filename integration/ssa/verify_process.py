#!/usr/bin/env python3
"""Real CPU context switches; legacy mode must expose off-CPU attribution bug."""
import argparse,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--simulator',default='sims/verilator/simulator-chipyard-RocketConfig');p.add_argument('--out-dir',type=pathlib.Path,required=True)
a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
root=pathlib.Path(__file__).resolve().parents[1];results=[]
for name,binary,expected,marker in [('spike-process','process-reference',0,'SSA PASS: two pools'),('rtl-process-legacy','process-legacy',42,'SSA FAIL process mask:'),('rtl-process','process',0,'SSA PASS: two pools')]:
 cmd=['spike',f'ssa/{binary}.riscv'] if name.startswith('spike') else [a.simulator,'+permissive',f'+loadmem=ssa/{binary}.hex','+max-cycles=50000000','+permissive-off',f'ssa/{binary}.riscv']
 print('RUN',name,flush=True);begin=time.monotonic();log=a.out_dir/(name+'.txt')
 with log.open('w') as f:
  try:code=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=900).returncode
  except subprocess.TimeoutExpired:code=124
 text=log.read_text();passed=code==expected and marker in text
 if name=='rtl-process-legacy':passed=passed and '0000000000001000' in text
 results.append(dict(name=name,command=cmd,exit_code=code,expected_exit_code=expected,passed=passed,seconds=round(time.monotonic()-begin,2)))
 (a.out_dir/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
 print('PASS' if passed else 'FAIL',name,code,flush=True)
 if not passed:print(text[-4000:]);raise SystemExit(1)
print('SSA PASS: process regression suite',flush=True)
