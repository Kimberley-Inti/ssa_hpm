#!/usr/bin/env python3
"""Execute native Linux performance image, validate measurements and frozen exports."""
import argparse,hashlib,json,pathlib,subprocess,time,sys,re,statistics
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();w=a.work.resolve();a.out.mkdir(parents=True,exist_ok=True)
if any(a.out.iterdir()):raise SystemExit('Refuse nonempty run directory')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
q=json.loads((w/'build-report.json').read_text());assert q['passed']
for n,h in q['images'].items():assert sha(w/n)==h,n
cmd=[str(a.simulator.resolve()),'+permissive','+loadmem='+str(w/'boot-a.hex'),'+max-cycles=2500000000','+permissive-off',str(w/'boot-a.elf')];log=a.out/'rocket-linux-performance.txt';execution={'command':cmd,'sha256':{str(f):sha(f) for f in [a.simulator,w/'boot-a.elf',w/'boot-a.hex']}};start=time.monotonic()
with log.open('w') as f:
 proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);execution['pid']=proc.pid;(a.out/'running.json').write_text(json.dumps(execution,indent=2)+'\n');code=proc.wait()
execution.update(native_exit_code=code,seconds=time.monotonic()-start,log_sha256=sha(log));(a.out/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
raise SystemExit(subprocess.run(['python3',str(pathlib.Path(__file__).with_name('linux-check.py')),'--out',str(a.out)]).returncode)
