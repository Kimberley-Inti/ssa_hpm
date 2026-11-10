#!/usr/bin/env python3
"""Grade real Linux exports; userspace markers or Spike alone cannot pass B/C."""
import argparse,json,pathlib,re
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',type=int,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
s=re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',a.log.read_text())
def rows(tag):
 out=[]
 for line in s.splitlines():
  if tag+' ' not in line:continue
  d={}
  for k,v in re.findall(r'(\w+)=([0-9a-f]+)',line.split(tag+' ',1)[1]):
   d[k]=int(v,16 if k in {'callee','cause','csr_cause','S','R','delta','original','final','off','recorded','raw'} else 10)
  out.append(d)
 return out
exports=rows('SSA_EXPORT');records=rows('SSA_RECORD');switches=rows('SSA_SWITCH');samples=rows('SSA_SAMPLE');accounts=rows('SSA_ACCOUNT');exits=rows('SSA_EXIT')
checks={}
def check(name,value):checks[name]=bool(value)
check('clean_linux_shutdown',a.exit_code==0 and 'reboot: Power down' in s and 'Kernel panic' not in s and 'SSA LINUX TEST FAIL' not in s)
check('driver_ready','SSA_LINUX_READY user_triggers=1 harts=1' in s)
check('user_fixture','SSA LINUX PROCESS FIXTURE PASS' in s and s.count('SSA LINUX DUAL USER PASS')==4)
check('security','SSA LINUX SECURITY USER PASS' in s)
check('nine_exports',len(exports)==9)
bytest={}
for e in exports:
 pid=e['pid'];key=f"test{e['test']}_role{e['role']}";bytest[e['test'],e['role']]=e
 rr=[r for r in records if r['pid']==pid];ee=[x for x in exits if x['pid']==pid]
 check(key+'_complete',e['complete']==1 and e['depth']==0 and e['spill']==0 and e['next']==3 and e['uid']==1000 and len(ee)==1 and ee[0]['selector']==0 and ee[0]['complete']==1)
 rr.sort(key=lambda x:x['id'])
 check(key+'_tree',len(rr)==2 and [x['id'] for x in rr]==[1,2] and [x['parent'] for x in rr]==[0,1] and all(rr[0][c]>=rr[1][c]>0 for c in ['cycle','instret','time']))
 for x in [x for x in samples if x['pid']==pid]:check(key+f"_sample{x['event']}_{x['counter']}",x['R']>=x['S'] and x['delta']==x['R']-x['S'])
for test in range(1,5):
 A=bytest.get((test,1));B=bytest.get((test,2))
 check(f'test{test}_pair',A and B and A['pool']!=B['pool'] and A['legacy']==B['legacy']==int(test>=3))
 if not A or not B:continue
 ar=[r for r in records if r['pid']==A['pid']];br=[r for r in records if r['pid']==B['pid']]
 check(f'test{test}_same_code',len(ar)==len(br)==2 and [x['callee'] for x in ar]==[x['callee'] for x in br])
 ev=[x for x in switches if x['pid']==A['pid'] and x['to']==B['pid'] and x['depth']==2 and x['rid']==2 and x['state']==0 and x['ivcsw']>0 and x['resumed']==1 and ((x['cause']&((1<<63)|255))==((1<<63)|5) or (x['csr_cause']&((1<<63)|255))==((1<<63)|5))]
 check(f'test{test}_timer_A_B_A',len(ev)>0)
 ac=[x for x in accounts if x['pid']==A['pid']]
 check(f'test{test}_accounting',len(ac)==3 and all(x['valid']==1 and x['off']>0 and (x['final']-x['original']==(0 if test>=3 else x['off'])) and x['raw']-x['recorded']==x['final']-x['original'] for x in ac))
 check(f'test{test}_unmonitored','SSA_UNMONITORED pid=1 selector=0' in s and any(x['from']==1 for x in ev))
 bev=[x for x in switches if x['pid']==B['pid'] and x['to']==A['pid'] and x['from']==A['pid'] and x['depth']==2 and x['rid']==2 and x['state']!=0 and x['resumed']==1]
 check(f'test{test}_B_sleep_resume',len(bev)>0)
 bc=[x for x in accounts if x['pid']==B['pid']]
 check(f'test{test}_B_accounting',len(bc)==3 and all(x['valid']==1 and x['off']>0 and x['final']-x['original']==(0 if test>=3 else x['off']) and x['raw']-x['recorded']==x['final']-x['original'] for x in bc))
comparison={}
for counter,name in enumerate(['cycle','instret','time']):
 vals={}
 for test in range(1,5):
  e=bytest.get((test,1));ar=[x for x in accounts if e and x['pid']==e['pid'] and x['counter']==counter]
  if len(ar)==1:vals[test]=ar[0]
 if len(vals)!=4:check(name+'_comparison_available',False);continue
 fixed=vals[2]['recorded']-vals[1]['recorded'];legacy=vals[4]['recorded']-vals[3]['recorded'];off=vals[2]['off']-vals[1]['off']
 comparison[name]={'fixed_long_minus_short':fixed,'legacy_long_minus_short':legacy,'excluded_long_minus_short':off}
 bvals={}
 for test in [1,2]:
  e=bytest.get((test,2));br=[x for x in records if e and x['pid']==e['pid'] and x['id']==2]
  if len(br)==1:bvals[test]=br[0][name]
 if len(bvals)==2:
  comparison[name]['B_fixed_long_minus_short']=bvals[2]-bvals[1]
  check(name+'_B_work_visible',bvals[2]>bvals[1])
 check(name+'_B_interval_grows',off>0 and legacy>0)
 # Cache/interrupt and boundary costs remain; demand a large, observable reduction.
 check(name+'_cross_talk_reduced',abs(fixed)*2<legacy)
report={'engine':'single-hart Rocket/Verilator real Linux processes','passed':all(checks.values()),'checks':checks,'comparison':comparison,'exports':exports,'switches':switches,'accounts':accounts}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'failed':[k for k,v in checks.items() if not v],'comparison':comparison},indent=2));raise SystemExit(0 if report['passed'] else 1)
