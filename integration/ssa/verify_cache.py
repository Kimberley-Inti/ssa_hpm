#!/usr/bin/env python3
"""Actual Rocket D-cache A event source, HPM/CSR samples and context oracle."""
import argparse,pathlib,subprocess,json,re,time,hashlib
p=argparse.ArgumentParser();p.add_argument('--simulator',required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];o=a.out_dir;o.mkdir(parents=True,exist_ok=True);tests=[];mask=(1<<40)-1
for name,expected in [('cache',0),('cache-selector-negative',42),('cache-context-negative',42),('cache-wrap',0)]:
 cmd=[a.simulator,'+permissive','+verbose','+ssa_cache_trace=1','+loadmem=ssa/'+name+'.hex','+max-cycles=2000000','+permissive-off','ssa/'+name+'.riscv'];log=o/(name+'.raw.txt');start=time.monotonic()
 with log.open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 s=log.read_text();excerpt=o/(name+'.txt');excerpt.write_text('\n'.join(l for l in s.splitlines() if l.startswith(('SSA_CACHE_','SSA_EVENT_','SSA PASS:','SSA NEGATIVE:')))+'\n');edges=[];samples=[];resets=[];records=[];g={}
 for l in s.splitlines():
  if l.startswith(('SSA_CACHE_EDGE','SSA_CACHE_SAMPLE','SSA_CACHE_RESET')):
   d={k:int(v,16 if k in ['cyc','value','sel'] else 10) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',l)}
   (edges if l.startswith('SSA_CACHE_EDGE') else samples if l.startswith('SSA_CACHE_SAMPLE') else resets).append(d)
  elif l.startswith('SSA_EVENT_RECORD'):records.append({k:int(v,16) for k,v in re.findall(r'(\w+)=(0x[0-9a-f]+)',l)})
  elif l.startswith('SSA_EVENT_GLOBAL'):g={k:int(v,16) for k,v in re.findall(r'(\w+)=(0x[0-9a-f]+)',l)}
 enabled=name!='cache-selector-negative';bycycle={x['cyc']:x for x in edges};reset=resets[-1] if resets else None
 sy={}
 for l in subprocess.check_output(['readelf','-sW',str(root/'ssa'/(name+'.riscv'))],text=True).splitlines():
  v=l.split()
  if len(v)==8 and v[-1] in ['warm_parent','cold_parent','event_common']:sy[v[-1]]=int(v[1],16)
 checks={'native_exit':r.returncode==expected,'actual_cache_source':sum(x['src'] for x in edges)>128,'reset_observed':bool(reset),'global_four_samples':len(g)==4,'two_parent_contexts':len(records)==4 and [x['id'] for x in records]==[1,2,3,4] and [x['parent'] for x in records]==[0,1,0,3] and records[1]['callee']==records[3]['callee']}
 checks['exact_elf_context_keys']=len(records)==4 and [x['callee'] for x in records]==[sy['warm_parent'],sy['event_common'],sy['cold_parent'],sy['event_common']]
 active=[x for x in edges if reset and x['cyc']>reset['cyc']]
 checks['fixed_selector']=all(x['sel']==(0x202 if enabled else 0) for x in active)
 checks['registered_source_to_increment']=all(bycycle.get(x['cyc']+1,{}).get('inc',0)==(x['src'] if enabled else 0) for x in active if x['src'])
 if reset:
  checks['all_csr_samples_match_real_hpm_increments']=bool(samples) and all(x['value']==(reset['value']+sum(e['inc'] for e in edges if reset['cyc']<e['cyc']<x['cyc']))&mask for x in samples if x['cyc']>reset['cyc'])
  checks['reported_global_from_actual_csr_reads']=all(any(x['value']==v for x in samples) for v in g.values())
 if len(records)==4 and len(g)==4:
  lo,hi=records[1]['cache'],records[3]['cache'];checks['parent_includes_child']=records[0]['cache']>=lo and records[2]['cache']>=hi
  checks['interval_boundary']=0<=((g['warm']-g['before'])&mask)-lo<128 and 0<=((g['cold']-g['warm'])&mask)-hi<128
  if name=='cache-selector-negative':checks['missing_selector_detected']=lo==hi==0 and 'SSA NEGATIVE:' in s
  elif name=='cache-context-negative':checks['swapped_workload_detected']=lo>hi+64 and 'SSA NEGATIVE:' in s
  else:
   checks['context_contrast']=hi>=128 and hi>lo+64 and 'SSA PASS:' in s
   checks['repeated_context_accumulates']=hi>((g['cold']-g['mid'])&mask)>0
  if name=='cache-wrap':checks['forty_bit_wrap']=g['cold']<g['before'] and reset['value']==(1<<40)-128
 else:checks['all_records_present']=False
 q={'name':name,'passed':all(checks.values()),'checks':checks,'command':cmd,'exit_code':r.returncode,'expected_exit':expected,'seconds':time.monotonic()-start,'source_pulses':sum(x['src'] for x in edges),'increments':sum(x['inc'] for x in edges),'global':g,'records':records,'reset':reset,'csr_samples':samples,'original_log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'event_excerpt':excerpt.name,'excerpt_sha256':hashlib.sha256(excerpt.read_bytes()).hexdigest()};tests.append(q);(o/'summary.json').write_text(json.dumps({'passed':all(t['passed'] for t in tests),'event':'dcache_a_transactions','selector':514,'width':40,'tests':tests},indent=2)+'\n');print(name,q['passed'],[k for k,v in checks.items() if not v],flush=True)
 if not q['passed']:raise SystemExit(1)

name='cache-abi';cmd=[a.simulator,'+permissive','+loadmem=ssa/cache-abi.hex','+max-cycles=2000000','+permissive-off','ssa/cache-abi.riscv'];log=o/(name+'.txt');start=time.monotonic()
with log.open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=900)
checks={'native_exit':r.returncode==0,'all_register_canaries_and_x5_calls':'SSA PASS: shadow registers' in log.read_text()}
tests.append({'name':name,'passed':all(checks.values()),'checks':checks,'command':cmd,'exit_code':r.returncode,'seconds':time.monotonic()-start});(o/'summary.json').write_text(json.dumps({'passed':all(t['passed'] for t in tests),'event':'dcache_a_transactions','selector':514,'width':40,'tests':tests},indent=2)+'\n');print(name,all(checks.values()),flush=True);raise SystemExit(0 if all(checks.values()) else 1)
