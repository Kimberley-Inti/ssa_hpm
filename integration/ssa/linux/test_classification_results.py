#!/usr/bin/env python3
"""Host protocol mutations, explicitly separate from hardware validation."""
from classification_results import parse
from test_export_results import fixture
from export_results import SEED,MASK
import json

def sample(n):
    core=fixture(n);s="";h=SEED
    s+=f'SSA_MBEGIN version=1 rule=1 session=1 total={n} emitted={n} width=64 aggregation=exclusive scope=retired_integer_virtual history=16 capacity=63 status=1 depth=0 spill=0 unframed=2 inputs={n*3+2} evictions=0 dropped=0\n'
    for i in range(1,n+1):
        s+=f'SSA_MRECORD session=1 id={i} total=3 warmup=2 scalar=1 stream=0 irregular=0\n'
        for x in [i,3,2,1,0,0]:h=((h^x)*1099511628211)&MASK
    s+=f'SSA_MEND session=1 emitted={n} hash={h:016x}\n'
    cut=core.index('SSA_XEND');return core[:cut]+s+core[cut:]

def run():
    checks={f'valid_{n}':parse(sample(n))['valid'] for n in (0,1,2,41,63)}
    checks['progress_interleaving']=parse(sample(2).replace('scope=retired_integer_virtual','scope=retired_SSA_HOST_PROGRESS cycles=100000 pc=1\nSSA_CSR scause=0\ninteger_virtual'))['valid']
    overflow=""
    overflow+='SSA_MBEGIN version=1 rule=1 session=1 total=1 emitted=1 width=64 aggregation=exclusive scope=retired_integer_virtual history=16 capacity=63 status=17 depth=0 spill=0 unframed=0 inputs=0 evictions=0 dropped=0\n'
    overflow+=f'SSA_MRECORD session=1 id=1 total=0 warmup={MASK} scalar=1 stream=0 irregular=0\n'
    h=SEED
    for x in [1,0,MASK,1,0,0]:h=((h^x)*1099511628211)&MASK
    overflow+=f'SSA_MEND session=1 emitted=1 hash={h:016x}\n'
    core=fixture(1);cut=core.index('SSA_XEND');overflow=core[:cut]+overflow+core[cut:]
    q=parse(overflow);checks['overflow_parseable_incomplete']=q['valid'] and not q['classification_sessions'][0]['complete']
    checks['unmarked_overflow_detected']=not parse(overflow.replace('status=17 depth=0','status=1 depth=0'))['valid']
    s=sample(2);row=next(l for l in s.splitlines(True) if l.startswith('SSA_MRECORD'))
    cases={'missing_row':s.replace(row,''),'duplicate_row':s.replace(row,row+row),
           'truncation':s[:s.index('SSA_MEND')], 'checksum':s.replace('scalar=1','scalar=0',1),
           'wrong_rule':s.replace('rule=1','rule=2'), 'wrong_session':s.replace('SSA_MRECORD session=1','SSA_MRECORD session=2',1),
           'wrong_width':s.replace('width=64 aggregation','width=40 aggregation'),
           'wrong_scope':s.replace('retired_integer_virtual','bus_transactions'),
           'missing_epoch':s.replace('capacity=63 status=1','capacity=63 status=0'),
           'input_partition':s.replace('inputs=8','inputs=9'),
           'wrong_depth':s.replace('status=1 depth=0','status=1 depth=1')}
    lines=s.splitlines(True);side=[l for l in lines if l.startswith(('SSA_MBEGIN','SSA_MRECORD','SSA_MEND'))]
    cases['after_release']=''.join(l for l in lines if l not in side)+''.join(side)
    cases['missing_base_context']=''.join(l for l in lines if not l.startswith(('SSA_XCHUNK','SSA_RECORD','SSA_EVENT_RECORD')))
    checks.update({name:not parse(broken)['valid'] for name,broken in cases.items()})
    declared=sample(2).replace('SSA_XBEGIN ', 'SSA_XBEGIN classification=1 class_rule=1 class_rows=2 ',1)
    checks['declared_sidecar_valid']=parse(declared)['valid']
    checks['declared_zero_sidecar_valid']=parse(sample(0).replace('SSA_XBEGIN ', 'SSA_XBEGIN classification=1 class_rule=1 class_rows=0 ',1))['valid']
    removed='\n'.join(l for l in declared.splitlines() if not l.startswith(('SSA_MBEGIN','SSA_MRECORD','SSA_MEND')))+'\n'
    # Assert the specific declaration error, not merely the legacy global
    # "no classification sessions" rejection.
    checks['whole_declared_sidecar_missing']=any('declared classification sidecar missing' in e['error'] for e in parse(removed)['errors'])
    checks['declared_disabled_unexpected_sidecar']=not parse(declared.replace('classification=1 class_rule=1 class_rows=2','classification=0 class_rule=0 class_rows=0'))['valid']
    checks['declared_wrong_rows']=not parse(declared.replace('class_rows=2','class_rows=1'))['valid']
    checks['declared_wrong_rule']=not parse(declared.replace('class_rule=1','class_rule=2'))['valid']
    return {'passed':all(checks.values()),'coverage':'host-only synthetic protocol mutations','checks':checks}
if __name__=='__main__':
    q=run();print(json.dumps(q,indent=2));raise SystemExit(0 if q['passed'] else 1)
