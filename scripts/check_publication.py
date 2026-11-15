#!/usr/bin/env python3
"""Verify functional navigation, report packaging and preserved implementation."""
import hashlib,json,pathlib,re,subprocess,zipfile,urllib.parse
r=pathlib.Path(__file__).resolve().parents[1]
def git(*a):return subprocess.check_output(['git','-C',str(r),*a])
files=[r/x for x in ('README.md','REPRODUCE.md','THIRD_PARTY.md')]+list((r/'docs').glob('*.md'))+[r/'report/README.md']
checked=0;errors=[]
for p in files:
 s=p.read_text()
 if p.name!='HISTORY.md':
  for label,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',s):
   target=target.strip('<>');u=urllib.parse.urlsplit(target)
   if u.scheme or target.startswith('#'):continue
   dest=(p.parent/urllib.parse.unquote(u.path)).resolve()
   if not dest.exists():errors.append(f'{p.relative_to(r)}: {target}')
   checked+=1
 if p.name not in ('HISTORY_MAP.json',):
  assert not re.search(r'^#+\s+.*\bStage\s*\d',s,re.I|re.M),p
assert not re.search(r'[\u3400-\u9fff]',(r/'README.md').read_text()),'README must be English'
assert not errors,'Broken local links:\n'+'\n'.join(errors)
with zipfile.ZipFile(r/'report/SSA-HPM-overleaf.zip') as z:
 source={p.relative_to(r/'report/source').as_posix():p.read_bytes() for p in (r/'report/source').rglob('*') if p.is_file()}
 assert set(z.namelist())==set(source)
 for n,b in source.items():assert z.read(n)==b,n
 assert r'\author{Liu Qinruo}' in source['main.tex'].decode()
assert git('rev-parse','v0.2.0^{}').decode().strip()=='2adbfa5de81f341bd575e8498b370c5a12a02785'
assert git('rev-parse','v0.1.0^{}').decode().strip()=='0421e67203e0cfb63d96699f061ffa7d8d00fddf'
# No patch byte or implementation source changes relative to the accepted release.
changes=git('diff','v0.2.0','--','patches').decode();assert not changes,'implementation patches changed'
for line in git('diff','--name-only','v0.2.0','--','integration').decode().splitlines():assert pathlib.Path(line).suffix=='.md',line
print(json.dumps({'passed':True,'local_document_links':checked,'packaged_source_files':len(source),'release_tags_preserved':True,'implementation_patches_unchanged':True},indent=2))
