#!/usr/bin/env python3
"""Check functional evidence references and byte-preserved historical logs."""
import hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'docs/EVIDENCE_PATHS.json').read_text())['directories']
for old,new in m.items():assert not (ROOT/old).exists() and (ROOT/new).is_dir(),(old,new)
pattern=re.compile(r'evidence/(?:'+ '|'.join(re.escape(pathlib.PurePosixPath(x).name) for x in m)+r')(?=/|[\s\x27\x22]|$)')
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines();errors=[]
for n in set(files):
 p=ROOT/n
 if not p.is_file() or n.startswith('patches/') or p.suffix in ['.patch','.pdf','.zip','.pyc']:continue
 if n=='docs/EVIDENCE_PATHS.json' or (n.startswith('evidence/') and p.suffix in ['.txt','.log','.sha256']):continue
 try:s=p.read_text()
 except UnicodeError:continue
 if pattern.search(s):errors.append(n)
assert not errors,('stale current evidence references',sorted(errors))
raw=json.loads((ROOT/'evidence/raw-log-manifest.json').read_text())
for n,h in raw['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
print('PASS functional paths;',len(raw['files']),'original log/hash files unchanged')
