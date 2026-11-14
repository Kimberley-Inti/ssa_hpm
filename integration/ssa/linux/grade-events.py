#!/usr/bin/env python3
"""Grade one real Linux boot: opt-in DTLB sessions plus the stage5/stage4 rerun."""
import argparse,json,pathlib,re,subprocess
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',type=int,required=True);p.add_argument('--users',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();o=a.out_dir;o.mkdir(parents=True,exist_ok=True)
s=re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',a.log.read_text());(o/'console.txt').write_text(s);u=json.loads(a.users.read_text());c={};mask=(1<<40)-1
check=lambda k,v:c.update({k:bool(v)})
check('clean_shutdown',a.exit_code==0 and 'reboot: Power down' in s and 'FAIL' not in s and 'Kernel panic' not in s)
start=s.find('SSA_HPM_EVENT_SUITE_START');end=s.find('SSA_HPM_EVENT_SUITE_END');check('event_suite_boundaries',start>=0 and end>start)
if start<0 or end<start:raise SystemExit('Missing event suite markers; execution incomplete')
t=s[start:end]
def rows(tag,text=t):
 rr=[]
 for line in text.splitlines():
  if not line.startswith(tag+' '):continue
  d={}
  for k,v in re.findall(r'(\w+)=(\S+)',line):
   d[k]=int(v,16) if k in {'callee','S','R','delta','cause','csr_cause','original','final','off','recorded','raw'} else int(v) if v.isdigit() else v
  rr.append(d)
 return rr
exports=rows('SSA_EXPORT');rec=rows('SSA_EVENT_RECORD');beg=rows('SSA_EVENT_BEGIN');sess=rows('SSA_SESSION');fin=rows('SSA_EVENT_SESSION');sw=rows('SSA_SWITCH');samples=rows('SSA_SAMPLE');acc=rows('SSA_ACCOUNT');beg0=rows('SSA_BEGIN');opens=rows('SSA_EVENT_OPEN')
profile=rows('SSA_HPM_PROFILE',s);check('actual_firmware_selector',len(profile)==1 and profile[0]['selector']==0x1002 and profile[0]['width']==40 and profile[0]['user']==0)
check('user_hpm_counter_denied',t.count('SSA HPM COUNTER PERMISSION PASS')==1)
check('eight_owned_abi2_sessions',len(exports)==len(beg)==8 and {e['session'] for e in exports}=={b['session'] for b in beg} and all(b['abi']==2 and b['selector']==4098 and b['width']==40 and b['depth']==0 and b['next']==1 for b in beg))
check('frozen_event_mode_cleared',len(fin)==8 and all(f['policy']==1 and 0<=f['cutoff']<=mask for f in fin))
for e in exports:
 sid=e['session'];r=sorted([x for x in rec if x['session']==sid],key=lambda x:x['id']);check(f'session{sid}_bounded_unique_records',len(r)==e['next']-1 and len({x['id'] for x in r})==len(r) and all(0<=x['dtlb']<=mask for x in r))
 check(f'session{sid}_single_export',sum(x['session']==sid for x in exports)==1)
ctx=[e for e in exports if e['test']==8];check('one_context_process',len(ctx)==1)
if len(ctx)==1:
 e=ctx[0];r=sorted([x for x in rec if x['session']==e['session']],key=lambda x:x['id']);sy=u['events']['symbols']
 check('context_closed_reused_records',e['complete']==1 and e['depth']==0 and e['next']==5 and len(r)==4 and [x['id'] for x in r]==[1,2,3,4] and [x['parent'] for x in r]==[0,1,0,3] and [x['callee'] for x in r]==[sy['event_warm'],sy['event_common'],sy['event_cold'],sy['event_common']])
 if len(r)==4:
  check('cold_walks_exceed_warm',r[1]['dtlb']<=10 and r[3]['dtlb']>=100 and r[3]['dtlb']>r[1]['dtlb']+80)
  check('event_inclusive_parents',r[0]['dtlb']>=r[1]['dtlb'] and r[2]['dtlb']>=r[3]['dtlb'])
