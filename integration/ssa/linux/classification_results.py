#!/usr/bin/env python3
"""Validate rule1 sidecars against complete version1 context/session export."""
import argparse,json,pathlib,re
from export_results import parse as parse_base,SEED,MASK,normalize
COLUMNS=['total','warmup','scalar','stream','irregular']
def parse(text):
    text=normalize(text)
    base=parse_base(text);errors=list(base['errors']);sessions={}
    windows={}
    for n,line in enumerate(text.splitlines(),1):
        tag=line.split(' ',1)[0]
        if tag in ['SSA_XBEGIN','SSA_XCHUNK_END','SSA_XEND','SSA_XRELEASE']:
            m=re.search(r'\bsession=(\d+)',line)
            if m:windows.setdefault(int(m[1]),{})[tag]=n
    def need(ok,msg):
        if not ok: raise ValueError(msg)
    for n,line in enumerate(text.splitlines(),1):
        tag=line.split(' ',1)[0]
        if tag not in ('SSA_MBEGIN','SSA_MRECORD','SSA_MEND'):continue
        d={k:(int(v,16) if k=='hash' else int(v) if v.isdigit() else v) for k,v in re.findall(r'(\w+)=(\S+)',line)}
        try:
            sid=d['session']
            w=windows.get(sid,{})
            need(w.get('SSA_XCHUNK_END',w.get('SSA_XBEGIN',10**18))<n<w.get('SSA_XEND',10**18),'sidecar outside frozen context export window')
            if tag=='SSA_MBEGIN':
                need(sid not in sessions,'duplicate sidecar')
                need(d['version']==d['rule']==1 and d['width']==64 and d['history']==16 and d['capacity']==63,'rule metadata')
                need(d['aggregation']=='exclusive' and d['scope']=='retired_integer_virtual','observation/aggregation')
                need(d['emitted']==min(d['total'],63),'capacity/emitted')
                need(0<=d['status']<64 and d['status']&1 and not d['status']&2,'missing epoch or reset busy')
                sessions[sid]={'header':d,'records':[],'hash':SEED};continue
            need(sid in sessions,'unknown sidecar session');s=sessions[sid];h=s['header']
            need('end' not in s,'payload after terminal')
            if tag=='SSA_MRECORD':
                need(d['id']==len(s['records'])+1 and d['id']<=h['emitted'],'record sequence/bounds')
                need(all(0<=d[k]<=MASK for k in COLUMNS),'counter width')
                need(d['total']==(sum(d[k] for k in COLUMNS[1:])&MASK),'classification partition')
                need(sum(d[k] for k in COLUMNS[1:])<=MASK or h['status']&16,'unmarked counter overflow')
                for x in [d['id']]+[d[k] for k in COLUMNS]:s['hash']=((s['hash']^x)*1099511628211)&MASK
                s['records'].append(d)
            else:
                need(d['emitted']==len(s['records'])==h['emitted'] and d['hash']==s['hash'],'terminal checksum/count')
                need(h['inputs']==((sum(r['total'] for r in s['records'])+h['unframed']+h['dropped'])&MASK),'input partition')
                need(bool(h['status']&8)==bool(h['evictions']),'eviction status')
                s['end']=d;s['complete']=not(h['status']&~9 or h['dropped'] or h['total']>63)
        except (KeyError,ValueError,TypeError) as e:errors.append({'line':n,'error':str(e)})
    contexts={s['header']['session']:s for s in base['sessions']}
    for sid,ctx in contexts.items():
        h=ctx['header']
        if 'classification' not in h:continue  # Legacy format cannot promise whole-sidecar detection.
        if bool(h['classification']) != (sid in sessions):
            errors.append({'session':sid,'error':'declared classification sidecar missing or unexpected'})
        elif sid in sessions and (sessions[sid]['header']['rule']!=h['class_rule'] or sessions[sid]['header']['emitted']!=h['class_rows']):
            errors.append({'session':sid,'error':'classification declaration/sidecar mismatch'})
    for sid,s in sessions.items():
        if 'end' not in s:errors.append({'session':sid,'error':'truncated classification export'})
        if sid not in contexts or s['header']['total']!=contexts[sid]['header']['total']:
            errors.append({'session':sid,'error':'classification/context ownership mismatch'})
        else:
            ctx=contexts[sid]
            if not s['header']['status']&4 and s['header']['depth']!=ctx['header']['depth']:
                errors.append({'session':sid,'error':'context mirror depth mismatch'})
            for r in s['records']:
                if r['id']>len(ctx['records']):errors.append({'session':sid,'error':'missing base context for classification row'});continue
                r.update({k:ctx['records'][r['id']-1][k] for k in ['parent','callee','open']})
    if not sessions:errors.append({'error':'no classification sessions'})
    return {'valid':not errors,'errors':errors,'classification_sessions':list(sessions.values()),'context_export':base,'classification_contracts':{str(sid):'declared' if 'classification' in x['header'] else 'legacy_undeclared' for sid,x in contexts.items()}}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();q=parse(a.log.read_text());a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'valid':q['valid'],'sessions':len(q['classification_sessions']),'errors':q['errors'][:8]},indent=2));raise SystemExit(0 if q['valid'] else 2)
