#!/usr/bin/env python3
"""Destructive cleanup gated by two remote proofs, current hashes and explicit flag.
Preserves the original repository/Git metadata and global/unrelated content.
Never runs as part of verification or merely by importing this file.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,shutil,subprocess

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(project,*args,input=None):
 r=subprocess.run(['git','-C',str(project),*args],input=input,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout

def cleanup(sp,execute):
 assert execute,'Pass --execute only after reviewing both remote verification records'
 sp=sp.resolve();s=json.loads(sp.read_text());p=Path(s['project']);g=Path(s['gitdir']);a=Path(s['archive_root']);label=s['final_label'];v=s['verifications'][label];commit=s['final_commit']
 assert v['commit']==commit and v['http']['result']=='PASS'and v['fresh']['result']=='PASS','Both independent gates must pass the same final commit'
 assert git(p,'rev-parse','HEAD').decode().strip()==commit
 assert git(p,'ls-remote','origin','refs/heads/'+s['branch']).decode().split()[0]==commit,'Remote advanced; reverify before cleanup'
 assert not(g/'index.lock').exists(),'Another Git operation may be active'
 assert not git(p,'diff','HEAD','--name-only').strip(),'Uncommitted tracked modifications; do not delete'
 assert not git(p,'diff','--cached','--name-only').strip(),'Staged user changes; do not delete'
 expected=json.loads(Path(s['freezes'][label]).read_text())
 spec=importlib.util.spec_from_file_location('checked_archive',sp.parent/'verify_archive.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.verify(a,expected)
 eligible=[x for x in s['files']if x['cleanup_eligible']]
 # Preflight every original file and detect unique/new unarchived project files.
 known={Path(x['absolute_source'])for x in s['files']if x['source_group']=='project'}
 unknown=[]
 for root,dirs,names in os.walk(p,followlinks=False):
  for name in names:
   f=Path(root)/name
   if f.is_relative_to(g)or f.is_relative_to(a)or f==p/'.git':continue
   if f not in known:unknown.append(str(f.relative_to(p)))
 assert not unknown,'New unarchived files must be retained: '+str(unknown)
 for x in eligible:
  f=Path(x['absolute_source']);assert f.is_file()and f.stat().st_size==x['size']and sha(f)==x['sha256'],'Source changed; retain '+str(f)
 # Protect original Git metadata by relocating it to the conventional root .git.
 # The old .git pointer is moved INTO that metadata, never deleted.
 old_pointer=p/'.git';assert old_pointer.is_file()and old_pointer.read_text().strip()=='gitdir: '+str(g)
 relative_control=sp.parent.relative_to(g);newg=p/'.git';backup=g/relative_control/'original-gitdir-pointer.txt';assert not backup.exists()
 old_pointer.rename(backup)
 try:g.rename(newg)
 except Exception:
  backup.rename(old_pointer);raise
 newcontrol=newg/relative_control;sp=newcontrol/'state.json';s['gitdir']=str(newg);s['control']=str(newcontrol)
 try:assert git(p,'rev-parse','--show-toplevel').decode().strip()==str(p);assert git(p,'rev-parse','HEAD').decode().strip()==commit
 except Exception:
  newg.rename(g);(g/relative_control/'original-gitdir-pointer.txt').rename(old_pointer);raise
 assert sha(newcontrol/'original-gitdir-pointer.txt')==next(x['sha256']for x in s['files']if x['source_group']=='project'and x['relative_path']=='.git')
 s['cleanup_started']=True;s['cleanup_started_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();sp.write_text(json.dumps(s,indent=2)+'\n')
 removed=[];bytes_removed=0
 for x in eligible:
  f=Path(x['absolute_source']);assert not f.is_relative_to(newg)
  assert f.is_file()and sha(f)==x['sha256'],'File changed during cleanup; stop and retain '+str(f)
  f.unlink();removed.append({'group':x['source_group'],'path':x['relative_path'],'bytes':x['size']});bytes_removed+=x['size']
 # Remove the local archive only after each exact frozen file is rechecked.
 for rel,x in expected['files'].items():
  f=a/rel;assert f.is_file()and f.stat().st_size==x['size']and sha(f)==x['sha256'];f.unlink();bytes_removed+=x['size']
 # Only remove directories that are now empty; never recursively delete user directories.
 for root,dirs,names in os.walk(p,topdown=False,followlinks=False):
  d=Path(root)
  if d==p or d.is_relative_to(newg):continue
  try:d.rmdir()
  except OSError:pass
 # Remove only this task's owned verification clones/downloads/restores/jobs.
 temp=Path(s['temp_root']);owner=json.loads((temp/'TASK_OWNER.json').read_text());assert owner['createdAtUtc']==s['createdAtUtc']and owner['project']==s['project'];assert temp.parent==Path('/home/user/.cache')and temp.name.startswith('video-editing-archive-')
 shutil.rmtree(temp)
 # Clean, empty sparse worktree: index flags/config only, no commit/reset/remote deletion.
 git(p,'config','core.sparseCheckout','true');git(p,'config','core.sparseCheckoutCone','false');(newg/'info').mkdir(exist_ok=True);(newg/'info/sparse-checkout').write_text('!/*\n')
 tracked=git(p,'ls-files','-z');git(p,'update-index','--skip-worktree','-z','--stdin',input=tracked)
 status=git(p,'status','--porcelain').decode();assert not status.strip(),'Unexpected remaining worktree change: '+status
 remaining=[str(f.relative_to(p))for f in p.rglob('*')if f.is_file()and not f.is_relative_to(newg)];assert not remaining,'Unexpected non-Git project files remain'
 protected_global=[x for x in s['files']if not x['cleanup_eligible']and x['source_group']=='global-pip-cache']
 for x in protected_global:assert Path(x['absolute_source']).exists(),'Global cache unexpectedly removed'
 assert git(p,'rev-parse','HEAD').decode().strip()==commit
 report={'result':'PASS','finishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':commit,'branch':s['branch'],'repository':'https://github.com/'+s['repository'],'archive_url':'https://github.com/'+s['repository']+'/tree/'+s['branch']+'/'+s['archive_name'],'original_project_related_files_removed':len(removed),'local_archive_files_removed':len(expected['files']),'bytes_removed_from_project_scopes':bytes_removed,'temporary_verification_root_removed':True,'git_metadata_preserved_and_relocated':str(newg),'original_git_pointer_preserved':str(newcontrol/'original-gitdir-pointer.txt'),'global_pip_files_preserved':len(protected_global),'remaining_non_git_project_files':remaining,'worktree_status':status,'sparse_worktree_empty':True,'source_files_excluded_from_cleanup':'Protected Git metadata and all shared global pip cache files; the archived wheel remains globally by design.','restore_hint':'Clone the archive elsewhere, or git sparse-checkout disable to materialize this verified repository again. No deletion commit was made.'}
 s['cleanup_report']=report;s['phase']='cleaned';s['cleanup_finished']=True
 # Frozen expectation paths moved along with Git metadata.
 s['freezes']={k:str(newcontrol/Path(v).name)for k,v in s['freezes'].items()};sp.write_text(json.dumps(s,indent=2)+'\n')
 (newcontrol/'FINAL_REPORT.txt').write_text(json.dumps(report,indent=2)+'\n\nFIRST AND SECOND VERIFICATION\n'+json.dumps(s['verifications'][label],indent=2)+'\n')
 print(json.dumps(report,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--state',required=True,type=Path);ap.add_argument('--execute',action='store_true');a=ap.parse_args();cleanup(a.state,a.execute)
