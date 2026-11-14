#!/usr/bin/env python3
"""Record actual native execution and hashes before invoking the Linux oracle."""
import argparse,pathlib,subprocess,json,hashlib,time
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--timeout',type=int,default=86400);a=p.parse_args();w=a.work.resolve();out=a.out_dir.resolve();out.mkdir(parents=True,exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
report=json.loads((w/'build-report.json').read_text());assert report['passed']
for name,value in report['images'].items():assert sha(w/name)==value
cmd=[str(a.simulator.resolve()),'+permissive','+loadmem='+str(w/'boot-a.hex'),'+max-cycles=1500000000','+permissive-off',str(w/'boot-a.elf')]
log=out/'rocket-linux-classification.txt';begin=time.monotonic();hashes={str(f):sha(f) for f in [a.simulator.resolve(),w/'boot-a.elf',w/'boot-a.hex',w/'init',w/'classnext']}
with log.open('w') as f:
    proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
    (out/'running.json').write_text(json.dumps(dict(command=cmd,pid=proc.pid,sha256=hashes),indent=2)+'\n')
    try:code=proc.wait(timeout=a.timeout)
    except subprocess.TimeoutExpired:proc.terminate();proc.wait();code=124
q=dict(command=cmd,native_exit_code=code,seconds=time.monotonic()-begin,sha256=hashes,log_sha256=sha(log));(out/'execution.json').write_text(json.dumps(q,indent=2)+'\n')
r=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('grade-classification.py')),str(log),'--exit-code',str(code),'--out',str(out/'summary.json')]);(out/'runner-exit.json').write_text(json.dumps(dict(native_exit_code=code,checker_exit_code=r.returncode))+'\n');raise SystemExit(r.returncode)
