#!/usr/bin/env python3
"""Recheck a completed native capture; this does not start a simulation."""
import argparse,hashlib,json,pathlib,subprocess,sys,re,statistics
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--switch-only',action='store_true');p.add_argument('--accounting-witness',type=pathlib.Path);a=p.parse_args();log=a.out/'rocket-linux-performance.txt';execution=json.loads((a.out/'execution.json').read_text());assert hashlib.sha256(log.read_bytes()).hexdigest()==execution['log_sha256'];code=execution['native_exit_code']
r=None if a.switch_only else subprocess.run(['python3',str(pathlib.Path(__file__).with_name('check.py')),str(log),'--linux','--exit-code',str(code),'--out',str(a.out/'work-summary.json')])
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'linux'));from classification_results import parse;from export_results import normalize
text=normalize(log.read_text(errors='replace'));exports=parse(text)
(a.out/'exports.json').write_text(json.dumps(exports,indent=2)+'\n')
costs=[]
for line in text.splitlines():
 if not line.startswith('SSA_COST '):continue
 d=dict(re.findall(r'(\w+)=(\S+)',line));costs.append({k:int(v) if k!='phase' else v for k,v in d.items()})
phases={}
for kind in sorted({d['phase'] for d in costs}):
 group=[d for d in costs if d['phase']==kind];phases[kind]={'n':len(group),**{k:{'min':min(d[k] for d in group),'median':statistics.median(d[k] for d in group),'max':max(d[k] for d in group)} for k in ['cycle','instret','time']}}
(a.out/'phase-costs.json').write_text(json.dumps({'raw':costs,'statistics':phases},indent=2)+'\n')
def fields(tag):
 rows=[]
 for line in text.splitlines():
  if not line.startswith(tag+' '):continue
  hexkeys={'cause','csr_cause','S','R','delta','original','final','off','recorded','raw'}
  rows.append({k:int(v,16) if k in hexkeys else int(v) if v.isdigit() else v for k,v in re.findall(r'(\w+)=(\S+)',line)})
 return rows
owners={d['role']:d for d in fields('SSA_EXPORT') if d['role'] in (1,2)}
switches=fields('SSA_SWITCH');samples=fields('SSA_SAMPLE');accounts=fields('SSA_ACCOUNT');ordering=False;actual_irq=False
if set(owners)=={1,2}:
 ap,bp=owners[1]['pid'],owners[2]['pid'];mask=(1<<63)|255
 ae=[d for d in switches if d['pid']==ap and d['to']==bp and d['depth']==2 and d['rid']==2 and d['state']==0 and d['ivcsw']>0 and d['resumed'] and any((d[k]&mask)==((1<<63)|5) for k in ['cause','csr_cause'])]
 actual_irq=bool(ae)
 for x in ae:
  for y in [z for z in switches if z['pid']==bp and z['from']==ap and z['depth']==2 and z['state'] and z['resumed']]:
   aa=[z for z in samples if z['pid']==ap and z['event']==x['event'] and z['counter']==0];bb=[z for z in samples if z['pid']==bp and z['event']==y['event'] and z['counter']==0]
   if len(aa)==len(bb)==1 and bb[0]['S']<aa[0]['S']<bb[0]['R']<aa[0]['R']:ordering=True
owned_accounts=[d for d in accounts if d['pid'] in {v['pid'] for v in owners.values()}]
account_keys={(d['pid'],d['counter']) for d in owned_accounts}
required_keys={(v['pid'],j) for v in owners.values() for j in range(4)}
rebased=len(owned_accounts)==8 and account_keys==required_keys and len(required_keys)==8 and all(d['valid']==d['rebased']==1 and ((d['final']-d['original'])&((1<<(40 if d['counter']==3 else 64))-1))==d['off'] and ((d['raw']-d['recorded'])&((1<<(40 if d['counter']==3 else 64))-1))==d['off'] for d in owned_accounts)
expected_off={}
for d in owned_accounts:
 active_events={x['event'] for x in switches if x['pid']==d['pid'] and x['depth']>=2 and x['resumed']}
 mask=(1<<(40 if d['counter']==3 else 64))-1
 expected=sum(x['delta'] for x in samples if x['pid']==d['pid'] and x['counter']==d['counter'] and x['event'] in active_events)&mask
 expected_off[str(d['pid'])+':'+str(d['counter'])]=expected
 rebased &= d['off']==expected and expected>0
