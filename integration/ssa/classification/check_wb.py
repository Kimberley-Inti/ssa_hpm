#!/usr/bin/env python3
"""Independent pre-clock WB inputs -> reference categories -> exported HW sums.
The read-only host harness does not use hardware category labels as oracle input.
"""
import argparse,pathlib,re,json,collections
from reference import Classifier

def check(text):
    raw=[];rows={}
    for line in text.splitlines():
        if line.startswith('SSA_WB_MEM '):raw.append({k:int(v,16 if k in ('pc','va') else 10) for k,v in re.findall(r'(\w+)=(\w+)',line)})
        if line.startswith('SSA_CLASS_ROW '):
            w=[int(x,16) for x in line.split()[1:]];rows[w[0]]=w[1:]
    ref=Classifier();sums=collections.defaultdict(lambda:[0]*5);names=['warmup','scalar','stream','irregular']
    observed=[d for d in raw if d['observe']]
    for d in observed:
        kind=ref.observe(d['rid'],d['pc'],d['va'],d['store'],d['size']);row=sums[d['rid']];row[0]+=1;row[names.index(kind)+1]+=1
    checks={'actual_wb_observations':bool(observed),'actual_replay_seen':any(d['replay'] for d in raw),'actual_exception_seen':any(d['exception'] for d in raw),
        'replays_exceptions_never_observed':all(not d['observe'] for d in raw if d['replay'] or d['exception']),
        'observe_implies_retire':all(d['valid'] and not d['replay'] and not d['exception'] for d in observed),
        'unique_sampling_cycles':len({d['cycle'] for d in raw})==len(raw),
        'reference_matches_all_hardware_rows':all(rows[i][:5]==sums[i] for i in range(1,8)),
        'global_input_partition':rows[0][5]==len(observed)+rows[0][3]+rows[0][7],
        'history_evictions_match':rows[0][6]==ref.evictions}
    return {'passed':all(checks.values()),'checks':checks,'candidates':len(raw),'observations':len(observed),'replays':sum(d['replay'] for d in raw),'exceptions':sum(d['exception'] for d in raw),'reference_rows':dict(sums)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();q=check(a.log.read_text());a.out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2));raise SystemExit(0 if q['passed'] else 1)
