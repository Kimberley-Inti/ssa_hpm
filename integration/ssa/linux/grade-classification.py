#!/usr/bin/env python3
"""Rule1 real Linux lifecycle and preemptive isolation oracle."""
import argparse,json,pathlib,re,subprocess
from classification_results import parse
from export_results import normalize
COLUMNS=['total','warmup','scalar','stream','irregular']
def grade(text,code):
    text=normalize(text)
    q=parse(text);checks={'native_exit0':code==0,'normal_shutdown':'Power down' in text or 'Power off' in text,'suite_complete':'SSA_CLASSIFICATION_SUITE_END' in text,'no_guest_failure':'SSA LINUX TEST FAIL' not in text,'complete_transport':q['valid'],'seven_sessions':len(q['classification_sessions'])==7}
    sessions=q['classification_sessions'];base={s['header']['session']:s for s in q['context_export']['sessions']}
    def vector(s,rid):return [s['records'][rid-1][k] for k in COLUMNS]
    first=next((s for s in sessions if s['header']['total']==6),None)
    checks['context_patterns']=bool(first) and vector(first,2)==[32,4,14,12,2] and vector(first,4)==[16,4,0,12,0] and vector(first,6)==[16,4,0,6,6]
    checks['same_callee_different_parents']=bool(first) and len({first['records'][i-1]['callee'] for i in [2,4,6]})==1 and [first['records'][i-1]['parent'] for i in [2,4,6]]==[1,3,5]
    checks['class_coverage_valid']=all(s['header']['status'] in [1,9] and not s['header']['dropped'] for s in sessions)
    checks['all_pools_released']=all(s['released'] for s in base.values())
    checks['explicit_stop']=bool(first) and base[first['header']['session']]['header']['reason']=='stop'
    checks['zero_session']=any(s['header']['total']==0 and s['header']['inputs']==s['header']['unframed'] and not s['records'] for s in sessions)
    old=next((s for s in sessions if base[s['header']['session']]['header']['reason']=='exec'),None)
    checks['exec_open_observed']=bool(old) and old['header']['depth']==1 and base[old['header']['session']]['header']['status']==1
    replacement=None
    if old:
        oldb=base[old['header']['session']]['header']
        replacement=next((s for s in sessions if (lambda b:b['pid']==oldb['pid'] and b['image']>oldb['image'])(base[s['header']['session']]['header'])),None)
    checks['exec_new_clean_epoch']=bool(replacement) and replacement['header']['session']!=old['header']['session'] and replacement['header']['total']==2 and vector(replacement,2)==[16,4,0,12,0]
    checks['failed_exec_history_preserved']=any(s['header']['total']==2 and vector(s,2)==[32,4,0,12,16] for s in sessions)
    rows=[]
    for l in text.splitlines():
        if l.startswith('SSA_EXPORT '):rows.append({k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)})
    role={d['role']:next((s for s in sessions if s['header']['session']==d['session']),None) for d in rows if d['role'] in (1,2)}
    a,b=role.get(1),role.get(2)
    checks['two_task_history_isolation']=bool(a and b) and vector(a,3)==[32,4,14,12,2] and vector(b,3)==[32,4,0,24,4]
    if a and b:
        ab,bb=base[a['header']['session']]['header'],base[b['header']['session']]['header']
        switches=[]
        for l in text.splitlines():
            if l.startswith('SSA_SWITCH '):switches.append({k:int(v,16) if k in ['cause','csr_cause'] else int(v) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',l)})
        checks['actual_A_B_A_open_preemption']=any(e['pid']==ab['pid'] and e['to']==bb['pid'] and e['depth']==2 and e['resumed']==1 and e['preempt']==1 for e in switches)
        samples=[]
        for l in text.splitlines():
            if l.startswith('SSA_SAMPLE '):samples.append({k:int(v,16) if k in ['S','R','delta'] else int(v) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',l)})
        ordered=False
        for ae in switches:
            if ae['pid']!=ab['pid'] or ae['to']!=bb['pid'] or ae['depth']!=2 or not ae['preempt'] or not ae['resumed']:continue
            for be in switches:
                if be['pid']!=bb['pid'] or be['from']!=ab['pid'] or be['depth']!=2 or not be['state'] or not be['resumed']:continue
                az=[z for z in samples if z['pid']==ab['pid'] and z['event']==ae['event'] and z['counter']==0]
                bz=[z for z in samples if z['pid']==bb['pid'] and z['event']==be['event'] and z['counter']==0]
                if len(az)==len(bz)==1 and bz[0]['S']<az[0]['S']<bz[0]['R']<az[0]['R']:ordered=True
        checks['timer_switch_sample_chronology']=ordered
        checks['unmonitored_handoff']=any(e['pid']==ab['pid'] and e['to']==bb['pid'] and e['depth']==2 and e['resumed'] and e['from'] not in [ab['pid'],bb['pid']] for e in switches)
        checks['all_pause_samples_modulo_correct']=all(z['delta']==(z['R']-z['S'])&((1<<(40 if z['counter']==3 else 64))-1) for z in samples)
        checks['both_stacks_restored']=a['header']['depth']==b['header']['depth']==0
        checks['same_virtual_callee_independent_epoch']=a['records'][2]['callee']==b['records'][2]['callee'] and ab['pool']!=bb['pool'] and ab['session']!=bb['session']
    else:checks['actual_A_B_A_open_preemption']=False
    closed=[s for s in base.values() if s.get('complete')]
    checks['existing_inclusive_counter_relationships']=bool(closed) and all(all(r[k]>=sum(c.get(k,0) for c in s['records'] if c['parent']==r['id']) for k in ['cycle','instret','time','cache']) for s in closed for r in s['records'])
    return dict(passed=all(checks.values()),checks=checks,export=q)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--exit-code',type=int,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();q=grade(a.log.read_text(errors='replace'),a.exit_code);a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'passed':q['passed'],'checks':q['checks'],'errors':q['export']['errors'][:8]},indent=2));raise SystemExit(0 if q['passed'] else 1)
