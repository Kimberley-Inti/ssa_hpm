#!/usr/bin/env python3
"""Run an independently timed RTL benchmark, retain native status and hashes."""
import argparse,hashlib,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--elf',type=pathlib.Path,required=True);p.add_argument('--hex',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--repeats',type=int,default=5);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
if (a.out/'running.json').exists():raise SystemExit('Refuse overwriting an existing run')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
cmd=[str(a.simulator.resolve()),'+permissive','+loadmem='+str(a.hex.resolve()),'+max-cycles=100000000','+permissive-off',str(a.elf.resolve())]
meta={'command':cmd,'sha256':{str(f.resolve()):sha(f) for f in [a.simulator,a.elf,a.hex]}};start=time.monotonic()
with (a.out/'rtl-performance.txt').open('w') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);meta['pid']=proc.pid;(a.out/'running.json').write_text(json.dumps(meta,indent=2)+'\n');code=proc.wait()
meta.update(exit_code=code,seconds=time.monotonic()-start,log_sha256=sha(a.out/'rtl-performance.txt'));(a.out/'execution.json').write_text(json.dumps(meta,indent=2)+'\n')
check=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('check.py')),str(a.out/'rtl-performance.txt'),'--repeats',str(a.repeats),'--exit-code',str(code),'--out',str(a.out/'summary.json')]);raise SystemExit(check.returncode)
