#!/usr/bin/env python3
"""Audit standalone Git history; permit only the curated, inspectable report binaries."""
import argparse,io,json,pathlib,re,subprocess,tempfile,zipfile,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=pathlib.Path);p.add_argument('--ref',default='HEAD');p.add_argument('--all',action='store_true',help='scan all local/remote refs and tags');a=p.parse_args()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
refs=['--all'] if a.all else [a.ref]
commits=git('rev-list','--reverse',*refs).decode().splitlines()
roots=git('rev-list','--max-parents=0',*refs).decode().splitlines()
assert len(set(roots))==1,'standalone history must retain a single independent root'
forbidden_ext={'.pdf','.bundle','.bin','.elf','.riscv','.hex','.jar','.o','.a','.so','.xz','.gz','.zip'}
secret=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{20,}'),re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),re.compile(rb'https?://[^\s/@:]+:[^\s/@]+@')]
residue=[b'LANChat', b'student ID:', b'student number:']
def inspect(b,label,template=False):
 assert not any(x.search(b) for x in secret),'possible credential: '+label
 if template:assert not any(x.lower() in b.lower() for x in residue),'template personal/example residue: '+label
seen=set();binary=[];count=0
for commit in commits:
 inspect(git('cat-file','commit',commit),commit)
 for line in git('ls-tree','-r',commit).decode().splitlines():
  meta,path=line.split('\t',1);mode,typ,sha=meta.split()
  assert mode!='160000','upstream gitlink: '+path
  assert not path.startswith(('generators/','toolchains/','ssa/handoff/','handoff/','.git/')),path
  assert not any(x in ('.ssh','.aws','.conda-env') for x in pathlib.PurePosixPath(path).parts),path
  if sha in seen:continue
  seen.add(sha);b=git('cat-file','blob',sha);suffix=pathlib.PurePosixPath(path).suffix.lower()
  if path=='report/SSA-HPM-report.pdf':
   assert len(b)<2*1024*1024
   with tempfile.TemporaryDirectory() as d:
    f=pathlib.Path(d)/'report.pdf';f.write_bytes(b)
    info=subprocess.check_output(['pdfinfo',str(f)]).decode();assert re.search(r'Author:\s+Liu Qinruo\s*\n',info),info
    t=subprocess.check_output(['pdftotext',str(f),'-']);inspect(t,path,True)
   binary.append({'path':path,'sha256':hashlib.sha256(b).hexdigest()});continue
  if path=='report/SSA-HPM-overleaf.zip':
   assert len(b)<2*1024*1024
   with zipfile.ZipFile(io.BytesIO(b)) as z:
    assert 'main.tex' in z.namelist()
    for n in z.namelist():
     q=pathlib.PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
     assert q.suffix in ('.tex','.sty','.bst','.bib','.md','.json','.csv','.txt'),n
     d=z.read(n);assert len(d)<1024*1024;inspect(d,n,True)
   binary.append({'path':path,'sha256':hashlib.sha256(b).hexdigest()});continue
  assert suffix not in forbidden_ext,path
  assert len(b)<1024*1024,'oversized artifact: '+path
  assert b'\0' not in b,'unexpected binary: '+path
  inspect(b,path,path.startswith('report/'));count+=1
result=dict(passed=True,commits=len(commits),independent_roots=roots,unique_text_blobs=count,curated_report_binaries=binary,scanned_ref='all refs and tags' if a.all else a.ref,excluded='upstream trees/history, gitlinks, binaries except inspected authored report, bundles, design PDFs, credentials')
if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