by={}
for test in [9,10]:
 pair={e['role']:e for e in exports if e['test']==test};check(f'test{test}_pair',set(pair)=={1,2})
 if set(pair)!={1,2}:continue
 A,B=pair[1],pair[2];by[test]=A
 check(f'test{test}_isolated_pools',A['pool']!=B['pool'] and A['pid']!=B['pid'] and all(e['uid']==1000 and e['complete']==1 and e['depth']==0 and e['next']==3 and e['spill']==0 for e in pair.values()))
 aa=[x for x in sw if x['pid']==A['pid'] and x['depth']>=2 and x['rid']==2 and x['to']==B['pid'] and x['state']==0 and x['ivcsw']>0 and any((x[k]&((1<<63)|255))==((1<<63)|5) for k in ['cause','csr_cause']) and x['resumed']==1]
 check(f'test{test}_real_timer_A_B_A_open_frame',bool(aa))
 for role,e in pair.items():
  ac=[x for x in acc if x['pid']==e['pid'] and x['counter']==3];rr=next((x for x in rec if x['session']==e['session'] and x['id']==2),None)
  tree=sorted([x for x in rec if x['session']==e['session']],key=lambda z:z['id']);sy=u['events']['symbols']
  check(f'test{test}_role{role}_record_tree',len(tree)==2 and [x['parent'] for x in tree]==[0,1] and [x['callee'] for x in tree]==[sy['parent'],sy['common']] and tree[0]['dtlb']>=tree[1]['dtlb'])
  if role==2:check(f'test{test}_B_generated_walks',rr and rr['dtlb']>=512)
  active={x['event'] for x in sw if x['pid']==e['pid'] and x['depth']>=2 and x['rid']==2};ss=[x for x in samples if x['pid']==e['pid'] and x['event'] in active and x['counter']==3]
  check(f'test{test}_role{role}_accepted_samples',bool(ss) and all((x['R']-x['S'])&mask==x['delta'] for x in ss))
  if len(ac)==1 and rr:
   z=ac[0];diff=(z['final']-z['original'])&mask
   check(f'test{test}_role{role}_event_accounting',z['valid']==1 and z['recorded']==rr['dtlb'] and z['off']==sum(x['delta'] for x in ss)&mask and z['off']>0 and diff==(z['off'] if test==9 else 0) and z['raw']==(z['recorded']+diff)&mask)
   if test==9 and role==1:check('B_walks_excluded_from_A',z['off']>=100 and z['recorded']*2<z['raw'])
   if test==10 and role==1:check('legacy_fails_positive_rebase_identity',diff!=z['off'] and z['recorded']==z['raw'])
  else:check(f'test{test}_role{role}_event_accounting',False)
 # DTLB can stay constant between sample instants; chronology uses cycle instead.
 ordered=False
 for x in aa:
  az=[z for z in samples if z['pid']==A['pid'] and z['event']==x['event'] and z['counter']==0]
  for be in [z for z in sw if z['pid']==B['pid'] and z['from']==A['pid'] and z['state']!=0 and z['resumed']==1 and z['depth']>=2 and z['rid']==2]:
   bz=[z for z in samples if z['pid']==B['pid'] and z['event']==be['event'] and z['counter']==0]
   if len(az)==len(bz)==1 and bz[0]['S']<az[0]['S']<bz[0]['R']<az[0]['R']:ordered=True
 check(f'test{test}_sample_chronology',ordered)
 check(f'test{test}_unmonitored_handoff','SSA_UNMONITORED pid=1 selector=0' in t and any(x['from'] not in {A['pid'],B['pid']} for x in aa))
if set(by)=={9,10}:
 v={k:next(x['dtlb'] for x in rec if x['session']==e['session'] and x['id']==2) for k,e in by.items()};check('negative_control_visible',v[10]>v[9]+100)
# Extended-counter exec: old/new/failed are separate ABI2 sessions in this segment.
ex={k:[e for e in exports if e['test']==k] for k in [5,6,7]};check('extended_exec_three_sessions',all(len(v)==1 for v in ex.values()))
if all(len(v)==1 for v in ex.values()):
 old,new,failed=[ex[k][0] for k in [5,6,7]];bb={e['session']:next(x for x in beg0 if x['session']==e['session']) for e in [old,new,failed]}
 check('event_exec_new_image_session',old['pid']==new['pid'] and old['session']!=new['session'] and bb[new['session']]['image']==bb[old['session']]['image']+1)
 for e,name,lo,hi in [(old,'old',32,90),(new,'new',100,160),(failed,'failed',100,180)]:
  r=sorted([x for x in rec if x['session']==e['session']],key=lambda x:x['id']);check(name+'_event_leaf',len(r)==2 and lo<=r[1]['dtlb']<=hi and r[1]['open']==0)
  check(name+'_event_begin_clean',bb[e['session']]['depth']==0 and bb[e['session']]['next']==1)
  sy=u['eventnext' if name=='new' else 'eventexec']['symbols'];parent=sy.get('old_parent',sy.get('parent'));leaf=sy.get('old_leaf',sy.get('common'))
  check(name+'_event_exec_tree',len(r)==2 and [x['parent'] for x in r]==[0,1] and [x['callee'] for x in r]==[parent,leaf])
  if name=='old':check('event_old_abandoned',e['complete']==0 and e['depth']==1 and len(r)==2 and r[0]['dtlb']==0 and r[0]['open']==1 and len([x for x in opens if x['session']==e['session'] and x['rid']==1])==1)
  else:check(name+'_event_closed_exit',e['complete']==1 and e['depth']==0 and len(r)==2 and r[0]['dtlb']>=r[1]['dtlb'] and r[0]['open']==0)
 qs=[x for x in rows('SSA_CHECK') if x['session']==failed['session']];check('event_enoent_keeps_open_frame',len(qs)==2 and all(x['depth']==1 and x['next']==3 and x['selector']==failed['pool'] for x in qs) and qs[0]['image']==qs[1]['image'])
 check('event_exec_ends_once',len([x for x in rows('SSA_EXEC_END') if x['session']==old['session']])==1 and not any(x['session']==old['session'] for x in rows('SSA_EXIT')))
# Grade the original fixtures using only actual boot prefix and actual regression suffix.
base=o/'baseline';base.mkdir(exist_ok=True);(base/'console.txt').write_text(s[:start]+s[end+len('SSA_HPM_EVENT_SUITE_END'):]);(base/'user-elfs.json').write_text(json.dumps(u,indent=2)+'\n')
cmd=['python3',str(pathlib.Path(__file__).with_name('grade-exec.py')),str(base/'console.txt'),'--exit-code',str(a.exit_code),'--users',str(base/'user-elfs.json'),'--out-dir',str(base)]
code=subprocess.run(cmd).returncode;check('stage5_and_stage4_regression',code==0)
r={'passed':all(c.values()),'event':'DTLB accepted PTW requests','selector':4098,'width':40,'semantics':'occurrence interval inclusive, modulo40; every-open-frame pause R-S excluded','checks':c,'exports':exports,'records':rec,'samples':samples,'accounts':acc,'sessions':sess,'source_log':str(a.log),'baseline':'baseline/summary.json'};(o/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':len(c),'failed':[k for k,v in c.items() if not v]},indent=2));raise SystemExit(0 if r['passed'] else 1)
