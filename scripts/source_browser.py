#!/usr/bin/env python3
"""Generate/check a small source browser from pinned, patch-reconstructed trees."""
import argparse,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
COMPONENTS={
 'rocket-chip':dict(url='https://github.com/chipsalliance/rocket-chip.git',base='44b0b8249279d25bd75ea693b725d9ff1b96e2ab',tree='0c41414a848beded9c96acc413a3d85eec00ef9b',files=['src/main/scala/rocket/RocketCore.scala','src/main/scala/rocket/CSR.scala','src/main/scala/rocket/IDecode.scala','src/main/scala/rocket/SSAMemoryClassifier.scala','src/main/resources/ssa/microcode.S','scripts/gen-ssa-rom.py','LICENSE.Berkeley','LICENSE.SiFive']),
 'linux':dict(url='https://github.com/firesim/linux.git',base='5f5fd87b36e21ed59b759b69eebfa1c74955cb37',tree='c937114e57032e8f896bc853d1d63ff16e9bf8a7',files=['kernel/ssa_hpm.c','include/linux/ssa_hpm.h','COPYING','LICENSES/preferred/GPL-2.0','LICENSES/exceptions/Linux-syscall-note']),
 'opensbi':dict(url='https://github.com/riscv/opensbi.git',base='a98258d0b537a295f517bbc8d813007336731fa9',tree='c8e81125ce6b92976ccfff630c49a61d9d887e91',files=['platform/ssa_rocket/platform.c','platform/ssa_rocket/config.mk','platform/ssa_rocket/objects.mk','COPYING.BSD'])}
def patches(name):
 if name=='rocket-chip':return sorted((ROOT/'patches/rocket-chip').glob('*.patch'))
 d=ROOT/'integration/ssa/linux'
 return sorted(p for p in d.glob('*.patch') if ('opensbi' in p.name)==(name=='opensbi'))
def digest(b):return hashlib.sha256(b).hexdigest()
def run(args,cwd=None):return subprocess.check_output(list(map(str,args)),cwd=cwd,stderr=subprocess.STDOUT)
def reconstruct(name,d):
 c=COMPONENTS[name];ps=patches(name)
 env=os.environ.copy();env.update(GIT_COMMITTER_NAME='SSA-HPM reproduction',GIT_COMMITTER_EMAIL='reproduction@localhost')
 if not d.exists():
  d.mkdir(parents=True);run(['git','init','-b','source-browser'],d);run(['git','remote','add','upstream',c['url']],d)
  # Sparse partial reconstruction fetches all tree metadata but only affected blobs.
  run(['git','config','remote.upstream.promisor','true'],d);run(['git','config','remote.upstream.partialclonefilter','blob:none'],d)
  print('FETCH',name,c['base'],flush=True)
  run(['git','fetch','--depth=1','--filter=blob:none','--no-tags','upstream',c['base']],d)
  paths=set(c['files'])
  for p in ps:
   for line in p.read_text().splitlines():
    if line.startswith('+++ b/'):paths.add(line[6:])
  run(['git','sparse-checkout','init','--no-cone'],d)
  run(['git','sparse-checkout','set','--no-cone',*sorted('/'+p for p in paths)],d)
  run(['git','checkout','--detach','FETCH_HEAD'],d)
  for p in ps:
   print('APPLY',p.name,flush=True)
   subprocess.run(['git','am','--keep-cr',str(p)],cwd=d,env=env,stdout=subprocess.DEVNULL,check=True)
 tree=run(['git','rev-parse','HEAD^{tree}'],d).decode().strip()
 assert tree==c['tree'],(name,'tree mismatch',tree,c['tree'])
 run(['git','merge-base','--is-ancestor',c['base'],'HEAD'],d)
 accepted=json.loads((ROOT/'evidence/final-validation/source-commits.json').read_text())['candidate']
 return {'url':c['url'],'base':c['base'],'accepted_commit':accepted[{'rocket-chip':'rocket_chip','linux':'linux','opensbi':'opensbi'}[name]],'accepted_tree':tree,'patches':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in ps}}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['generate','check']);p.add_argument('--work',type=pathlib.Path,required=True,help='public-baseline reconstruction workspace, outside src/');a=p.parse_args();work=a.work.resolve()
 assert work!=ROOT and ROOT not in work.parents,'use an external workspace'
 # Full Chipyard reproduction is deliberately separate; its Rocket checkout may be reused after exact-tree verification.
 specs={};files={}
 for name,c in COMPONENTS.items():
  d=work/'generators/rocket-chip' if name=='rocket-chip' and (work/'generators/rocket-chip/.git').exists() else work/name
  specs[name]=reconstruct(name,d)
  for rel in c['files']:
   b=run(['git','show','HEAD:'+rel],d);dest=ROOT/'src'/name/rel;key=str(dest.relative_to(ROOT));files[key]={'sha256':digest(b),'component_path':rel}
   if a.action=='generate':dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
   else:assert dest.is_file() and dest.read_bytes()==b,'source-browser mismatch: '+key
 expected={'schema':1,'purpose':'Read-only source browser; build inputs remain the pinned patches.','components':specs,'files':files}
 manifest=ROOT/'src/manifest.json'
 if a.action=='generate':manifest.write_text(json.dumps(expected,indent=2)+'\n')
 else:assert json.loads(manifest.read_text())==expected,'source-browser manifest mismatch'
 actual={str(f.relative_to(ROOT)) for f in (ROOT/'src').rglob('*') if f.is_file() and f not in [manifest,ROOT/'src/README.md']}
 assert actual==set(files),'unexpected source-browser files'
 print('PASS',a.action,':',len(files),'exact files;',len(specs),'accepted component trees',flush=True)
if __name__=='__main__':
 try:main()
 except subprocess.CalledProcessError as e:
  if e.output:sys.stderr.write(e.output.decode(errors='replace'))
  raise
