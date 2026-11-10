#!/usr/bin/env python3
"""Execute immutable Linux B/C image in Rocket, record real status, then grade."""
import argparse,hashlib,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--image',type=pathlib.Path,required=True);p.add_argument('--hex',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--timeout',type=int,default=14400);p.add_argument('--user-elf',type=pathlib.Path);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
user=a.user_elf or a.image.parent/'init'
syms={}
for line in subprocess.check_output(['readelf','-sW',str(user)],text=True).splitlines():
 parts=line.split()
 if len(parts)==8 and parts[-1] in {'parent','common'}:syms[parts[-1]]=int(parts[1],16)
assert len(syms)==2,'user ELF must contain the actual measured symbols'
(a.out_dir/'user-symbols.json').write_text(json.dumps({'elf_sha256':hashlib.sha256(user.read_bytes()).hexdigest(),'symbols':syms},indent=2)+'\n')
cmd=[str(a.simulator.resolve()),'+permissive','+loadmem='+str(a.hex.resolve()),'+max-cycles=500000000','+permissive-off',str(a.image.resolve())];log=a.out_dir/'rocket-linux-process.txt';begin=time.monotonic()
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.image,a.hex,a.simulator)}
with log.open('w') as f:
 try:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
 except subprocess.TimeoutExpired:code=124
(a.out_dir/'execution.json').write_text(json.dumps(dict(command=cmd,exit_code=code,seconds=time.monotonic()-begin,sha256=hashes),indent=2)+'\n')
r=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('grade-process.py')),str(log),'--exit-code',str(code),'--out',str(a.out_dir/'summary.json')]);raise SystemExit(r.returncode)
