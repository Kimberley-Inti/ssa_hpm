#!/usr/bin/env python3
"""Validate exec sessions against real Linux records, then grade the stage4 rerun."""
import argparse,json,pathlib,re,subprocess
p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',type=int,required=True);p.add_argument('--users',type=pathlib.Path,required=True);p.add_argument('--out-dir',type=pathlib.Path,required=True);a=p.parse_args();out=a.out_dir;out.mkdir(parents=True,exist_ok=True)
s=re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',a.log.read_text());(out/'console.txt').write_text(s);users=json.loads(a.users.read_text());checks={}
def check(k,v):checks[k]=bool(v)
def rows(tag):
 result=[]
 for line in s.splitlines():
  if not line.startswith(tag+' '):continue
  d={}
  for k,v in re.findall(r'(\w+)=(\S+)',line[len(tag)+1:]):
   d[k]=int(v,16) if k in {'callee','S','R','delta','cause','csr_cause','original','final','off','recorded','raw'} else int(v) if v.isdigit() else v
  result.append(d)
 return result
exports=rows('SSA_EXPORT');begins=rows('SSA_BEGIN');ends=rows('SSA_EXIT');execends=rows('SSA_EXEC_END');sessions=rows('SSA_SESSION');records=rows('SSA_RECORD');opens=rows('SSA_OPEN');queries=rows('SSA_CHECK')
check('clean_shutdown',a.exit_code==0 and 'reboot: Power down' in s and 'Kernel panic' not in s and 'SSA EXEC FAIL' not in s and 'RETURNED SUCCESS PATH FAIL' not in s)
for marker in ['SSA EXEC IMAGE B ENTER','SSA EXEC IMAGE B PASS','SSA EXEC SUCCESS CHILD PASS','SSA EXEC ENOENT CHILD PASS','SSA EXEC FIXTURE PASS']:
 check(marker,s.count(marker)==1)
selected={test:[e for e in exports if e['test']==test] for test in [5,6,7]};check('three_exec_fixture_sessions',all(len(v)==1 for v in selected.values()))
if all(len(v)==1 for v in selected.values()):
 old,new,failed=[selected[x][0] for x in [5,6,7]]
 check('same_pid_new_session',old['pid']==new['pid'] and old['session']<new['session']<failed['session'] and len({old['session'],new['session'],failed['session']})==3)
 check('pool_reuse',old['pool']==new['pool'])
 check('old_open_export',old['uid']==1000 and old['complete']==0 and old['depth']==1 and old['next']==3 and old['spill']==0)
 for e,name,symbols,minleaf in [(old,'old',users['init']['symbols'],3300),(new,'new',users['next']['symbols'],6600),(failed,'failed',users['init']['symbols'],6600)]:
  sid=e['session'];rr=sorted([r for r in records if r['session']==sid],key=lambda x:x['id']);bb=[r for r in begins if r['session']==sid];meta=[r for r in sessions if r['session']==sid]
  check(name+'_one_begin_and_export',len(bb)==1 and sum(x['session']==sid for x in exports)==1 and len(meta)==1)
  check(name+'_clean_begin',len(bb)==1 and bb[0]['depth']==0 and bb[0]['next']==1 and bb[0]['selector']==e['pool'])
  parent=symbols.get('old_parent',symbols.get('parent'));leaf=symbols.get('old_leaf',symbols.get('common'))
  check(name+'_tree_and_symbols',len(rr)==2 and [r['callee'] for r in rr]==[parent,leaf] and [r['parent'] for r in rr]==[0,1] and [r['id'] for r in rr]==[1,2])
  check(name+'_closed_leaf',len(rr)==2 and rr[1]['open']==0 and rr[1]['instret']>=minleaf and rr[1]['cycle']>0 and rr[1]['time']>0)
  if name=='old':
   oo=[r for r in opens if r['session']==sid];ee=[r for r in execends if r['session']==sid]
   check('open_abandoned_not_returned',len(oo)==1 and oo[0]['frame']==1 and oo[0]['rid']==1 and oo[0]['status']=='abandoned' and len(rr)==2 and rr[0]['open']==1 and all(rr[0][k]==0 for k in ['cycle','instret','time']))
   check('exec_commit_end_once',len(ee)==1 and ee[0]['selector']==0 and not any(x['session']==sid for x in ends) and len(meta)==1 and meta[0]['reason']=='exec' and meta[0]['selector']==0)
  else:
   ee=[r for r in ends if r['session']==sid]
   check(name+'_closed_exit',e['complete']==1 and e['depth']==0 and e['next']==3 and e['spill']==0 and e['uid']==1000 and len(ee)==1 and ee[0]['selector']==0 and not any(x['session']==sid for x in execends) and len(meta)==1 and meta[0]['reason']=='exit')
   check(name+'_inclusive',len(rr)==2 and rr[0]['open']==0 and all(rr[0][k]>=rr[1][k]>0 for k in ['cycle','instret','time']))
 oldbegin=[x for x in begins if x['session']==old['session']];newbegin=[x for x in begins if x['session']==new['session']]
 check('actual_exec_epoch',len(oldbegin)==len(newbegin)==1 and newbegin[0]['image']==oldbegin[0]['image']+1)
 qs=[q for q in queries if q['session']==failed['session']]
 check('enoent_keeps_open_session',len(qs)==2 and all(q['pid']==failed['pid'] and q['depth']==1 and q['next']==3 and q['selector']==failed['pool'] for q in qs) and qs[0]['image']==qs[1]['image'])
 check('no_duplicate_exports_same_pid',sum(x['pid']==old['pid'] for x in exports)==2 and sum(x['pid']==failed['pid'] for x in exports)==1)
 check('freeze_release_then_new_enable',s.index(f"SSA_EXEC_END pid={old['pid']} session={old['session']}")<s.index('SSA EXEC IMAGE B ENTER')<s.index(f"SSA_BEGIN pid={new['pid']} session={new['session']}"))
 check('new_enters_unmonitored',f"SSA_UNMONITORED pid={new['pid']} selector=0" in s[s.index('SSA EXEC IMAGE B ENTER'):s.index(f"SSA_BEGIN pid={new['pid']} session={new['session']}")])
# Preserve the actual boot prefix and post-exec regression suffix. No invented lines.
regdir=out/'regression';regdir.mkdir(exist_ok=True);marker='SSA EXEC REGRESSION BEGIN\n';start=s.find('SSA EXEC FIXTURE START');split=s.find(marker)
check('regression_boundary',start>=0 and split>=0)
regcode=1
if start>=0 and split>=0:
 (regdir/'console.txt').write_text(s[:start]+s[split+len(marker):]);(regdir/'user-symbols.json').write_text(json.dumps(users['regress'],indent=2)+'\n')
 regcode=subprocess.run(['python3',str(pathlib.Path(__file__).with_name('grade-process.py')),str(regdir/'console.txt'),'--exit-code',str(a.exit_code),'--out',str(regdir/'summary.json'),'--symbols',str(regdir/'user-symbols.json')]).returncode
check('affected_stage4_regression',regcode==0)
r={'passed':all(checks.values()),'engine':'real single-hart Rocket/Verilator Linux','checks':checks,'sessions':[x for x in exports if x['test']>=5],'session_boundaries':sessions,'records':[x for x in records if x['session'] in {e['session'] for e in exports if e['test']>=5}],'open_frames':opens,'queries':queries,'regression':'regression/summary.json','errno_scope':'ENOENT before exec_mmap commit; validated by source assertion and successful child wait'}
(out/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'failed':[k for k,v in checks.items() if not v]},indent=2));raise SystemExit(0 if r['passed'] else 1)
