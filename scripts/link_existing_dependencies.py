#!/usr/bin/env python3
"""Reuse matching local dependencies for a reconstructed workspace only.

This never replaces the patched Rocket tree, and checks every linked dependency
against the reconstructed superproject's gitlink. Source working trees must be
clean (untracked build artifacts do not affect the source diff). It is an
optional VM acceleration path, not an alternative source baseline.
"""
import argparse,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('workspace',type=pathlib.Path);p.add_argument('existing',type=pathlib.Path);p.add_argument('--report',type=pathlib.Path);a=p.parse_args()
w=a.workspace.resolve();s=a.existing.resolve()
assert w!=s and (w/'ssa').is_dir() and (w/'generators/rocket-chip/.git').exists()
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
entries=git(w,'ls-tree','-r','HEAD').splitlines()+git(w/'generators/rocket-chip','ls-tree','-r','HEAD').splitlines()
linked=[];missing=[];mismatch=[]
for prefix,repo in [('',w),('generators/rocket-chip/',w/'generators/rocket-chip')]:
 for line in git(repo,'ls-tree','-r','HEAD').splitlines():
  meta,path=line.split('\t',1);mode,typ,sha=meta.split()
  if mode!='160000' or prefix+path=='generators/rocket-chip':continue
  rel=prefix+path;source=s/rel;dest=w/rel
  try:
   top=pathlib.Path(git(source,'rev-parse','--show-toplevel')).resolve()
   actual=git(source,'rev-parse','HEAD')
   if top!=source.resolve():raise ValueError('not a module')
   if actual!=sha:mismatch.append(dict(path=rel,expected=sha,actual=actual));continue
   if git(source,'diff','HEAD','--name-only'):raise ValueError('tracked changes')
  except (subprocess.CalledProcessError,ValueError):missing.append(rel);continue
  if dest.is_dir() and not dest.is_symlink() and not any(dest.iterdir()):dest.rmdir()
  if dest.exists() or dest.is_symlink():raise RuntimeError('destination is not empty: '+rel)
  dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(source,target_is_directory=True)
  linked.append(dict(path=rel,sha=sha))
for rel in ['.conda-env']:
 if (s/rel).is_dir() and not (w/rel).exists():(w/rel).symlink_to(s/rel,target_is_directory=True)
result=dict(linked=linked,unavailable=missing,mismatched=mismatch)
if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if mismatch:raise SystemExit('refused mismatched dependencies; initialize them from upstream instead')
