#!/usr/bin/env python3
"""Merge only the authorized SSA-HPM stage PRs after final acceptance.

Default is a read-only plan. --execute requires a clean accepted candidate,
validated evidence and the exact frozen stage heads. Never rewrites history,
deletes branches, changes visibility, or replaces an existing tag.
"""
import argparse,hashlib,json,pathlib,subprocess,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1];REPO='Kimberley-Inti/ssa_hpm'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pr',type=int,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
assert not a.receipt.resolve().is_relative_to(ROOT),'keep integration receipt outside the accepted Git tree'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.PIPE).strip()
def api(path,method='GET',data=None):
 cmd=['gh','api',path,'--method',method]
 if data is None:return json.loads(subprocess.check_output(cmd,text=True,stderr=subprocess.PIPE))
 with tempfile.NamedTemporaryFile(mode='w') as f:
  json.dump(data,f);f.flush();return json.loads(subprocess.check_output(cmd+['--input',f.name],text=True,stderr=subprocess.PIPE))
who=api('user');assert who['login']=='Kimberley-Inti' and who['id']==185574409
repo=api('repos/'+REPO);assert repo['private'] and repo['permissions']['push'] and repo['default_branch']=='main'
candidate=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}')
original=json.loads((ROOT/'evidence/stage11/pulls-baseline.json').read_text());original=sorted(original,key=lambda x:x['number'])
assert len(original)==9 and [x['number'] for x in original]==list(range(1,10))
plan=[]
for saved in original:
 pr=api('repos/'+REPO+'/pulls/'+str(saved['number']));assert pr['head']['repo']['full_name']==REPO and pr['head']['ref']==saved['head'] and pr['head']['sha']==saved['sha']
 assert subprocess.run(['git','merge-base','--is-ancestor',pr['head']['sha'],candidate],cwd=ROOT).returncode==0
 plan.append(pr)
last=api('repos/'+REPO+'/pulls/'+str(a.pr));assert a.pr not in range(1,10) and last['head']['repo']['full_name']==REPO and last['head']['ref']=='stage11-final-validation' and last['head']['sha']==candidate
assert last['base']['ref']=='stage10-transparent-launch';plan.append(last)
receipt={'candidate_sha':candidate,'candidate_tree':tree,'private':True,'plan':[{'pr':x['number'],'head':x['head']['sha'],'base':x['base']['ref'],'url':x['html_url']} for x in plan],'executed':False};a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
if not a.execute:print(json.dumps(receipt,indent=2));raise SystemExit(0)
assert not git('status','--porcelain'),'accepted candidate must be committed and clean'
gate=json.loads((ROOT/'evidence/stage11/summary.json').read_text());assert gate['passed'] and all(gate['checks'].values())
manifest=json.loads((ROOT/'evidence/stage11/artifact-manifest.json').read_text())
for name,sha in manifest['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
with tempfile.TemporaryDirectory(prefix='ssa-final-gate-') as d:
 subprocess.run(['python3','scripts/final.py','check-evidence','--out',d],cwd=ROOT,check=True)
subprocess.run(['python3','scripts/audit.py'],cwd=ROOT,check=True)
old_tags=api('repos/'+REPO+'/tags');receipt['tags_before']=old_tags;receipt['merges']=[]
for pr in plan:
 n=pr['number'];live=api('repos/'+REPO+'/pulls/'+str(n));assert live['head']['sha']==pr['head']['sha']
 if not live['merged']:
  assert live['state']=='open'
  if live['base']['ref']!='main':api('repos/'+REPO+'/pulls/'+str(n),'PATCH',{'base':'main'})
  # Review the exact remaining diff after the previous merge, before mutation.
  diff=api('repos/'+REPO+'/pulls/'+str(n)+'/files?per_page=100');receipt['merges'].append({'pr':n,'diff_files':[x['filename'] for x in diff]})
  if live['draft']:
   api('graphql','POST',{'query':'mutation($id:ID!){markPullRequestReadyForReview(input:{pullRequestId:$id}){pullRequest{isDraft}}}','variables':{'id':live['node_id']}})
  for attempt in range(6):
   try:
    result=api('repos/'+REPO+'/pulls/'+str(n)+'/merge','PUT',{'sha':pr['head']['sha'],'merge_method':'merge','commit_title':'Merge SSA-HPM stage PR #'+str(n)})
    assert result['merged'];break
   except subprocess.CalledProcessError:
    if attempt==5:raise
    time.sleep(5)
  live=api('repos/'+REPO+'/pulls/'+str(n));assert live['merged'] and live['state']=='closed'
 else:receipt['merges'].append({'pr':n,'already_merged':True})
 receipt['merges'][-1].update(url=live['html_url'],merge_commit_sha=live['merge_commit_sha']);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
main=api('repos/'+REPO+'/commits/main');assert main['commit']['tree']['sha']==tree,'merged tree differs: inspect and verify before release'
subprocess.run(['git','fetch','origin','main'],cwd=ROOT,check=True);subprocess.run(['git','switch','main'],cwd=ROOT,check=True);subprocess.run(['git','merge','--ff-only','origin/main'],cwd=ROOT,check=True);assert git('rev-parse','HEAD')==main['sha']
existing={x['name'] for x in api('repos/'+REPO+'/tags')};tag='v0.2.0';patch=0
while tag in existing or git('tag','--list',tag):patch+=1;tag='v0.2.'+str(patch)
subprocess.run(['git','-c','tag.gpgSign=false','tag','-a',tag,main['sha'],'-m','SSA-HPM accepted single-hart research prototype'],cwd=ROOT,check=True);subprocess.run(['git','push','origin','refs/tags/'+tag],cwd=ROOT,check=True)
body='Accepted single-hart SSA-HPM research prototype.\n\nMain: '+main['sha']+'\nCandidate: '+candidate+'\n\nSee docs/STAGE11.md, docs/PERFORMANCE.md, docs/ACCEPTANCE.md and REPRODUCE.md for actual coverage and limits.\n\nFast evidence replay: python3 scripts/final.py check-evidence --out /tmp/ssa-evidence-check\n\nStage PRs were integrated with merge commits; original commits, branches and v0.1.0 are retained. No unextended-hardware, area or universal Linux application support claim.'
release=api('repos/'+REPO+'/releases','POST',{'tag_name':tag,'target_commitish':main['sha'],'name':'SSA-HPM '+tag+' — single-hart research prototype','body':body,'draft':False,'prerelease':False})
assert api('repos/'+REPO)['private'] and api('repos/'+REPO+'/commits/main')['sha']==main['sha']
for old in old_tags:
 now=next(x for x in api('repos/'+REPO+'/tags') if x['name']==old['name']);assert now['commit']['sha']==old['commit']['sha']
ref=api('repos/'+REPO+'/git/ref/tags/'+tag);obj=ref['object']
if obj['type']=='tag':obj=api('repos/'+REPO+'/git/tags/'+obj['sha'])['object']
assert obj['type']=='commit' and obj['sha']==main['sha']
receipt.update(executed=True,main_sha=main['sha'],tree_identical=True,tag=tag,release_url=release['html_url'],release_id=release['id']);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
