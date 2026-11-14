#!/usr/bin/env python3
"""Actual native auto-launch Linux run plus old manual lifecycle regression."""
import pathlib,argparse,json,subprocess,hashlib,time,sys
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--timeout',type=int,default=172800);a=p.parse_args();w=a.work.resolve();out=a.out_dir.resolve();out.mkdir(parents=True,exist_ok=True);src=pathlib.Path(__file__).resolve().parent
if any(out.iterdir()):raise SystemExit('Refusing nonempty result directory')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
report=json.loads((w/'build-report.json').read_text());assert report['passed']
for name,h in report['images'].items():assert sha(w/name)==h
users=json.loads((w/'transparent-users.json').read_text());assert users['passed']
for name,d in users['inputs'].items():assert sha(w/name)==d['sha256'],name
sim=a.simulator.resolve();cmd=[str(sim),'+permissive','+loadmem='+str(w/'boot-a.hex'),'+max-cycles=2500000000','+permissive-off',str(w/'boot-a.elf')];log=out/'rocket-linux-transparent.txt';hashes={str(f):sha(f) for f in [sim,w/'boot-a.elf',w/'boot-a.hex']};start=time.monotonic()
with log.open('w') as f:
 proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);(out/'running.json').write_text(json.dumps({'command':cmd,'pid':proc.pid,'sha256':hashes},indent=2)+'\n')
 try:code=proc.wait(timeout=a.timeout)
 except subprocess.TimeoutExpired:proc.terminate();proc.wait();code=124
execution={'command':cmd,'native_exit_code':code,'seconds':time.monotonic()-start,'sha256':hashes,'log_sha256':sha(log)};(out/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
r=subprocess.run(['python3',str(src/'grade.py'),str(log),'--exit-code',str(code),'--users',str(w/'transparent-users.json'),'--out',str(out/'summary.json')])
sys.path.insert(0,str(src.parent));from export_results import normalize
text=normalize(log.read_text(errors='replace'));reg=text[text.find('SSA_CLASSIFICATION_SUITE_START'):] if 'SSA_CLASSIFICATION_SUITE_START' in text else '';reglog=out/'manual-regression.txt';reglog.write_text(reg)
r2=subprocess.run(['python3',str(src.parent/'grade-classification.py'),str(reglog),'--exit-code',str(code),'--out',str(out/'manual-summary.json')])
(out/'runner-exit.json').write_text(json.dumps({'native_exit_code':code,'auto_checker_exit_code':r.returncode,'manual_checker_exit_code':r2.returncode})+'\n');raise SystemExit(0 if code==r.returncode==r2.returncode==0 else 1)
