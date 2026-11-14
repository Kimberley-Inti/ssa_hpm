#!/usr/bin/env python3
"""Actual Linux auto-launch oracle: ownership, ELF identities, trees and counters."""
import pathlib,sys,re,json,argparse,importlib.util
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from export_results import normalize
from classification_results import parse

def fields(text,tag):
 rows=[]
 for l in text.splitlines():
  if not l.startswith(tag+' '):continue
  d={}
  for k,v in re.findall(r'(\w+)=(\S+)',l):
   d[k]=int(v,16) if k in ['entry','app','interp','cause','csr_cause','S','R','delta'] else int(v) if re.fullmatch('-?\\d+',v) else v
  rows.append(d)
 return rows

def grade(text,code,users):
 text=normalize(text);auto=text.split('AUTO_SUITE_START',1)[-1].split('AUTO_SUITE_END',1)[0];q=parse(auto);c={}
 def check(k,v):c[k]=bool(v)
 check('native_exit0',code==0);check('normal_powerdown','Power down' in text);check('auto_suite_complete','AUTO_SUITE_END' in text);check('no_guest_failure',not any(x in text for x in ['PLAIN_TEST_FAIL','LAUNCH_EXEC_FAIL','Kernel panic']))
 check('complete_exports',q['valid'])
 if not q['valid']:return {'passed':False,'checks':c,'exports':q,'auto_results':fields(auto,'SSA_AUTO_RESULT')}
 base={s['header']['session']:s for s in q['context_export']['sessions']};cls={s['header']['session']:s for s in q['classification_sessions']}
 starts=fields(auto,'SSA_AUTO_RESULT');arms=fields(auto,'SSA_AUTO_ARM');ends=fields(auto,'SSA_AUTO_END');reject=fields(auto,'SSA_AUTO_REJECT');forks=fields(auto,'SSA_AUTO_FORK');switches=fields(auto,'SSA_SWITCH');samples=fields(auto,'SSA_SAMPLE')
 pids=[];pending=False
 for line in auto.splitlines():
  if line=='LAUNCH_PID':pending=True
  elif pending and re.fullmatch(r'0x[0-9a-f]{16}',line):pids.append(int(line,16));pending=False
 check('twelve_controlled_launches',len(pids)==12)
 if len(pids)!=12:return {'passed':False,'checks':c,'exports':q,'auto_results':starts,'launch_pids':pids}
 stat,exe,fail,disabled,setid,h1,h2,exhaust,b,a,dyn,cap=pids
 def sessions(pid):return [s for s in base.values() if s['header']['pid']==pid]
 def result(pid):return [x for x in starts if x['pid']==pid]
 def counter(s,rid):return [cls[s['header']['session']]['records'][rid-1][k] for k in ['total','warmup','scalar','stream','irregular']]
 def tree(s,names,elf='plain'):
  sy=users['inputs'][elf]['symbols'];return [r['callee'] for r in s['records']]==[sy[n] for n in names]
 check('target_elf_no_ssa_calls',all(users['inputs'][n]['no_ssa_calls_checked'] for n in ['plain','plain-next','plain-capacity','plain-dynamic','libplain.so']))
 check('all_session_pools_released',bool(base) and all(s['released'] for s in base.values()))
 check('auto_enabled_links_to_owned_session',all(x['session'] in base and base[x['session']]['header']['pid']==x['pid'] and base[x['session']]['header']['image']==x['image'] for x in starts if x['enabled']))
 check('unprivileged_arm_denied','LAUNCH_UNPRIV_ARM_DENIED' in auto)
 check('ten_auto_sessions_exact',len(base)==10 and len(starts)==11 and len([x for x in starts if x['enabled']])==10 and {x['session'] for x in starts if x['enabled']}==set(base))
 exports=fields(auto,'SSA_EXPORT');check('ordinary_targets_uid1000',len(exports)==len(base) and all(x['uid']==1000 for x in exports))
 check('noncapacity_classification_complete',all(x['complete'] for sid,x in cls.items() if base[sid]['header']['pid']!=cap))
 check('profiles_and_sidecar_owned',len(cls)==9 and all(s['header']['legacy']==0 and s['header']['profile']==('dcache_a_transactions' if s['header']['pid'] not in [dyn,cap] else 'base') and ((s['header']['session'] in cls)==(s['header']['pid']!=dyn)) for s in base.values()))
 check('closed_records_inclusive_counters',all(all(r[k]>=sum(z[k] for z in s['records'] if z['parent']==r['id']) for k in ['cycle','instret','time']+(['cache'] if s['header']['abi']==2 else [])) for s in base.values() if s['complete'] for r in s['records']))
 ss=sessions(stat);check('static_one_session',len(ss)==1)
 if len(ss)==1:
  s=ss[0];check('static_exact_tree',s['header']['total']==6 and [r['parent'] for r in s['records']]==[0,1,0,3,0,5] and tree(s,['scalar_parent','class_common','stream_parent','class_common','irregular_parent','class_common']))
  check('static_leaf_classification',counter(s,2)==[32,4,14,12,2] and counter(s,4)==[16,4,0,12,0] and counter(s,6)==[16,4,0,6,6]);check('static_normal_exit',s['complete'] and s['header']['reason']=='exit')
 es=sorted(sessions(exe),key=lambda s:s['header']['session']);check('exec_two_distinct_sessions',len(es)==2)
 if len(es)==2:
  old,new=es;check('exec_image_replaced',new['header']['image']==old['header']['image']+1 and new['header']['session']!=old['header']['session'])
  check('exec_old_open_marked',old['header']['reason']=='exec' and old['header']['depth']==1 and old['header']['status']==1 and old['records'][2]['open']==1 and old['records'][2]['instret']==0)
  check('exec_old_closed_records',old['header']['total']==4 and counter(old,2)==[16,4,6,6,0] and counter(old,4)==[16,4,0,6,6])
  check('exec_new_clean',new['complete'] and new['header']['total']==2 and counter(new,2)==[16,4,0,12,0] and tree(new,['stream_parent','class_common'],'plain-next'))
 fs=sessions(fail);check('failed_exec_same_session',len(fs)==1)
 if len(fs)==1:
  s=fs[0];check('failed_exec_history_fork_preserved',s['header']['total']==4 and counter(s,2)==[48,4,0,18,26] and tree(s,['fail_fork','class_common','terminate','class_common']))
  check('signal_open_frame_explicit',s['header']['status']==1 and s['header']['depth']==1 and s['records'][2]['open']==1 and any(x['pid']==fail and x['signal']==15 and x['monitored']==1 for x in ends))
 children=[x['child'] for x in forks if x['parent']==fail];check('fork_policy_cleared',len(children)==1 and not sessions(children[0]) and not result(children[0]) and 'PLAIN_FORK_CHILD_UNSELECTED' in auto)
 check('thread_creation_rejected',any(x['pid']==fail and x['reason']=='threads' and x['errno']==95 for x in reject))
 check('disabled_identical_target_unmonitored',not sessions(disabled) and not result(disabled) and not any(x['pid']==disabled for x in arms) and 'AUTO_DISABLED_DONE' in auto)
 check('setid_precommit_rejected',not sessions(setid) and not result(setid) and any(x['pid']==setid and x['reason']=='setid' for x in reject) and 'LAUNCH_SETID_REJECT_OK' in auto)
 rr=result(exhaust);check('exhaustion_fail_open_explicit',len(rr)==1 and rr[0]['error']==-16 and rr[0]['enabled']==0 and rr[0]['reason']=='pool_exhausted' and not sessions(exhaust))
 hs=[sessions(h1),sessions(h2)];check('holders_two_pools',all(len(x)==1 for x in hs) and hs[0][0]['header']['pool']!=hs[1][0]['header']['pool'])
 if all(len(x)==1 for x in hs):check('holders_history_restored_after_unmonitored_work',all(counter(x[0],2)==[32,4,14,12,2] and x[0]['complete'] for x in hs))
 aa,bb=sessions(a),sessions(b);check('dual_two_sessions',len(aa)==len(bb)==1)
 if len(aa)==len(bb)==1:
  aa,bb=aa[0],bb[0];check('dual_owned_context_chains',all(s['header']['total']==3 and [r['parent'] for r in s['records']]==[0,1,2] and tree(s,['task_parent','task_common','class_common']) for s in [aa,bb]) and aa['header']['pool']!=bb['header']['pool'])
  check('dual_history_isolation',counter(aa,3)==[32,4,14,12,2] and counter(bb,3)==[32,4,0,24,4])
  mask=(1<<63)|255
  ae=[x for x in switches if x['pid']==a and x['to']==b and x['depth']==2 and x['rid']==2 and x['state']==0 and x['ivcsw']>0 and x['resumed'] and any((x[k]&mask)==((1<<63)|5) for k in ['cause','csr_cause'])]
  check('real_timer_preemption_open2',bool(ae));ordered=False
  for x in ae:
   for y in [z for z in switches if z['pid']==b and z['from']==a and z['depth']==2 and z['state'] and z['resumed']]:
    az=[z for z in samples if z['pid']==a and z['event']==x['event'] and z['counter']==0];bz=[z for z in samples if z['pid']==b and z['event']==y['event'] and z['counter']==0]
    if len(az)==len(bz)==1 and bz[0]['S']<az[0]['S']<bz[0]['R']<az[0]['R']:ordered=True
  check('dual_sample_chronology',ordered);check('dual_closed_after_resume',aa['complete'] and bb['complete'])
 check('all_pause_deltas_modulo_correct',bool(samples) and all(z['delta']==((z['R']-z['S'])&((1<<(40 if z['counter']==3 else 64))-1)) for z in samples))
 ds=sessions(dyn);dr=result(dyn);check('dynamic_actual_execution',len(ds)==len(dr)==1 and dr[0]['enabled'] and dr[0]['dynamic']==1 and 'PLAIN_DYNAMIC_OK' in auto)
 if len(ds)==len(dr)==1:
  s=ds[0];x=dr[0];check('dynamic_application_record',any(z['callee']==users['inputs']['plain-dynamic']['symbols']['dynamic_parent'] and z['instret']>0 for z in s['records']));check('dynamic_interpreter_records',x['entry']!=x['app'] and x['interp']>0 and any(x['interp']<=z['callee']<x['interp']+0x100000 for z in s['records']))
  check('dynamic_closed_subtrees_inclusive',all(all(z[k]>=sum(c[k] for c in s['records'] if c['parent']==z['id']) for k in ['cycle','instret','time']) for z in s['records'] if not z['open']))
  match=re.search(r'PLAIN_DYN_ANCHOR\s+(0x[0-9a-f]{16})',auto);check('dynamic_shared_function_record',bool(match) and any(z['callee']==int(match[1],16) and z['instret']>0 for z in s['records']))
  check('dynamic_no_silent_state_loss',s['end']['records_complete']==1 and not(s['header']['status']&~1))
 cs=sessions(cap);check('capacity_session',len(cs)==1)
 if len(cs)==1:
  s=cs[0];side=cls[s['header']['session']];h=side['header'];check('capacity_base64_full_export',s['complete'] and len(s['records'])==64 and s['chunks']==4)
  check('capacity_sidecar_explicit_incomplete',h['total']==64 and h['emitted']==63 and len(side['records'])==63 and h['dropped']==1 and h['inputs']==h['unframed']+65 and not side['complete'])
 return {'passed':all(c.values()),'checks':c,'exports':q,'auto_results':starts,'launch_pids':pids,'switches':switches,'samples':samples,'auto_end':ends}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',required=True,type=int);p.add_argument('--users',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);a=p.parse_args();q=grade(a.log.read_text(errors='replace'),a.exit_code,json.loads(a.users.read_text()));a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'passed':q['passed'],'checks':len(q['checks']),'failed':[k for k,v in q['checks'].items() if not v],'errors':q['exports']['errors'][:5]},indent=2));raise SystemExit(0 if q['passed'] else 1)
