#!/usr/bin/env python3
"""Audit every reachable commit/blob in the standalone release history."""
import argparse,json,pathlib,re,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report',type=pathlib.Path);p.add_argument('--ref',default='HEAD');a=p.parse_args()
ref=a.ref
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
commits=git('rev-list','--reverse',ref).decode().splitlines()
roots=git('rev-list','--max-parents=0',ref).decode().splitlines()
assert len(roots)==1,'release must have a single independent root'
forbidden_ext={'.pdf','.bundle','.bin','.elf','.riscv','.hex','.jar','.o','.a','.so','.xz','.gz','.zip'}
secret=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{20,}'),
        re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
        re.compile(rb'https?://[^\s/@:]+:[^\s/@]+@')]
seen=set();count=0
for commit in commits:
    # No upstream commits may be parents or extra roots.
    subject=git('show','-s','--format=%s',commit).decode().strip()
    assert not any(r.search(git('cat-file','commit',commit)) for r in secret),'possible secret in commit metadata'
    for line in git('ls-tree','-r',commit).decode().splitlines():
        meta,path=line.split('\t',1);mode,typ,sha=meta.split()
        assert mode!='160000',f'upstream gitlink in standalone repo: {path}'
        assert not path.startswith(('generators/','toolchains/','ssa/handoff/','handoff/','.git/')),path
        assert pathlib.PurePosixPath(path).suffix.lower() not in forbidden_ext,path
        assert not any(part in ('.ssh','.aws','.conda-env') for part in pathlib.PurePosixPath(path).parts),path
        if sha in seen:continue
        b=git('cat-file','blob',sha);seen.add(sha)
        assert len(b)<1024*1024,f'oversized artifact: {path}'
        assert b'\0' not in b,f'binary artifact: {path}'
        assert not any(r.search(b) for r in secret),f'possible secret in {path}, blob {sha}'
        count+=1
result=dict(passed=True,commits=len(commits),independent_roots=roots,unique_text_blobs=count,
            excluded='upstream trees/history, gitlinks, binaries, bundles, PDFs, credential patterns',
            scanned_ref=ref)
if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
