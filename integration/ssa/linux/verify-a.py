#!/usr/bin/env python3
"""Grade Linux A only from an actual Rocket/Verilator execution and clean exit."""
import argparse,hashlib,json,pathlib,re,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--image',type=pathlib.Path,required=True);p.add_argument('--hex',type=pathlib.Path,required=True);p.add_argument('--simulator',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);p.add_argument('--timeout',type=int,default=7200);a=p.parse_args()
a.out_dir.mkdir(parents=True,exist_ok=True);cmd=[str(a.simulator.resolve()),'+permissive','+loadmem='+str(a.hex.resolve()),'+max-cycles=500000000','+permissive-off',str(a.image.resolve())]
log=a.out_dir/'rocket-linux-a.txt';begin=time.monotonic()
with log.open('w') as f:
 try:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
 except subprocess.TimeoutExpired:code=124
text=log.read_text();text=re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',text);(a.out_dir/'rocket-linux-a.console.txt').write_text(text);checks={'opensbi':'OpenSBI v0.8' in text,'linux':'Linux version 5.7.0-rc3' in text,'userspace_pid1':'SSA LINUX A PASS: real userspace PID 1 on Rocket' in text,'shutdown':'reboot: Power down' in text,'no_panic':'Kernel panic' not in text,'exit_zero':code==0}
report=dict(stage='A',engine='RocketConfig Verilator (not Spike)',passed=all(checks.values()),checks=checks,command=cmd,exit_code=code,seconds=round(time.monotonic()-begin,2),image_sha256=hashlib.sha256(a.image.read_bytes()).hexdigest(),simulator_sha256=hashlib.sha256(a.simulator.read_bytes()).hexdigest())
(a.out_dir/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
