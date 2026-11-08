#!/usr/bin/env python3
"""Execute actual software and RTL tests; fail on exit status or missing markers."""
import argparse, json, pathlib, subprocess, time
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--rtl-only',action='store_true')
p.add_argument('--spike-only',action='store_true')
a=p.parse_args()
assert not (a.rtl_only and a.spike_only)
out=root/'ssa/results';out.mkdir(exist_ok=True)
tests=[]
if not a.rtl_only:
    tests += [('spike-context',['spike','ssa/reference.riscv'],['nested, parents, reuse, restore, collision, counters']),
              ('spike-boundary',['spike','ssa/boundary-reference.riscv'],['258 calls','record exhaustion']),
              ('spike-abi',['spike','ssa/abi-reference.riscv'],['shadow registers'])]
if not a.spike_only:
    for name,binary,markers in [('context','test',['nested, parents, reuse, restore, collision, counters']),
                                ('boundary','boundary',['258 calls','record exhaustion']),
                                ('abi','abi',['shadow registers']),
                                ('late','late',['shadow registers']),
                                ('disabled-reference','reference',['nested, parents, reuse, restore, collision, counters'])]:
        tests.append(('rtl-'+name,['sims/verilator/simulator-chipyard-RocketConfig','+permissive',
                                 '+loadmem=ssa/'+binary+'.hex','+max-cycles=5000000',
                                 '+permissive-off','ssa/'+binary+'.riscv'],markers))
results=[]
for name,cmd,markers in tests:
    begin=time.monotonic()
    log=out/(name+'.txt')
    print('RUN',name,flush=True)
    with log.open('w') as f:
        try:
            r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=600)
            code=r.returncode
        except subprocess.TimeoutExpired:
            code=124
    text=log.read_text()
    passed=code==0 and all('SSA PASS: '+m in text or m in text for m in markers) and '*** FAILED ***' not in text
    results.append(dict(name=name,command=cmd,exit_code=code,passed=passed,seconds=round(time.monotonic()-begin,2)))
    (out/('rtl-summary.json' if a.rtl_only else 'spike-summary.json' if a.spike_only else 'summary.json')).write_text(json.dumps(results,indent=2)+'\n')
    print(('PASS' if passed else 'FAIL'),name,results[-1]['seconds'],'s',flush=True)
    if not passed:
        print(text[-4000:])
        raise SystemExit(1)
