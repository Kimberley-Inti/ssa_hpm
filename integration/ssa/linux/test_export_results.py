#!/usr/bin/env python3
"""Host-only protocol fault injection; not hardware-capacity execution."""
import json,pathlib,argparse,re,hashlib
from export_results import parse,plan,digest,SEED,CAPACITY,CHUNK,NAMES

def fixture(n=33,abi=2):
 rows=[dict(id=i,parent=0 if i==1 else 1,callee=0x1000+i*4,cycle=i*10,instret=i,time=i//2,open=0,**({'dtlb':i} if abi==2 else {})) for i in range(1,n+1)]
 s='SSA_BEGIN session=1 pid=10 image=1 pool=123\n'
 s+=f'SSA_XBEGIN version=1 session=1 pid=10 image=1 abi={abi} total={n} capacity={CAPACITY} chunk={CHUNK} counters={4 if abi==2 else 3} reason=exit pool=123 next={n+1} depth=0 spill=0 errors=0 status=0 legacy=0 policy=interval_inclusive_pause_rebase\n'
 for i in range(4 if abi==2 else 3):s+=f'SSA_XCOUNTER session=1 index={i} name={NAMES[i]} width={40 if i==3 else 64} selector={4098 if i==3 else 0}\n'
 for seq,first,count in plan(n):
  s+=f'SSA_XCHUNK session=1 seq={seq} first={first} count={count}\n';rr=rows[first-1:first-1+count]
  for r in rr:
   s+='SSA_RECORD pid=10 session=1 '+' '.join(f'{k}={v:016x}' if k=='callee' else f'{k}={v}' for k,v in r.items() if k!='dtlb')+'\n'
   if abi==2:s+=f"SSA_EVENT_RECORD pid=10 session=1 id={r['id']} parent={r['parent']} callee={r['callee']:016x} dtlb={r['dtlb']} open=0\n"
  s+=f'SSA_XCHUNK_END session=1 seq={seq} count={count} hash={digest(rr):016x}\n'
 s+=f'SSA_XEND session=1 chunks={len(list(plan(n)))} emitted={n} total={n} hash={digest(rows):016x} status=0 records_complete=1\nSSA_XRELEASE session=1 pid=10 pool=123 reason=exit\n';return s

def run():
 c={};check=lambda k,v:c.update({k:bool(v)})
 for n in [0,1,2,15,16,17,32,33,41]:
  for abi in [1,2]:check(f'valid_{n}_abi{abi}',parse(fixture(n,abi))['valid'])
 for n in [0,1,16,17,33,41]:
  cache=fixture(n).replace('policy=interval_inclusive_pause_rebase\n','policy=interval_inclusive_pause_rebase profile=dcache_a_transactions\n').replace('name=dtlb_accepted_ptw_requests','name=dcache_a_transactions').replace('selector=4098','selector=514').replace(' dtlb=',' cache=')
  q=parse(cache);check(f'valid_cache_{n}',q['valid'] and q['sessions'][0]['header']['profile']=='dcache_a_transactions')
  if n==41:
   for name,broken in [('cache_wrong_selector',cache.replace('selector=514','selector=4098')),('cache_wrong_payload',cache.replace(' cache=',' dtlb=')),('cache_missing_profile',cache.replace(' profile=dcache_a_transactions','')),('unknown_profile',cache.replace('profile=dcache_a_transactions','profile=unknown')),('cache_scalar_channel_injection',cache.replace('SSA_RECORD pid=10 session=1 id=1 ', 'SSA_RECORD pid=10 session=1 cache=1 id=1 ')),('cache_dual_payload',cache.replace(' cache=1 ', ' cache=1 dtlb=1 '))]:check(name+'_detected',not parse(broken)['valid'])
 p=list(plan(CAPACITY));check('maximum_capacity_bounded_plan',len(p)==16384 and p[0]==(0,1,16) and p[-1]==(16383,262129,15) and sum(x[2] for x in p)==CAPACITY and all(1<=x[2]<=16 for x in p))
 for n in [-1,CAPACITY+1]:
  try:list(plan(n));check(f'invalid_capacity_{n}',False)
  except ValueError:check(f'invalid_capacity_{n}',True)
 base=fixture();ls=base.splitlines(True);a=next(i for i,l in enumerate(ls) if 'SSA_XCHUNK ' in l and 'seq=1 ' in l);b=next(i for i,l in enumerate(ls) if 'SSA_XCHUNK_END ' in l and 'seq=1 ' in l)+1
 cases={'missing_chunk':''.join(ls[:a]+ls[b:]),'duplicate_chunk':''.join(ls[:b]+ls[a:b]+ls[b:]),'truncated_terminal':base[:base.index('SSA_XEND')],'truncated_record':base[:base.index('SSA_XCHUNK_END')],'bad_checksum':base.replace('cycle=10 ','cycle=11 ',1),'bad_parent':base.replace('parent=0 ','parent=9 ',1),'foreign_payload_injection':base.replace('SSA_XCHUNK_END session=1 seq=0', 'SSA_RECORD pid=11 session=99 id=1 parent=0 callee=0000000000001000 cycle=1 instret=1 time=0 open=0\nSSA_XCHUNK_END session=1 seq=0',1),'wrong_session':base.replace('SSA_RECORD pid=10 session=1','SSA_RECORD pid=10 session=2',1),'bad_width':base.replace('width=40','width=64'),'bad_total':base.replace('total=33','total=262144',1),'pool_reuse_before_release':base[:base.index('SSA_XRELEASE')]+'SSA_BEGIN session=2 pid=11 image=1 pool=123\n','bad_frame_status':base.replace('depth=0','depth=1',1),'missing_event':base.replace(next(l for l in ls if l.startswith('SSA_EVENT_RECORD')),'',1)}
 for name,s in cases.items():check(name+'_detected',not parse(s)['valid'])
 # Full transport can truthfully report an aborted prefix. Deliberate mapping
 # failure is represented by terminal IO bit; never silently accepted complete.
 short=fixture(0).replace('total=0','total=10').replace('next=1','next=11').replace('status=0 records_complete=1','status=32 records_complete=0')
 q=parse(short);check('explicit_io_abort_parseable',q['valid'] and not q['sessions'][0]['complete'])
 q=parse(base.replace('SSA_XRELEASE session=1 pid=10 pool=123 reason=exit\n',''));check('explicit_stop_pool_can_remain_held',q['valid'] and not q['sessions'][0]['released'])
 return {'passed':all(c.values()),'coverage':'host-only fault injection and capacity arithmetic; not full-capacity RTL execution','checks':c}
def native_tests(path):
 from export_results import normalize
 s=normalize(path.read_text(errors='replace'));end=re.search(r'^SSA_XRELEASE[^\n]*\n',s,re.M)
 if not end:raise ValueError('No completed/released native export yet')
 s=s[:end.end()];q=parse(s);checks={'native_first_export_valid':q['valid'] and len(q['sessions'])==1 and q['sessions'][0]['header']['total']==41 and q['sessions'][0]['chunks']==3 and q['sessions'][0]['released']}
 ls=s.splitlines(True);a=next(i for i,l in enumerate(ls) if l.startswith('SSA_XCHUNK ') and 'seq=1 ' in l);b=next(i for i,l in enumerate(ls) if l.startswith('SSA_XCHUNK_END ') and 'seq=1 ' in l)+1
 cases={'native_missing_chunk':''.join(ls[:a]+ls[b:]),'native_duplicate_chunk':''.join(ls[:b]+ls[a:b]+ls[b:]),'native_missing_END':s[:s.index('SSA_XEND ')]}
 for name,text in cases.items():checks[name+'_detected']=not parse(text)['valid']
 return {'passed':all(checks.values()),'coverage':'actual completed41-record native prefix regraded; negatives are host mutations, not new hardware faults','prefix_sha256':hashlib.sha256(s.encode()).hexdigest(),'checks':checks}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--native-log',type=pathlib.Path);a=p.parse_args();q=run()
 if a.native_log:
  q['native']=native_tests(a.native_log);q['passed']=q['passed'] and q['native']['passed']
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'passed':q['passed'],'checks':len(q['checks']),'failed':[k for k,v in q['checks'].items() if not v],'native':q.get('native')},indent=2));raise SystemExit(0 if q['passed'] else 1)
