#!/usr/bin/env python3
"""Fetch pinned public baselines into a NEW workspace and apply project patches.

No submodule update is run against the original development tree. Existing
nonempty destinations are rejected to preserve user work.
"""
import argparse,hashlib,json,os,pathlib,shutil,subprocess
release=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('workspace',type=pathlib.Path)
p.add_argument('--report',type=pathlib.Path)
a=p.parse_args();work=a.workspace.resolve()
if work.exists() and any(work.iterdir()):p.error('workspace must be absent or empty')
m=json.loads((release/'provenance.json').read_text());commands=[]
env=os.environ.copy();env.update(GIT_COMMITTER_NAME='SSA-HPM reproduction',GIT_COMMITTER_EMAIL='reproduction@localhost')
def run(args,cwd=None):
    commands.append(dict(argv=list(map(str,args)),cwd=str(cwd) if cwd else None))
    return subprocess.check_output(list(map(str,args)),cwd=cwd,env=env,stderr=subprocess.STDOUT).decode()
def init(repo,url,sha):
    repo.mkdir(parents=True,exist_ok=True)
    run(['git','init','-b','ssa-hpm-reproduce'],repo)
    run(['git','remote','add','upstream',url],repo)
    print('FETCH',url,sha,flush=True)
    run(['git','fetch','--no-tags','--depth=1','upstream',sha],repo)
    run(['git','checkout','--detach','FETCH_HEAD'],repo)
    assert run(['git','rev-parse','HEAD'],repo).strip()==sha
try:
    init(work,m['chipyard']['url'],m['chipyard']['base'])
    rocket=work/'generators/rocket-chip'
    init(rocket,m['rocket_chip']['url'],m['rocket_chip']['base'])
    for kind,repo in [('chipyard',work),('rocket-chip',rocket)]:
        for patch in sorted((release/'patches'/kind).glob('*.patch')):
            print('APPLY',patch.relative_to(release),flush=True)
            run(['git','am','--keep-cr',patch],repo)
    tree=run(['git','rev-parse','HEAD^{tree}'],rocket).strip()
    assert tree==m['rocket_chip']['expected_tree'],(tree,m['rocket_chip']['expected_tree'])
    # Tests are supplied as standalone project files, not duplicated in patches.
    shutil.copytree(release/'integration/ssa',work/'ssa')
    (work/'ssa/microcode.S').symlink_to('../generators/rocket-chip/src/main/resources/ssa/microcode.S')
    run(['git','add','-f','ssa'],work)
    run(['git','commit','-m','Install SSA-HPM standalone validation suite'],work)
    checks={}
    for rel,expected in m.get('expected_files',m['accepted_files']).items():
        path=work/rel
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual==expected,rel
        checks[rel]=actual
    run(['python3','ssa/gen_rom.py','--check'],work)
    result=dict(passed=True,chipyard_base=m['chipyard']['base'],rocket_base=m['rocket_chip']['base'],
                rocket_tree=tree,exact_file_hashes=checks,commands=commands)
except subprocess.CalledProcessError as e:
    print(e.output.decode(errors='replace'))
    raise
if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n')
print('PASS: public baseline fetch, clean patch application, exact accepted source hashes, ROM check',flush=True)
print('Workspace:',work)
