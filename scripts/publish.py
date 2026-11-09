#!/usr/bin/env python3
"""Publish the audited private release using an explicitly verified gh identity.

Requires an interactive gh login already completed by the repository owner.
Never logs tokens, force-pushes, overwrites tags, or repurposes another repo.
"""
import base64,json,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
repo='Kimberley-Inti/ssa_hpm';url='https://github.com/'+repo+'.git'
def run(args,**kw):return subprocess.check_output(args,cwd=root,stderr=subprocess.PIPE,**kw).decode().strip()
def api(path,method='GET',data=None):
    cmd=['gh','api',path,'--method',method]
    if data is None:return json.loads(run(cmd))
    with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
        json.dump(data,f);f.flush();return json.loads(run(cmd+['--input',f.name]))
who=api('user')
assert who['login']=='Kimberley-Inti' and who['id']==185574409,'gh must authenticate Kimberley-Inti (185574409)'
assert not run(['git','status','--porcelain']),'commit the checked release contents first'
subprocess.run(['python3','scripts/audit.py'],cwd=root,check=True)
try:r=api('repos/'+repo);created=False
except subprocess.CalledProcessError as e:
    if b'404' not in e.stderr:raise
    r=api('user/repos','POST',dict(name='ssa_hpm',private=True,description='SSA-HPM: software context aware Rocket performance monitoring',auto_init=False));created=True
assert r['private'] and not r.get('fork') and r['owner']['login']==who['login']
assert r.get('permissions',{}).get('push',created),'authenticated account lacks push permission'
# Existing nonempty repositories must identify this exact accepted project.
if not created and r.get('size',0)>0:
    try:
        proof=api('repos/'+repo+'/contents/provenance.json')
        m=json.loads(base64.b64decode(proof['content']))
        assert m['rocket_chip']['accepted_delivery']=='986407bc6df8d2a67572250f1df9eb2c0edeacf9'
    except Exception:raise SystemExit('Repository name conflict: existing contents were preserved; owner must resolve it')
assert run(['git','branch','--show-current'])=='main','publish from main only'
head=run(['git','rev-parse','HEAD'])
existing=run(['git','ls-remote',url,'refs/tags/v0.1.0','refs/tags/v0.1.0^{}'])
if existing:
    target=existing.splitlines()[-1].split()[0]
    assert target==head,'v0.1.0 already exists at another commit; existing tag preserved'
    if not run(['git','tag','--list','v0.1.0']):
        subprocess.run(['git','fetch','--no-tags',url,'refs/tags/v0.1.0:refs/tags/v0.1.0'],cwd=root,check=True)
    else:assert run(['git','rev-parse','v0.1.0^{}'])==head,'local version conflict'
else:
    local_tag=run(['git','tag','--list','v0.1.0'])
    if local_tag:assert run(['git','rev-parse','v0.1.0^{}'])==head,'local version conflict'
    else:subprocess.run(['git','tag','-a','v0.1.0','-m','SSA-HPM first-stage validated private release'],cwd=root,check=True)
remotes=run(['git','remote']).splitlines()
if 'origin' not in remotes:subprocess.run(['git','remote','add','origin',url],cwd=root,check=True)
else:assert run(['git','remote','get-url','origin'])==url,'existing origin differs; left unchanged'
subprocess.run(['git','config','--local','--add','credential.https://github.com.helper',''],cwd=root,check=True)
subprocess.run(['git','config','--local','--add','credential.https://github.com.helper','!/usr/bin/gh auth git-credential'],cwd=root,check=True)
subprocess.run(['git','push','--atomic','-u','origin','main','refs/tags/v0.1.0'],cwd=root,check=True)
api('repos/'+repo,'PATCH',dict(default_branch='main'))
r=api('repos/'+repo);c=api('repos/'+repo+'/commits/main')
assert r['private'] and r['default_branch']=='main' and c['sha']==head
assert c['commit']['tree']['sha']==run(['git','rev-parse','HEAD^{tree}'])
checked=[]
for path in ['README.md','HISTORY.md','provenance.json','REPRODUCE.md','scripts/apply.py',
             'patches/rocket-chip/0008-986407bc6.patch','integration/ssa/test.c']:
    f=api('repos/'+repo+'/contents/'+path+'?ref=v0.1.0')
    assert base64.b64decode(f['content'])==(root/path).read_bytes(),path
    checked.append(path)
print(json.dumps(dict(url=r['html_url'],private=True,default_branch=r['default_branch'],head=head,
                     tag='v0.1.0',remote_tag=run(['git','ls-remote','origin','refs/tags/v0.1.0','refs/tags/v0.1.0^{}']),
                     tree_verified=True,files_verified=checked),indent=2))