distinct_owners=set(owners)=={1,2} and all(len({v[k] for v in owners.values()})==2 for k in ['pid','pool','session'])
by_session={v['header']['session']:v for v in exports['context_export']['sessions']}
paths=[[(r['id'],r['parent'],r['callee']) for r in by_session[v['session']]['records']] for v in owners.values() if v['session'] in by_session]
same_paths=len(paths)==2 and paths[0]==paths[1] and len(paths[0])==(2 if a.switch_only else 3) and [x[:2] for x in paths[0]]==[(i,i-1) for i in range(1,len(paths[0])+1)]
cache_metadata=all(v['header']['abi']==1 or (v['counters'][3]['name']=='dcache_a_transactions' and v['counters'][3]['width']==40 and v['counters'][3]['selector']==514) for v in by_session.values())
(a.out/'switch-accounting.json').write_text(json.dumps({'owners':owners,'switches':switches,'samples':samples,'accounts':accounts,'two_distinct_task_pools':distinct_owners,'same_calls_in_separate_sessions':same_paths,'cache_profile_metadata':cache_metadata,'actual_timer_open2':actual_irq,'sample_chronology':ordering,'all_four_rebased':rebased,'independently_summed_pause_deltas':expected_off},indent=2)+'\n')
witnessed=False
if a.accounting_witness:
 assert not a.switch_only and a.accounting_witness.resolve()!=a.out.resolve()
 done=subprocess.run(['python3',__file__,'--out',str(a.accounting_witness),'--switch-only'])
 other=json.loads((a.accounting_witness/'execution.json').read_text())
 # Same exact progress executable / RTL archive; different test payload is explicit.
 model=execution['command'][0];other_model=other['command'][0]
 assert execution['sha256'][model]==other['sha256'][other_model]
 witnessed=done.returncode==0 and json.loads((a.accounting_witness/'summary.json').read_text())['passed']
coverage={'primary_accounting_rows':len(owned_accounts),'primary_direct_snapshot_proof':bool(rebased),'companion_used':witnessed,'companion':str(a.accounting_witness) if a.accounting_witness else None,'reason':'Legacy SSA_ACCOUNT output requires next==3; full benchmark creates three records. A separate two-record fixture supplies direct snapshot proof when needed.'}
checks={'native_exit0':code==0,'normal_powerdown':'Power down' in text,'work_measurements':(r.returncode==0 if r else 'SSA_PERF ' not in text and text.count('SSA_PERF_PHASE_ARM ')==2),'suite_complete':'SSA_PERF_LINUX_DONE' in text,'no_guest_failure':not any(x in text for x in ['PLAIN_TEST_FAIL','Kernel panic','LAUNCH_EXEC_FAIL']),'exports_valid':exports['valid'],'all_contexts_closed_complete':all(x['complete'] for x in exports['context_export']['sessions']),'all_classification_coverage_complete':all(x['complete'] for x in exports['classification_sessions']),'all_sidecar_contracts_declared':all(v=='declared' for v in exports['classification_contracts'].values()),'two_distinct_task_pools':distinct_owners,'same_calls_in_separate_sessions':same_paths,'cache_profile_metadata':cache_metadata,'actual_timer_open2':actual_irq,'A_B_A_sample_chronology':ordering,'pause_sample_arithmetic':bool(samples) and all(((x['R']-x['S'])&((1<<(40 if x['counter']==3 else 64))-1))==x['delta'] for x in samples),'all_four_pause_intervals_rebased':bool(rebased or witnessed),'expected_session_count':len(exports['context_export']['sessions'])==(2 if a.switch_only else 8),'all_pools_released':all(x['released'] for x in exports['context_export']['sessions']),'kernel_cost_phases':all(k in phases for k in (['dictionary_init','freeze','record_copy','export','pause','resume','exec_ready']+([] if a.switch_only else ['exec_failed']))),'open_frame_switch_cost':any(d['phase']=='resume' and d['detail']>=2 for d in costs)}
report={'passed':all(checks.values()),'checks':checks,'accounting_coverage':coverage,'fixture':'two-record-switch-only' if a.switch_only else 'full-performance'};(a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
