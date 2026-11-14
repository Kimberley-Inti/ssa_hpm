#!/usr/bin/env python3
"""Host-only resealed semantic mutations of a completed two-record native capture."""
import argparse,hashlib,json,pathlib,re,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--log',type=pathlib.Path,required=True);p.add_argument('--execution',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'linux'))
from export_results import normalize
raw=normalize(a.log.read_text(errors='replace'));receipt=json.loads(a.execution.read_text());assert receipt['native_exit_code']==0 and hashlib.sha256(a.log.read_bytes()).hexdigest()==receipt['log_sha256']
def increment(text,tag,key):
 pattern=r'('+tag+r' [^\n]*?\b'+key+r'=)([0-9a-f]{16})'
 changed,n=re.subn(pattern,lambda m:m[1]+format((int(m[2],16)+1)%2**64,'016x'),text,count=1);assert n==1;return changed
account_lines=re.findall(r'^SSA_ACCOUNT [^\n]*',raw,flags=re.M);assert len(account_lines)==8
duplicate=raw.replace(account_lines[1],account_lines[0],1)
cases={'duplicate_counter_account':duplicate,'valid':raw,'wrong_pause_delta':increment(raw,'SSA_SAMPLE','delta'),'wrong_snapshot_offset':increment(raw,'SSA_ACCOUNT','off'),'missing_accounts':re.sub(r'^SSA_ACCOUNT [^\n]*\n','',raw,flags=re.M)}
checks={};details={}
with tempfile.TemporaryDirectory(prefix='ssa-accounting-mutations-') as d:
 for name,text in cases.items():
  w=pathlib.Path(d)/name;w.mkdir();(w/'rocket-linux-performance.txt').write_text(text);ex=dict(receipt,log_sha256=hashlib.sha256((w/'rocket-linux-performance.txt').read_bytes()).hexdigest(),coverage='host-only normalized/resealed semantic mutation; not a native execution');(w/'execution.json').write_text(json.dumps(ex))
  r=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('linux-check.py')),'--out',str(w),'--switch-only'],capture_output=True,text=True)
  summary=json.loads((w/'summary.json').read_text());want=name=='valid';checks[name]=(r.returncode==0)==want and summary['passed']==want;details[name]={'checker_exit_code':r.returncode,'failed_checks':[k for k,v in summary['checks'].items() if not v]}
report={'passed':all(checks.values()),'coverage':'host-only mutations of one completed native switch capture','checks':checks,'details':details};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(not report['passed'])
