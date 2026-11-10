#!/usr/bin/env python3
"""Observe real PTW handshakes and the standard HPM increment in Rocket RTL."""
import argparse,pathlib,subprocess,time,json,re,hashlib
p=argparse.ArgumentParser();p.add_argument('--simulator',required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];a.out_dir.mkdir(parents=True,exist_ok=True);results=[];mask=(1<<40)-1
for name,expected in [('event',0),('event-selector-negative',42),('event-context-negative',42),('event-wrap',0)]:
 log=a.out_dir/(name+'.raw.txt');cmd=[a.simulator,'+permissive','+verbose','+ssa_event_trace=1','+loadmem=ssa/'+name+'.hex','+max-cycles=1000000','+permissive-off','ssa/'+name+'.riscv'];begin=time.monotonic()
 with log.open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 s=log.read_text();lines=[l for l in s.splitlines() if l.startswith(('SSA_DTLB_EDGE','SSA_EVENT_','SSA PASS:','SSA NEGATIVE:'))];excerpt=a.out_dir/(name+'.txt');excerpt.write_text('\n'.join(lines)+'\n');edges=[];records=[];g=None
 for line in lines:
  if line.startswith('SSA_DTLB_EDGE'):
   d=dict(re.findall(r'(\w+)=([0-9a-f]+)',line));edges.append({k:int(v,16 if k in ['cyc','sel'] else 10) for k,v in d.items()})
  elif line.startswith('SSA_EVENT_RECORD'):records.append({k:int(v,16) for k,v in re.findall(r'(\w+)=(0x[0-9a-f]+)',line)})
  elif line.startswith('SSA_EVENT_GLOBAL'):g={k:int(v,16) for k,v in re.findall(r'(\w+)=(0x[0-9a-f]+)',line)}
 raw=sum(x['src'] for x in edges);inc=sum(x['inc'] for x in edges);initial=(1<<40)-8 if name=='event-wrap' else 0;inc_cycles={x['cyc'] for x in edges if x['inc']};enabled=name!='event-selector-negative';checks={'actual_expected_exit':r.returncode==expected,'observed_real_requests':raw>=128,'selector':all(e['sel']==(0x1002 if enabled else 0) for e in edges),'source_to_registered_increment':inc==raw if enabled else inc==0,'one_cycle_latency':all(e['cyc']+1 in inc_cycles for e in edges if e['src']) if enabled else True,'records':len(records)==4 and [x['id'] for x in records]==[1,2,3,4] and [x['parent'] for x in records]==[0,1,0,3] and records[1]['callee']==records[3]['callee']}
 if g and len(records)==4:
  checks.update(global_counter_matches_source=g['cold']==(initial+inc)&mask,warm_interval=records[1]['dtlb']==(g['warm']-g['before'])&mask,cold_interval=records[3]['dtlb']==(g['cold']-g['warm'])&mask)
  if name=='event-selector-negative':checks['missed_event_negative_detected']=records[3]['dtlb']==0 and raw>=128 and 'SSA NEGATIVE:' in s
  elif name=='event-context-negative':checks['misattribution_negative_detected']=records[1]['dtlb']>=100 and records[3]['dtlb']<=6 and 'SSA NEGATIVE:' in s
  else:
   checks['nonzero_repeated_record_accumulation']=records[3]['dtlb']>((g['cold']-g['mid'])&mask)>0
   checks['expected_context_contrast']=records[1]['dtlb']<=6 and records[3]['dtlb']>=100 and 'SSA PASS:' in s
  if name=='event-wrap':checks['counter_wrapped']=g['cold']<g['before']
 else:checks['complete_global_output']=False
 q={'name':name,'command':cmd,'exit_code':r.returncode,'expected_exit':expected,'seconds':time.monotonic()-begin,'passed':all(checks.values()),'checks':checks,'requests':raw,'increments':inc,'private_request_pulses':sum(x['src'] for x in edges if x['private']),'global':g,'records':records,'original_log':str(log),'original_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'excerpt':excerpt.name,'model_sha256':hashlib.sha256(pathlib.Path(a.simulator).resolve().read_bytes()).hexdigest()};results.append(q);(a.out_dir/'summary.json').write_text(json.dumps({'passed':all(x['passed'] for x in results),'tests':results},indent=2)+'\n');print(name,'PASS' if q['passed'] else 'FAIL',q['seconds'],[k for k,v in checks.items() if not v],flush=True)
 if not q['passed']:raise SystemExit(1)

name='event-abi';cmd=[a.simulator,'+permissive','+loadmem=ssa/event-abi.hex','+max-cycles=1000000','+permissive-off','ssa/event-abi.riscv'];log=a.out_dir/(name+'.txt');begin=time.monotonic()
with log.open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=600)
q={'name':name,'command':cmd,'exit_code':r.returncode,'expected_exit':0,'seconds':time.monotonic()-begin,'passed':r.returncode==0 and 'SSA PASS: shadow registers' in log.read_text(),'meaning':'actual ABI2 ROM executes against every-register canaries, x5 calls/returns and ordinary jumps'};results.append(q);(a.out_dir/'summary.json').write_text(json.dumps({'passed':all(x['passed'] for x in results),'tests':results},indent=2)+'\n');print(name,'PASS' if q['passed'] else 'FAIL',flush=True);raise SystemExit(0 if q['passed'] else 1)
