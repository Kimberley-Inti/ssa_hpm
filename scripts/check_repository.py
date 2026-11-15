#!/usr/bin/env python3
"""Verify repository navigation, installed-file manifests, report packaging and preserved implementation."""
import hashlib,json,pathlib,re,subprocess,zipfile,urllib.parse
r=pathlib.Path(__file__).resolve().parents[1]
def git(*a):return subprocess.check_output(['git','-C',str(r),*a])
files=[r/x for x in ('README.md','HISTORY.md','REPRODUCE.md','THIRD_PARTY.md')]+list((r/'docs').glob('*.md'))+list((r/'integration').rglob('*.md'))+list((r/'report').rglob('*.md'))+list((r/'src').rglob('*.md'))
checked=0;errors=[]
for p in files:
 s=p.read_text()
 if True:
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
# Renames change paths, not implementation bytes; selection equivalence is checked separately.
subprocess.run(['python3',str(r/'scripts/check_patch_series.py')],check=True)
print(json.dumps({'passed':True,'local_document_links':checked,'packaged_source_files':len(source),'release_tags_preserved':True,'implementation_patches_unchanged':True},indent=2))

manifest=json.loads((r/'provenance.json').read_text())
for path,expected in manifest['expected_files'].items():
 source=r/'integration'/path
 if source.exists():assert hashlib.sha256(source.read_bytes()).hexdigest()==expected,path
for entry in (r/'evidence').rglob('*manifest.json'):
 data=json.loads(entry.read_text())
 if isinstance(data,dict) and isinstance(data.get('files'),dict):
  for path,expected in data['files'].items():
   target=r/path
   if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==expected,(str(entry),path)
   elif path.startswith(('evidence/','integration/','docs/','patches/')):raise AssertionError((str(entry),'missing',path))
print('PASS installed-source and evidence manifests')

source_manifest=json.loads((r/'src/manifest.json').read_text())
for path,entry in source_manifest['files'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==entry['sha256'],path
for component in source_manifest['components'].values():
 for path,expected in component['patches'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==expected,path
measurement=json.loads((r/'report/source/data/measurements.json').read_text())
for path,expected in measurement['provenance']['input_sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==expected,path
print('PASS source-browser hashes and report measurement inputs')
