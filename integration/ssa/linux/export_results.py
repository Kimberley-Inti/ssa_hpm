#!/usr/bin/env python3
"""Validate v1 bounded SSA export streams and write explicit complete/partial JSON.

Old SSA_RECORD payloads are deliberately retained. Historical pre-v1 logs use
existing grade-process/grade-exec/grade-events tools, not fabricated checksums.
"""
import argparse,collections,json,pathlib,re
MASK=(1<<64)-1
SEED=14695981039346656037
CAPACITY=262143
CHUNK=16
NAMES=['cycle','instret','time','dtlb_accepted_ptw_requests']

def plan(total,chunk=CHUNK):
 if not 0<=total<=CAPACITY or not 1<=chunk<=CHUNK:raise ValueError('invalid capacity/chunk')
 for seq,first in enumerate(range(1,total+1,chunk)):yield seq,first,min(chunk,total-first+1)

def digest(records,h=SEED):
 for r in records:
  for x in [r['id'],r['parent'],r['callee'],r['cycle'],r['instret'],r['time'],r.get('dtlb',0),r['open']]:h=((h^x)*1099511628211)&MASK
 return h

def normalize(text):return re.sub(r'SSA_HOST_PROGRESS[^\n]*\n|SSA_CSR[^\n]*\n','',text)

