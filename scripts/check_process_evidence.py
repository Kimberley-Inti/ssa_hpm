#!/usr/bin/env python3
"""Check quantitative relationships in actual controlled-task simulator output."""
import argparse,json,pathlib,re
p=argparse.ArgumentParser();p.add_argument('results',type=pathlib.Path);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
def rows(text,task):
 groups=re.findall(task+r' parent cycle/instret/time, common cycle/instret/time, excluded cycle/instret/time:\n((?:[0-9a-f]{16}\n){9})',text)
 assert len(groups)==2,(task,len(groups))
 return [list(map(lambda x:int(x,16),g.split())) for g in groups]
legacy=(a.results/'rtl-process-legacy.txt').read_text();fixed=(a.results/'rtl-process.txt').read_text()
la=rows(legacy,'A');fa=rows(fixed,'A');fb=rows(fixed,'B')
assert la[1][4]>la[0][4],la
assert fa[0][4]==fa[1][4]>0,fa
assert fa[0][1]==fa[1][1] and all(r[1]>=r[4] for r in fa+fb)
assert fb[1][4]>fb[0][4],fb
assert all(fa[1][i]>fa[0][i] for i in (6,7,8)),fa
assert la[1][4]-la[0][4]==fa[1][7]-fa[0][7]
assert '0000000000001000' in legacy and 'SSA PASS: two pools' in fixed
m=dict(passed=True,columns=['parent_cycle','parent_instret','parent_time','common_cycle','common_instret','common_time','off_cycle','off_instret','off_time'],legacy_A=la,corrected_A=fa,corrected_B=fb,excluded_other_task_instret=fa[1][7]-fa[0][7])
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m,indent=2))
