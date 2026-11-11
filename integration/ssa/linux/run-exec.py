#!/usr/bin/env python3
"""Run a pinned Linux exec fixture and the affected stage4 regression in one boot."""
import argparse,hashlib,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--export',dest='export_test',action='store_true');p.add_argument('--event',action='store_true');p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--timeout',type=int,default=21600);a=p.parse_args();a.event=a.event or a.export_test;w=a.work.resolve();out=a.out_dir.resolve();out.mkdir(parents=True,exist_ok=True)
log=out/('rocket-linux-events.txt' if a.event else 'rocket-linux-exec.txt')
if log.exists() or (out/'execution.json').exists():raise SystemExit('Refusing to overwrite an existing execution; use a new result directory')
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
users={}
for name in (['init','lifecycle','next','regress','events','eventexec','eventnext'] if a.export_test else ['init','next','regress','events','eventexec','eventnext'] if a.event else ['init','next','regress']):
 syms={}
 for line in subprocess.check_output(['readelf','-sW',str(w/name)],text=True).splitlines():
  v=line.split()
  if len(v)==8 and (v[-1].startswith(('leaf','export_')) or v[-1] in {'old_parent','old_leaf','parent','common','event_common','event_warm','event_cold'}):syms[v[-1]]=int(v[1],16)
 users[name]={'sha256':h(w/name),'symbols':syms}
(out/'user-elfs.json').write_text(json.dumps(users,indent=2)+'\n')
image=w/'boot-a.elf';hexfile=w/'boot-a.hex';sim=a.simulator.resolve();hashes={str(f):h(f) for f in [image,hexfile,sim]};cmd=[str(sim),'+permissive','+loadmem='+str(hexfile),'+max-cycles='+('1500000000' if a.event else '800000000'),'+permissive-off',str(image)];begin=time.monotonic()
with log.open('w') as f:
 try:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
 except subprocess.TimeoutExpired:code=124
(out/'execution.json').write_text(json.dumps({'command':cmd,'exit_code':code,'seconds':time.monotonic()-begin,'sha256':hashes,'log_sha256':h(log)},indent=2)+'\n')
raise SystemExit(subprocess.run(['python3',str(pathlib.Path(__file__).with_name('grade-export.py' if a.export_test else 'grade-events.py' if a.event else 'grade-exec.py')),str(log),'--exit-code',str(code),'--users',str(out/'user-elfs.json'),'--out-dir',str(out)]).returncode)
