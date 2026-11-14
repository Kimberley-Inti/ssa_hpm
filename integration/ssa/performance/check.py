#!/usr/bin/env python3
import argparse,json,pathlib,statistics,re
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--repeats',type=int,default=5);p.add_argument('--linux',action='store_true');p.add_argument('--exit-code',type=int,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
phases=[];phase_records=[];rows=[];errors=[];seen=set();modes=[0,1,3,4,5,6] if a.linux else list(range(6));s=re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',a.log.read_text(errors='replace'))
for line in s.splitlines():
 if line.startswith(('SSA_PERF_CAL ','SSA_PERF_INIT ','SSA_PERF_PHASE_')):
  phases.append(line)
  try:
   mode,kind,rep,c0,c1,i0,i1,t0,t1,x=[int(v,16) for v in line.split()[1:]]
   if mode not in modes or c1<=c0 or i1<=i0 or t1<t0:errors.append('bad phase samples')
   phase_records.append(dict(phase=line.split()[0],mode=mode,workload=kind,repetition=rep,cycle=c1-c0,instret=i1-i0,time=t1-t0,value=x,start=[c0,i0,t0],end=[c1,i1,t1]))
  except ValueError:errors.append('malformed phase')
  continue
 if not line.startswith('SSA_PERF '):continue
 try:
  m,k,r,c0,c1,i0,i1,t0,t1,x=[int(v,16) for v in line.split()[1:]]
  key=(m,k,r)
  if key in seen:errors.append('duplicate '+str(key))
  seen.add(key)
  if not (m in modes and 0<=k<5 and 0<=r<a.repeats):errors.append('range '+str(key))
  if c1<=c0 or i1<=i0 or t1<t0:errors.append('counter order '+str(key))
  rows.append(dict(mode=m,workload=k,repetition=r,cycle=c1-c0,instret=i1-i0,time=t1-t0,checksum=x,start=[c0,i0,t0],end=[c1,i1,t1]))
 except ValueError:errors.append('malformed row')
if seen!={(m,k,r) for m in modes for k in range(5) for r in range(a.repeats)}:errors.append('missing rows')
for k in range(5):
 if len({r['checksum'] for r in rows if r['workload']==k})!=1:errors.append('checksum mismatch '+str(k))
if ('SSA_PERF_LINUX_DONE' if a.linux else 'SSA_PERF_DONE') not in s:errors.append('missing end')
cal=[r for r in phase_records if r['phase']=='SSA_PERF_CAL']
if len(cal)!=len(modes)*a.repeats or {(r['mode'],r['repetition']) for r in cal}!={(m,r) for m in modes for r in range(a.repeats)}:errors.append('missing or duplicate calibration')
for tag,expected in ([('SSA_PERF_PHASE_INIT',6),('SSA_PERF_PHASE_FAIL_EXEC',6),('SSA_PERF_PHASE_STOP',4),('SSA_PERF_PHASE_EXPORT',4),('SSA_PERF_PHASE_ARM',3)] if a.linux else [('SSA_PERF_INIT',6)]):
 if len([r for r in phase_records if r['phase']==tag])!=expected:errors.append('phase count '+tag)
if a.exit_code!=0:errors.append('native exit '+str(a.exit_code))
table=[]
for m in modes:
 for k in range(5):
  group=[r for r in rows if r['mode']==m and r['workload']==k]
  if not group:continue
  d={'mode':m,'workload':k,'n':len(group)}
  for metric in ['cycle','instret','time']:
   values=[r[metric] for r in group];baseline=[r[metric] for r in rows if r['mode']==0 and r['workload']==k];mid=statistics.median(values);base=statistics.median(baseline) if baseline else 0
   d[metric]={'min':min(values),'median':mid,'max':max(values),'relative_change':(mid/base-1) if base else None}
  table.append(d)
report={'passed':not errors,'errors':errors,'scope':'same extended single-hart model; independent target boundaries; no area or no-extension hardware comparison','modes':({0:'off',1:'basic',3:'cache',4:'classification',5:'automatic-cache-classification',6:'manual-cache-classification'} if a.linux else {0:'off',1:'basic',2:'dtlb',3:'cache',4:'classification',5:'cache-classification'}),'workloads':['compute','calls128','depth16','stream32KiB','irregular32KiB'],'repetitions':a.repeats,'rows':rows,'statistics':table,'setup_and_calibration_raw':phases,'phase_records':phase_records,'linux':a.linux}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'rows':len(rows),'errors':errors}));raise SystemExit(bool(errors))
