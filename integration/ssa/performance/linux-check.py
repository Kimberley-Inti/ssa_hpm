#!/usr/bin/env python3
"""Recheck a completed native capture; this does not start a simulation."""
import argparse,hashlib,json,pathlib,subprocess,sys,re,statistics
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();log=a.out/'rocket-linux-performance.txt';execution=json.loads((a.out/'execution.json').read_text());assert hashlib.sha256(log.read_bytes()).hexdigest()==execution['log_sha256'];code=execution['native_exit_code']
r=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('check.py')),str(log),'--linux','--exit-code',str(code),'--out',str(a.out/'work-summary.json')])
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
checks={'native_exit0':code==0,'normal_powerdown':'Power down' in text,'work_measurements':r.returncode==0,'suite_complete':'SSA_PERF_LINUX_DONE' in text,'no_guest_failure':not any(x in text for x in ['PLAIN_TEST_FAIL','Kernel panic','LAUNCH_EXEC_FAIL']),'exports_valid':exports['valid'],'eight_sessions':len(exports['context_export']['sessions'])==8,'all_pools_released':all(x['released'] for x in exports['context_export']['sessions']),'kernel_cost_phases':all(k in phases for k in ['dictionary_init','freeze','record_copy','export','pause','resume','exec_ready','exec_failed']),'open_frame_switch_cost':any(d['phase']=='resume' and d['detail']>=2 for d in costs)}
report={'passed':all(checks.values()),'checks':checks};(a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
