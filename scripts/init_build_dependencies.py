#!/usr/bin/env python3
"""Initialize the pinned submodules used by the recorded RocketConfig build.

Run only in a workspace created by apply.py. Never update the Rocket gitlink:
that would move its checkout away from the applied SSA-HPM patch series.
"""
import argparse,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('workspace',type=pathlib.Path);a=p.parse_args();w=a.workspace.resolve()
assert (w/'ssa').is_dir() and (w/'generators/rocket-chip/scripts/gen-ssa-rom.py').is_file()
profile=json.loads((root/'evidence/publication/dependencies.json').read_text())
for item in profile['linked']:
    rel=item['path'];prefix='generators/rocket-chip/'
    parent=w/prefix if rel.startswith(prefix) else w
    path=rel.removeprefix(prefix) if rel.startswith(prefix) else rel
    assert rel!='generators/rocket-chip'
    subprocess.run(['git','submodule','update','--init','--recursive','--',path],cwd=parent,check=True)
    actual=subprocess.check_output(['git','-C',str(w/rel),'rev-parse','HEAD'],text=True).strip()
    assert actual==item['sha'],rel
subprocess.run(['python3','ssa/gen_rom.py','--check'],cwd=w,check=True)
