#!/usr/bin/env python3
"""Final-candidate reproduction or fast, explicitly host-only evidence replay."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,time,shlex,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
r=sub.add_parser('reproduce');r.add_argument('out',type=pathlib.Path);r.add_argument('--reuse-dependencies',type=pathlib.Path,required=True);r.add_argument('--musl-cache',type=pathlib.Path);r.add_argument('--jobs',type=int,default=4)
e=sub.add_parser('check-evidence');e.add_argument('--out',type=pathlib.Path,required=True)
a=p.parse_args();a.out=a.out.resolve()
if a.out.exists() and any(a.out.iterdir()):p.error('output directory must be new or empty; inspect prior run receipts instead of restarting')
a.out.mkdir(parents=True,exist_ok=True);rows=[]
def command(name,cmd,cwd=ROOT):
 start=time.monotonic()
 with (a.out/(name+'.log')).open('w') as log:code=subprocess.run(list(map(str,cmd)),cwd=cwd,stdout=log,stderr=subprocess.STDOUT).returncode
 d={'name':name,'command':list(map(str,cmd)),'cwd':str(cwd),'exit_code':code,'seconds':time.monotonic()-start};rows.append(d);(a.out/'steps.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,flush=True)
 if code:raise SystemExit(code)
 return d
if a.action=='reproduce':
 w=a.out/'workspace';sim=w/'sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig';j=str(a.jobs)
 command('public-apply',['python3',ROOT/'scripts/apply.py',w,'--report',a.out/'public-apply.json'])
 command('dependencies',['python3',ROOT/'scripts/link_existing_dependencies.py',w,a.reuse_dependencies,'--report',a.out/'dependencies.json'])
 command('model',['bash','-c','source ssa/env.sh\nexec make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j'+j+' OPT_FAST=-O3 OPT_SLOW=-O3 "LINK=/usr/bin/g++ -B/usr/bin/"'],w)
 command('fixtures',['bash','-c','source ssa/env.sh\nexec make -C ssa -j'+j+' all events cache-events classification linux-probes'],w)
 for name,script in [('base','ssa/verify.py'),('process','ssa/verify_process.py'),('dtlb','ssa/verify_events.py'),('cache','ssa/verify_cache.py'),('permissions','ssa/linux/verify-probes.py'),('classification','ssa/classification/run.py')]:command(name,['bash','-c','source ssa/env.sh\nexec '+shlex.join(['python3',script,'--simulator',str(sim),'--out-dir',str(a.out/name)])],w)
 command('wb-model',['python3',w/'ssa/classification/build-trace.py','--workspace',w,'--config','SSAHPMEventRocketConfig','--out',a.out/'wb-model'])
 command('wb-native',[a.out/'wb-model/simulator-progress','+permissive','+verbose','+loadmem='+str(w/'ssa/classification-fault.hex'),'+max-cycles=5000000','+permissive-off',w/'ssa/classification-fault.riscv'],w)
 command('wb-oracle',['python3',w/'ssa/classification/check_wb.py',a.out/'wb-native.log','--out',a.out/'wb-summary.json'])
 command('progress',['python3',w/'ssa/linux/build-progress.py','--workspace',w,'--config','SSAHPMEventRocketConfig','--out',a.out/'progress'])
 for name,flag in [('linux','--transparent'),('linux-cost','--performance'),('linux-switch','--performance-switch')]:
  cmd=['python3',w/'ssa/linux/build-a.py','--work',a.out/(name+'-build'),flag,'--jobs',j]
  if a.musl_cache:cmd+=['--musl-cache',a.musl_cache]
  command(name+'-build',cmd)
 command('benchmark-build',['bash',w/'ssa/performance/build.sh',a.out/'benchmark-build','5'])
 command('switch-proof-native',['python3',w/'ssa/performance/linux-run.py','--work',a.out/'linux-switch-build','--simulator',a.out/'progress/simulator-progress','--out',a.out/'linux-switch-results','--switch-only'])
 jobs=[('linux-native',['python3',w/'ssa/linux/transparent/run.py','--work',a.out/'linux-build','--simulator',a.out/'progress/simulator-progress','--out-dir',a.out/'linux-results']),('linux-cost-native',['python3',w/'ssa/performance/linux-run.py','--work',a.out/'linux-cost-build','--simulator',a.out/'progress/simulator-progress','--out',a.out/'linux-cost-results','--accounting-witness',a.out/'linux-switch-results']),('bare-cost-native',['python3',w/'ssa/performance/run.py','--simulator',sim,'--elf',a.out/'benchmark-build/benchmark.riscv','--hex',a.out/'benchmark-build/benchmark.hex','--out',a.out/'benchmark-results','--repeats','5'])]
 active=[]
 for name,cmd in jobs:
  log=(a.out/(name+'.log')).open('w');proc=subprocess.Popen(list(map(str,cmd)),stdout=log,stderr=subprocess.STDOUT);active.append((name,cmd,proc,log,time.monotonic()))
 (a.out/'running.json').write_text(json.dumps([{'name':n,'pid':proc.pid,'command':list(map(str,c))} for n,c,proc,_,_ in active],indent=2)+'\n')
 failed=False
 for name,cmd,proc,log,start in active:
  code=proc.wait();log.close();rows.append({'name':name,'command':list(map(str,cmd)),'exit_code':code,'seconds':time.monotonic()-start});(a.out/'steps.json').write_text(json.dumps(rows,indent=2)+'\n');failed|=code!=0
 if failed:raise SystemExit('Native/checker failure: inspect receipts and logs; successful other runs were preserved')
 command('linux-postcheck',['python3',w/'ssa/linux/transparent/check-results.py','--results',a.out/'linux-results','--work',a.out/'linux-build'])
else:
 evidence=ROOT/'evidence/stage11';gate=json.loads((evidence/'summary.json').read_text());assert gate['passed'],'candidate not accepted'
 manifest=json.loads((evidence/'artifact-manifest.json').read_text());verified=0
 for name,h in manifest['files'].items():
  file=ROOT/name;assert hashlib.sha256(file.read_bytes()).hexdigest()==h,name;verified+=1
 suite=ROOT/'integration/ssa';linux=evidence/'linux-unified-final';perf=evidence/'linux-performance-final';bare=evidence/'performance-final';users=evidence/'linux-users.json'
 for logdir,logname in [(linux,'rocket-linux-transparent.txt'),(perf,'rocket-linux-performance.txt')]:
  receipt=json.loads((logdir/'execution.json').read_text());raw=(logdir/logname).read_bytes();assert receipt['native_exit_code']==0 and hashlib.sha256(raw).hexdigest()==receipt['log_sha256'] and 'Power down' in raw.decode(errors='replace')
 receipt=json.loads((bare/'execution.json').read_text());assert receipt['exit_code']==0 and hashlib.sha256((bare/'rtl-performance.txt').read_bytes()).hexdigest()==receipt['log_sha256']
 status=json.loads((linux/'runner-exit.json').read_text());assert status==dict(native_exit_code=0,auto_checker_exit_code=0,manual_checker_exit_code=0)
 command('auto-replay',['python3',suite/'linux/transparent/grade.py',linux/'rocket-linux-transparent.txt','--exit-code','0','--users',users,'--out',a.out/'auto.json'])
 command('manual-replay',['python3',suite/'linux/grade-classification.py',linux/'manual-regression.txt','--exit-code','0','--out',a.out/'manual.json'])
 command('auto-negatives',['python3',suite/'linux/transparent/negative.py','--native-log',linux/'rocket-linux-transparent.txt','--execution',linux/'execution.json','--users',users,'--out',a.out/'auto-negatives.json'])
 for name,script in [('reference','classification/test_reference.py'),('sidecar','linux/test_classification_results.py'),('measurement-protocol','performance/test_check.py')]:command(name,['python3',suite/script])
 command('export-protocol',['python3',suite/'linux/test_export_results.py','--out',a.out/'export-protocol.json'])
 command('bare-cost-replay',['python3',suite/'performance/check.py',bare/'rtl-performance.txt','--exit-code','0','--repeats','5','--out',a.out/'bare-cost.json'])
 command('linux-cost-replay',['python3',suite/'performance/check.py',perf/'rocket-linux-performance.txt','--linux','--exit-code','0','--repeats','5','--out',a.out/'linux-cost.json'])
 # Independent arithmetic result oracle, beyond equality between modes.
 aa,cc=1664525,1013904223;mask=(1<<64)-1
 expected=[(aa**128+cc*(aa**128-1)//(aa-1))&mask,(3**128+(3**128-1)//2)&mask,34,1+17*4096*4095//2+3*4096,1+17*4096*4095//2+3*4096]
 checked=0
 for name in ['bare-cost.json','linux-cost.json']:
  data=json.loads((a.out/name).read_text())
  for row in data['rows']:assert row['checksum']==expected[row['workload']];checked+=1
 assert checked==300
 (a.out/'closedform-results.json').write_text(json.dumps({'passed':True,'work_rows':checked,'expected':expected},indent=2)+'\n')
 # Workload statistics and direct pause proof have separate actual native captures.
 for label,src in [('cost-integrity',perf),('switch-integrity',evidence/'linux-switch-proof')]:
  dest=a.out/label;dest.mkdir()
  for n in ['execution.json','rocket-linux-performance.txt']:shutil.copy2(src/n,dest/n)
 command('linux-cost-integrity',['python3',suite/'performance/linux-check.py','--out',a.out/'cost-integrity','--accounting-witness',a.out/'switch-integrity'])
 command('accounting-negatives',['python3',suite/'performance/test_linux_accounting.py','--log',evidence/'linux-switch-proof/rocket-linux-performance.txt','--execution',evidence/'linux-switch-proof/execution.json','--out',a.out/'accounting-negatives.json'])
 command('wb-replay',['python3',suite/'classification/check_wb.py',evidence/'wb-memory-excerpt.txt','--out',a.out/'wb.json'])
 (a.out/'coverage.json').write_text(json.dumps({'coverage':'host-only replay of committed evidence; no new hardware, ELF execution or build','hashed_committed_artifacts':verified,'recorded_elf_linked_oracles':'hash-verified receipts, original ELF binaries intentionally excluded'},indent=2)+'\n')
(a.out/'summary.json').write_text(json.dumps({'passed':True,'action':a.action,'steps':rows},indent=2)+'\n')
print('PASS',a.action,flush=True)
