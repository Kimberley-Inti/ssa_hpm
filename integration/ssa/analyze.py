#!/usr/bin/env python3
"""Persist a context dump as JSON and reconstruct its inclusive call tree."""
import argparse,json,pathlib,re,subprocess
p=argparse.ArgumentParser()
p.add_argument('log',type=pathlib.Path)
p.add_argument('--elf',type=pathlib.Path)
p.add_argument('--json',type=pathlib.Path)
a=p.parse_args();symbols={}
if a.elf:
    for line in subprocess.check_output(['riscv64-unknown-elf-nm','-n',str(a.elf)],text=True).splitlines():
        m=re.fullmatch(r'([0-9a-fA-F]+) [tT] (\S+)',line)
        if m:symbols[int(m[1],16)]=m[2]
records={}
for line in a.log.read_text().splitlines():
    if not re.fullmatch(r'0x[0-9a-f]+(?: 0x[0-9a-f]+){6}',line):continue
    ident,callee,parent,cycles,instret,ticks,nxt=map(lambda x:int(x,16),line.split())
    if ident in records:raise ValueError('duplicate record id')
    records[ident]=dict(id=ident,callee=hex(callee),symbol=symbols.get(callee,hex(callee)),parent=parent,
                        cycle=cycles,instret=instret,time=ticks,next=nxt)
assert records,'no records in dump'
def path(ident,seen=None):
    if ident==0:return []
    seen=set() if seen is None else seen
    assert ident in records and ident not in seen,'invalid parent graph'
    seen.add(ident);r=records[ident]
    return path(r['parent'],seen)+[r['symbol']]
for ident,r in records.items():
    r['context']='/'.join(path(ident))
    print(f"{ident}: {r['context']}: cycle={r['cycle']} instret={r['instret']} time={r['time']}")
result=dict(format='ssa-hpm-v1',inclusive=True,includes_monitor_overhead=True,records=list(records.values()))
if a.json:a.json.write_text(json.dumps(result,indent=2)+'\n')