def parse(text):
 sessions={};starts={};pools={};errors=[]
 def need(v,msg):
  if not v:raise ValueError(msg)
 def fields(line):
  return {k:(int(v,16) if k in {'callee','hash'} else int(v) if v.isdigit() else v) for k,v in re.findall(r'(\w+)=(\S+)',line)}
 for number,line in enumerate(normalize(text).splitlines(),1):
  tag=line.split(' ',1)[0]
  if tag not in {'SSA_BEGIN','SSA_XBEGIN','SSA_XCOUNTER','SSA_XCHUNK','SSA_RECORD','SSA_EVENT_RECORD','SSA_XCHUNK_END','SSA_XFRAME','SSA_XEND','SSA_XRELEASE'}:continue
  try:
   d=fields(line);sid=d['session']
   if tag=='SSA_BEGIN':
    need(sid not in starts,'duplicate START session');need(d['pool'] not in pools,'pool reused before release');starts[sid]=d;pools[d['pool']]=sid;continue
   if tag=='SSA_XBEGIN':
    need(sid in starts and sid not in sessions,'missing START or duplicate export');st=starts[sid]
    need(d['version']==1 and d['abi'] in (1,2),'unsupported format/ABI')
    need(d['pid']==st['pid'] and d['image']==st['image'] and d['pool']==st['pool'],'session/image/pool ownership mismatch')
    need(d['capacity']==CAPACITY and d['chunk']==CHUNK,'capacity/chunk mismatch')
    need(0<=d['total']<=CAPACITY and d['counters']==(4 if d['abi']==2 else 3),'total/counters out of bounds')
    need(d['legacy'] in (0,1) and d['policy']==('interval_inclusive_no_rebase' if d['legacy'] else 'interval_inclusive_pause_rebase'),'counter semantics mismatch')
    need(d['reason'] in {'stop','exit','exec'} and 0<=d['status']<=63,'bad lifecycle/status')
    if 1<=d['next']<=CAPACITY+1:need(d['total']==d['next']-1,'next/total mismatch')
    else:need(d['total']==0 and d['status']&16,'invalid metadata unmarked')
    need(bool(d['depth'])==bool(d['status']&1) and bool(d['spill'])==bool(d['status']&2) and bool(d['errors'])==bool(d['status']&4),'integrity status mismatch')
    sessions[sid]={'header':d,'counters':[],'records':[],'frames':[],'chunks':0,'hash':SEED,'released':False,'active':None};continue
   if sid not in sessions:raise ValueError('unknown session or payload before export header')
   s=sessions[sid];h=s['header']
   if tag=='SSA_XRELEASE':
    need('end' in s and not s['released'],'release before END or duplicate release');need(d['pid']==h['pid'] and d['pool']==h['pool'] and pools.get(d['pool'])==sid,'release ownership mismatch');need(d['reason'] in {'exit','exec'},'invalid release');del pools[d['pool']];s['released']=True;continue
   need('end' not in s,'payload after END')
   if tag=='SSA_XCOUNTER':
    i=len(s['counters']);need(i<h['counters'] and d['index']==i and d['name']==NAMES[i] and d['width']==(40 if i==3 else 64) and d['selector']==(4098 if i==3 else 0),'bad counter definition');need(not s['records'] and s['active'] is None,'late metadata');s['counters'].append(d)
   elif tag=='SSA_XCHUNK':
    need(len(s['counters'])==h['counters'] and s['active'] is None,'missing metadata or nested chunk');need(d['seq']==s['chunks'] and d['first']==len(s['records'])+1,'chunk sequence/gap/duplicate');need(1<=d['count']<=CHUNK and d['first']+d['count']-1<=h['total'],'chunk bounds');s['active']={'header':d,'records':[]}
   elif tag=='SSA_RECORD':
    a=s['active'];need(a is not None,'record outside chunk');rr=a['records'];need(len(rr)<a['header']['count'] and d['id']==len(s['records'])+len(rr)+1,'record duplicate/gap');need(d['pid']==h['pid'] and 0<=d['parent']<d['id'] and d['callee']>0 and d['callee']%2==0,'record ownership/tree/address');need(all(0<=d[k]<=MASK for k in ['cycle','instret','time']),'scalar overflow');need(0<=d['open']<=min(h['depth'],256),'bad open count');rr.append(d)
   elif tag=='SSA_EVENT_RECORD':
    a=s['active'];need(h['abi']==2 and a and a['records'],'unexpected event payload');r=a['records'][-1];need('dtlb' not in r and all(d[k]==r[k] for k in ['pid','id','parent','callee','open']),'duplicate/mismatched event record');need(0<=d['dtlb']<(1<<40),'event width');r['dtlb']=d['dtlb']
   elif tag=='SSA_XCHUNK_END':
    a=s['active'];need(a is not None,'orphan chunk end');rr=a['records'];need(d['seq']==s['chunks'] and d['count']==a['header']['count']==len(rr),'truncated chunk');need(all(('dtlb' in r)==(h['abi']==2) for r in rr),'missing event channel');need(d['hash']==digest(rr),'chunk checksum');s['hash']=digest(rr,s['hash']);s['records']+=rr;s['chunks']+=1;s['active']=None
   elif tag=='SSA_XFRAME':
    need(s['active'] is None and d['frame']==len(s['frames'])+1 and d['frame']<=256 and 1<=d['rid']<=h['total'] and d['status']=='abandoned','invalid open frame');s['frames'].append(d)
   elif tag=='SSA_XEND':
    need(s['active'] is None and len(s['counters'])==h['counters'],'incomplete chunk/metadata');need(d['chunks']==s['chunks'] and d['emitted']==len(s['records']) and d['total']==h['total'] and d['hash']==s['hash'],'terminal count/checksum');need(d['status'] in {h['status'],h['status']|32} and d['records_complete'] in (0,1),'terminal status');need(bool(d['records_complete'])==(d['emitted']==d['total'] and not d['status']&32),'records-complete mismatch');need(d['records_complete'] or d['status']&32,'unmarked interruption');need(len(s['frames'])==min(h['depth'],256),'missing frame status')
    need(len({(r['parent'],r['callee']) for r in s['records']})==len(s['records']),'duplicate context key')
    framecounts=collections.Counter(f['rid'] for f in s['frames']);need(all(r['open']==framecounts[r['id']] for r in s['records']),'open frame/record mismatch');s['end']=d;s['complete']=bool(d['records_complete'] and d['status']==0)
  except (ValueError,KeyError,TypeError,IndexError) as e:errors.append({'line':number,'tag':tag,'error':str(e)})
 for sid,s in sessions.items():
  if 'end' not in s:errors.append({'session':sid,'error':'truncated export: missing END'})
  s.pop('active',None)
 if not sessions:errors.append({'error':'no version1 exports; use historical graders for legacy logs'})
 # START with no export is an interrupted session too.
 for sid in starts.keys()-sessions.keys():errors.append({'session':sid,'error':'session started but export missing'})
 return {'format_version':1,'valid':not errors,'errors':errors,'sessions':list(sessions.values())}

def main():
 p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--tree-limit',type=int,default=0);a=p.parse_args();q=parse(a.log.read_text(errors='replace'));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'valid':q['valid'],'sessions':len(q['sessions']),'records':sum(len(s['records']) for s in q['sessions']),'errors':q['errors'][:8]},indent=2));
 if a.tree_limit>0 and q['valid']:
  for x in q['sessions']:
   print('session',x['header']['session'],'reason',x['header']['reason'],'complete',x.get('complete',False));depth={0:-1}
   for r in x['records'][:a.tree_limit]:
    depth[r['id']]=depth[r['parent']]+1;print('  '*depth[r['id']]+f"{r['id']} @{r['callee']:x} instret={r['instret']}"+(f" dtlb={r['dtlb']}" if 'dtlb' in r else '')+(f" open={r['open']}" if r['open'] else ''))
 return 0 if q['valid'] else 2
if __name__=='__main__':raise SystemExit(main())
