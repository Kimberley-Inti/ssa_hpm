#!/usr/bin/env python3
"""Compare every hardware classified retired access against independent rule1.
No PASS marker substitutes for native exit, trace/row partitions and workload oracle.
"""
import argparse,collections,json,pathlib,re,subprocess
from reference import Classifier
NAMES=['warmup','scalar','stream','irregular']
def check(text,elf):
    fault='SSA_CLASS_FAULT_EXPECTED' in text
    capacity='SSA_CLASS_CAPACITY_EXPECTED' in text
    patterns='SSA_CLASS_PATTERNS_EXPECTED' in text
    models={};counts=collections.defaultdict(lambda:[0]*5);errors=[];rows={};events=[]
    for line in text.splitlines():
        if line.startswith('SSA_MEM_OBS '):
            d={k:int(v,16 if k in ('pc','va') else 10) for k,v in re.findall(r'(\w+)=\s*([0-9a-f]+)',line)}
            model=models.setdefault(d['session'],Classifier())
            want=model.observe(d['rid'],d['pc'],d['va'],d['store'],d['size'])
            if want not in NAMES or NAMES[d['category']]!=want: errors.append(['classification',d,want])
            row=counts[d['rid']];row[0]+=1;row[d['category']+1]+=1;events.append(d)
        elif line.startswith('SSA_CLASS_ROW '):
            words=[int(x,16) for x in line.split()[1:]];rows[words[0]]=words[1:]
    sy={}
    for line in subprocess.check_output(['readelf','-sW',str(elf)],text=True).splitlines():
        w=line.split()
        if len(w)==8 and w[0][:-1].isdigit():sy[w[-1]]=int(w[1],16)
    accesses=collections.defaultdict(list)
    for d in events:
        if d['pc']==sy['class_access']:accesses[d['rid']].append(NAMES[d['category']])
    expected={2:['warmup']*2+['scalar']*14,4:['warmup']*2+['stream']*6,6:['warmup']*2+['irregular']*6}
    if patterns:expected[8]='warmup warmup scalar irregular stream stream'.split()
    base=sy['data']
    want_va={2:[base]*16,4:[base+8*i for i in range(8)],6:[base+8*i for i in [0,32,8,80,0,9,71,4]]}
    if patterns:want_va[8]=[base+8*i for i in [0,0,0,1,2,3]]
    actual_va=collections.defaultdict(list)
    for d in events:
        if d['pc']==sy['class_access']:actual_va[d['rid']].append(d['va'])
    checks={'exact_virtual_sequences':dict(actual_va)==want_va,'observed':bool(events),'record_count':set(rows)==set(range(64 if capacity else 11 if patterns else 8 if fault else 7)),
      'trace_matches_rows':all(rows.get(i,[])[:5]==counts[i] for i in range(1,64 if capacity else 11 if patterns else 8 if fault else 7)),
      'drops_marked':(rows.get(0,[0]*8)[7]>0 if capacity else rows.get(0,[0]*8)[7]==0),'stack_restored':rows.get(0,[0]*8)[1:3]==[0,0],
      'input_partition':rows.get(0,[0]*8)[5]==len(events)+rows.get(0,[0]*8)[3]+rows.get(0,[0]*8)[7],
      'workload_contexts':dict(accesses)==expected,'reference_all_observations':not errors,
      'eviction_metadata_matches_reference':rows.get(0,[0]*8)[6]==sum(c.evictions for c in models.values()),
      'fault_excluded':not any(d['pc']==sy.get('class_fault_access') for d in events)}
    if capacity:checks['exact_capacity_accounting']=rows[0][5]==72+2+65 and rows[0][7]==72-63
    if patterns:
        for name,kind in [('class_interleave_scalar','scalar'),('class_interleave_stream','stream')]:
            checks[name]=[NAMES[d['category']] for d in events if d['pc']==sy[name]]==['warmup']*2+[kind]*6
        stores=[d for d in events if d['store']]
        checks['all_store_widths']=all(sum(d['size']==size and d['rid']==10 for d in stores)==8 for size in range(4))
        checks['store_streams']=all(NAMES[d['category']]=='stream' for d in stores if d['rid']==10 and d['category']!=0)
    return dict(passed=all(checks.values()),checks=checks,observations=len(events),errors=errors[:8],contexts=dict(accesses),rows=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=pathlib.Path);p.add_argument('--elf',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    result=check(a.log.read_text(),a.elf);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
