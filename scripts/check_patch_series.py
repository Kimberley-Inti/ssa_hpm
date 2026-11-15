#!/usr/bin/env python3
"""Verify patch identities, explicit coverage and every legacy Linux mode selection."""
import ast,hashlib,itertools,json,pathlib,subprocess,types
ROOT=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'docs/PATCH_NAMES.json').read_text());series=json.loads((ROOT/'integration/ssa/patch-series.json').read_text())['components']
listed=[]
for component,spec in series.items():
 assert isinstance(spec['patches'],list) and spec['patches'],component
 for item in spec['patches']:
  f=ROOT/spec['directory']/item['file'];assert f.is_file() and not item['file'][0].isdigit(),str(f)
  assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'],str(f)
  listed.append(f.relative_to(ROOT).as_posix())
assert len(listed)==len(set(listed))
actual={p.relative_to(ROOT).as_posix() for d in ['patches','integration/ssa/linux'] for p in (ROOT/d).rglob('*.patch')}
assert actual==set(listed),(actual-set(listed),set(listed)-actual)
for old,new in m['renames'].items():
 original=subprocess.check_output(['git','show',m['baseline_commit']+':'+old],cwd=ROOT)
 assert original==(ROOT/new).read_bytes(),new
 assert hashlib.sha256(original).hexdigest()==m['sha256'][new]
# Execute only the trusted patch-selection blocks, with git/build calls captured.
old=subprocess.check_output(['git','show','v0.2.0:integration/ssa/linux/build-a.py'],cwd=ROOT,text=True)
new=(ROOT/'integration/ssa/linux/build-a.py').read_text()
def block(text,start):return text[text.index(start):text.index("url='https://archive.ubuntu")]
old_code=block(old,"run(['git','am',src/");new_code=block(new,"series=json.loads(")
assert old[:old.index(old_code)].replace("'stage4-linux'","'linux-reconstruction'")==new[:new.index(new_code)]
assert old[old.index("url='https://archive.ubuntu"):]==new[new.index("url='https://archive.ubuntu"):]
mode_names=['process','exec_test','event','export_test','classification','transparent','reference']
for flags in itertools.product([False,True],repeat=len(mode_names)):
 a=types.SimpleNamespace(**dict(zip(mode_names,flags)));results=[]
 for code in [old_code,new_code]:
  calls=[]
  def run(command,repo):calls.append((repo,pathlib.Path(command[-1]).name))
  env={'a':a,'src':ROOT/'integration/ssa/linux','linux':'linux','sbi':'opensbi','run':run,'json':json,'hashlib':hashlib}
  exec(compile(code,'<patch-selection>','exec'),env);results.append(calls)
 renamed={pathlib.Path(k).name:pathlib.Path(v).name for k,v in m['renames'].items()}
 assert [(repo,renamed[name]) for repo,name in results[0]]==results[1],dict(zip(mode_names,flags))
print('PASS',len(listed),'unchanged patches; explicit inventory; 128 Linux/OpenSBI flag combinations preserve legacy selection/order')
# Only the rename map and original raw evidence may reference obsolete names.
tracked=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
old_names=[pathlib.Path(n).name for n in m['renames']]
for n in set(tracked):
 p=ROOT/n
 if not p.is_file() or n=='docs/PATCH_NAMES.json' or p.suffix in ['.patch','.pdf','.zip','.pyc']:continue
 if n.startswith('evidence/') and p.suffix in ['.txt','.log','.sha256']:continue
 try:text=p.read_text()
 except UnicodeError:continue
 assert not any(name in text for name in old_names),('obsolete patch reference',n)
print('PASS current patch paths; historical raw captures are intentionally unchanged')
