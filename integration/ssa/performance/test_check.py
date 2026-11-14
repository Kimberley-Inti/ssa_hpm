#!/usr/bin/env python3
"""Synthetic fault checks for measurement integrity; no hardware coverage claim."""
import json,pathlib,subprocess,tempfile
src=pathlib.Path(__file__).with_name('check.py')
def row(tag,m,k,r,x=7):
 return tag+' '+' '.join(f'{v:016x}' for v in [m,k,r,100,150,50,70,10,11,x])+'\n'
text=''
for m in range(6):
 text+=row('SSA_PERF_INIT',m,0,0)+row('SSA_PERF_CAL',m,0,0)
 for k in range(5):text+=row('SSA_PERF',m,k,0,k+7)
text+='SSA_PERF_DONE\n'
first=row('SSA_PERF',0,0,0,7);cases={'valid':text,'missing':text.replace(first,''),'duplicate':text+first,'wrong_checksum':text.replace(first,row('SSA_PERF',0,0,0,8)),'no_end':text.replace('SSA_PERF_DONE',''),'no_calibration':text.replace(row('SSA_PERF_CAL',0,0,0),''),'no_init':text.replace(row('SSA_PERF_INIT',0,0,0),'')}
cases['progress_interleaving']=text.replace('SSA_PERF 0000000000000000 ', 'SSA_PERF 00000000SSA_HOST_PROGRESS cycles=100000 pc=1\nSSA_CSR scause=0\n00000000 ',1)
checks={}
with tempfile.TemporaryDirectory() as d:
 d=pathlib.Path(d)
 for name,raw in cases.items():
  (d/'raw.txt').write_text(raw);q=subprocess.run(['python3',str(src),str(d/'raw.txt'),'--repeats','1','--exit-code','0','--out',str(d/'out.json')],stdout=subprocess.PIPE,text=True);checks[name]=(q.returncode==0)==(name in ('valid','progress_interleaving'))
 report={'passed':all(checks.values()),'coverage':'host-only synthetic measurement protocol fault injection','checks':checks};print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
