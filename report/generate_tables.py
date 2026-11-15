#!/usr/bin/env python3
"""Regenerate report tables and selected data from committed acceptance evidence."""
from pathlib import Path
import json,hashlib,shutil,csv
r=Path(__file__).resolve().parents[1];w=r/'report/source'
for d in ['sections','figures','tables','data','third_party']:(w/d).mkdir(exist_ok=True)
e=r/'evidence/stage11';inputs={'bare':e/'performance-final/summary.json','linux':e/'linux-performance-final/work-summary.json','kernel_cost':e/'linux-performance-final/phase-costs.json','switch':e/'linux-switch-proof/switch-accounting.json','acceptance':e/'summary.json','sources':e/'source-commits.json','instruction_accounting':e/'linux-instruction-accounting.json'}
d={k:json.loads(p.read_text()) for k,p in inputs.items()};d['provenance']={'validated_release':'v0.2.0','validated_main':'2adbfa5de81f341bd575e8498b370c5a12a02785','candidate':'9c1fdfb0e147c27f7aca58f306e91f532c3fb609','input_sha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs.values()}};(w/'data/measurements.json').write_text(json.dumps(d,indent=2)+'\n')
labels=['Compute','Calls128','Depth16','Stream32K','Irregular32K'];modes=[0,1,2,3,4,5];bare={(x['mode'],x['workload']):x for x in d['bare']['statistics']};linux={(x['mode'],x['workload']):x for x in d['linux']['statistics']}
def fmt(x):return f'{int(x):,}' if int(x)==x else f'{x:,.1f}'
def table(name,head,rows,caption,label):
 text=r'\begin{table*}[t]\centering\small'+'\n'+r'\begin{tabular}{l'+'r'*(len(head)-1)+r'}\toprule'+'\n'+' & '.join(head)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,row))+r'\\' for row in rows)+'\n'+r'\bottomrule\end{tabular}'+'\n'+r'\caption{'+caption+'}'+r'\label{'+label+'}'+'\n'+r'\end{table*}'+'\n';(w/'tables'/name).write_text(text)
table('bare-cycles.tex',['Workload','Off','Base','DTLB','Cache','Class.','Cache+class.'],[[labels[k]]+[fmt(bare[m,k]['cycle']['median']) for m in modes] for k in range(5)],'Bare-metal cycle medians on the same extended model. Each cell has five measured repetitions after one warmup. DTLB mode here exercises ABI2 snapshot cost on physical-address accesses.','tab:barecycles')
table('linux-cycles.tex',['Workload','Off','Base','Cache','Class.','Manual C+C','Auto C+C'],[[labels[k]]+[fmt(linux[m,k]['cycle']['median']) for m in [0,1,3,4,6,5]] for k in range(5)],'Linux cycle medians. C+C denotes Cache plus classification. Manual and automatic C+C use matched profiles; interrupt and cache phase contribute to variation.','tab:linuxcycles')
table('bare-instructions.tex',['Workload','Off','Base','Event ABI2'],[[labels[k]]+[fmt(bare[m,k]['instret']['median']) for m in [0,1,3]] for k in range(5)],'Bare-metal retired-instruction medians. Classification matches the corresponding base/event instruction count in these measurements.','tab:bareinst')
ph=d['kernel_cost']['statistics'];rows=[]
for n in ['dictionary_init','freeze','record_copy','export','pause','resume','exec_failed','exec_ready']:
 x=ph[n];c=x['cycle'];rows.append([n.replace('_',r'\_'),x['n'],fmt(c['min']),fmt(c['median']),fmt(c['max']),fmt(x['instret']['median']),fmt(x['time']['median'])])
table('kernel-costs.tex',['Kernel observation','$n$','Cycle min','Median','Max','Instret med.','Time med.'],rows,'Instrumented Linux phase observations from the full performance capture. Time is in CLINT ticks. Phases have different boundaries and session sizes; freeze/copy are subsets of export.','tab:costs')
with (w/'data/overhead.csv').open('w') as f:
 fields=['workload']+[m+s for m in ['base','dtlb','cache','class','cacheclass'] for s in ['', '_lo','_hi']];writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader()
 for k,label in enumerate(labels):
  row={'workload':label};baseline=bare[0,k]['cycle']['median']
  for m,name in [(1,'base'),(2,'dtlb'),(3,'cache'),(4,'class'),(5,'cacheclass')]:
   v=bare[m,k]['cycle'];row.update({name:v['median']/baseline,name+'_lo':(v['median']-v['min'])/baseline,name+'_hi':(v['max']-v['median'])/baseline})
  writer.writerow(row)
print('Prepared report tables from immutable evidence')
