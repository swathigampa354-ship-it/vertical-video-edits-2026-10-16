#!/usr/bin/env python3
"""Two distinct remote verification methods. Never deletes project/temporary files."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,subprocess,sys,uuid,zipfile
import requests

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(sp):return json.loads(sp.read_text())
def save(sp,s):sp.write_text(json.dumps(s,indent=2)+'\n')
def temporary(sp,s):
 if 'temp_root'not in s:
  token=hashlib.sha256((s['createdAtUtc']+s['project']).encode()).hexdigest()[:14];root=Path('/home/user/.cache')/('video-editing-archive-'+token)
  assert not root.exists(),'Temporary location unexpectedly exists';root.mkdir();(root/'TASK_OWNER.json').write_text(json.dumps({'createdAtUtc':s['createdAtUtc'],'project':s['project']}));s['temp_root']=str(root);save(sp,s)
 else:
  root=Path(s['temp_root']);owner=json.loads((root/'TASK_OWNER.json').read_text());assert owner['createdAtUtc']==s['createdAtUtc']and owner['project']==s['project']
 return root

def command(args,cwd=None,env=None):
 r=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True)
 if r.returncode:raise RuntimeError('Command failed: '+str(args[:3])+'\n'+r.stderr[-3000:]+'\n'+r.stdout[-1500:])
 return r.stdout

def first(sp,label,commit):
 s=load(sp);frozen=json.loads(Path(s['freezes'][label]).read_text());repo=s['repository'];prefix=s['archive_name']+'/';session=requests.Session();session.headers['Accept']='application/vnd.github+json';api='https://api.github.com/repos/'+repo
 def get(path):
  r=session.get(api+path,timeout=40);r.raise_for_status();return r.json()
 info=get('');assert not info['private'];tip=get('/commits/'+s['branch']);assert tip['sha']==commit,'Remote branch tip differs; do not clean'
 tree=get('/git/trees/'+tip['commit']['tree']['sha']+'?recursive=1');assert not tree.get('truncated')
 remote={x['path'][len(prefix):]:x for x in tree['tree']if x['type']=='blob'and x['path'].startswith(prefix)}
 assert set(remote)==set(frozen['files']),'Remote tree file paths/count differ'
 for rel,x in frozen['files'].items():
  assert remote[rel]['size']==x['size'],rel
  assert remote[rel]['mode']==('100755'if int(x['mode'],8)&0o111 else'100644'),rel
 # Verify earlier remote work was not overwritten by the archive commit.
 allremote={x['path']:x for x in tree['tree']if x['type']=='blob'}
 for old in s['original_remote_files']:assert allremote[old['path']]['sha']==old['sha']and allremote[old['path']]['mode']==old['mode']
 temp=temporary(sp,s)
 target=temp/('http-'+label+'-'+uuid.uuid4().hex[:10]+'.zip');url='https://codeload.github.com/'+repo+'/zip/'+commit
 response=session.get(url,stream=True,timeout=(20,180));response.raise_for_status();downloaded=0
 with target.open('xb')as out:
  for chunk in response.iter_content(1024*1024):
   if chunk:out.write(chunk);downloaded+=len(chunk)
 print('HTTPS archive downloaded',downloaded,'bytes',flush=True)
 total=0;video_paths=[];empty=[];lfs=[]
 with zipfile.ZipFile(target)as z:
  roots={n.split('/',1)[0]for n in z.namelist()};assert len(roots)==1;zprefix=next(iter(roots))+'/'+prefix
  names={n[len(zprefix):]:n for n in z.namelist()if n.startswith(zprefix)and not n.endswith('/')}
  assert set(names)==set(frozen['files']),'HTTPS archive members missing/extra'
  for rel,x in frozen['files'].items():
   info=z.getinfo(names[rel]);assert info.file_size==x['size'];h=hashlib.sha256();head=b''
   with z.open(info)as stream:
    for data in iter(lambda:stream.read(1024*1024),b''):
     if len(head)<128:head=(head+data)[:128]
     h.update(data)
   assert h.hexdigest()==x['sha256'],'Remote byte checksum '+rel;total+=x['size']
   if head.startswith(b'version https://git-lfs.github.com/spec/v1'):lfs.append(rel)
   if rel.lower().endswith(('.mp4','.mov','.m4v','.avi','.webm')):
    if rel.lower().endswith(('.mp4','.mov','.m4v')):assert head[4:8]==b'ftyp',rel
    video_paths.append(rel)
   if x['size']==0:empty.append(rel)
  layout=json.loads(z.read(names['configs/layout.json']));md={n for n in names if n.lower().endswith(('.md','.markdown'))};assert md==set(layout['allowed_markdown'])
  mapping=json.loads(z.read(names['configs/source-map.json']));intentional={x['archive_path']for x in mapping['copies']if x['size']==0};assert all(x in intentional for x in empty)
 assert not lfs,'Actual LFS object retrieval required; pointer alone not acceptable'
 result={'result':'PASS','verifiedAtUtc':now(),'commit':commit,'method':'Unauthenticated GitHub API tree plus independently downloaded pinned HTTPS codeload ZIP; all decompressed file bytes hashed.','archive_files':len(remote),'file_sizes_and_sha256_all_match':True,'bytes_verified':total,'videos_retrieved_in_full':len(video_paths),'lfs_pointers':lfs,'markdown_exception_count':len(md),'documentation_policy_pass':True,'intentional_empty_files':len(empty),'old_remote_files_preserved':len(s['original_remote_files']),'download_http_status':response.status_code,'source_payload_files':s['source_payload_count']}
 s.setdefault('verifications',{}).setdefault(label,{}) .update({'commit':commit,'http':result,'http_zip':str(target)})
 s['final_label']=label;s['final_commit']=commit;s.setdefault('task_temp_paths',[]).append(str(target));s['phase']='first-verified';save(sp,s)
 (sp.parent/'verification-report.txt').write_text('FIRST REMOTE VERIFICATION PASSED\n'+json.dumps(result,indent=2)+'\nSECOND CHECK NOT YET CLAIMED FOR THIS COMMIT.\n')
 print(json.dumps(result,indent=2))

def second(sp,label,commit):
 s=load(sp);v=s['verifications'][label];assert v['commit']==commit and v['http']['result']=='PASS'
 p=Path(s['project']);command(['git','fetch','origin',s['branch']],cwd=p);assert command(['git','rev-parse','refs/remotes/origin/'+s['branch']],cwd=p).strip()==commit
 temp=temporary(sp,s);clone=temp/('fresh-'+label+'-'+uuid.uuid4().hex[:10]);assert not clone.exists()
 command(['git','clone','--no-checkout','--single-branch','--branch',s['branch'],s['remote_url'],str(clone)])
 command(['git','-C',str(clone),'checkout','--detach',commit]);assert command(['git','-C',str(clone),'rev-parse','HEAD']).strip()==commit
 root=clone/s['archive_name'];env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
 for key in list(env):
  if key in['GITHUB_TOKEN','GH_TOKEN','ARCHIVE_GITHUB_TOKEN','SKILL_GITHUB_TOKEN']or key.startswith(('ARCHIVE_SECRET_','SKILL_SECRET_')):env.pop(key,None)
 verified=json.loads(command([sys.executable,str(root/'scripts/verify_archive.py'),'--root',str(root),'--expected',s['freezes'][label]],env=env))
 # Prove original names can be reconstructed, including docs renamed only for archive policy.
 restored=temp/('restored-'+label+'-'+uuid.uuid4().hex[:10]);restore_result=json.loads(command([sys.executable,str(root/'scripts/restore_archive.py'),'--root',str(root),'--destination',str(restored)],env=env))
 assert restore_result['restored_original_files']==s['source_payload_count']
 skill=root/'skills/video-editing-skill';mirror=root/'project/workspace/video-project';deps=mirror/'video-editing-skill/.cache/pydeps';binary=deps/'imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
 assert binary.is_file()and os.access(binary,os.X_OK),'Archived FFmpeg executable/mode missing'
 env['PYTHONPATH']=str(deps);env['FFMPEG_BIN']=str(binary)
 skill_result=json.loads(command([sys.executable,str(skill/'scripts/validate_package.py'),'--verify-zip'],cwd=temp,env=env));assert skill_result['result']=='PASS'
 job=temp/('standalone-'+label+'-'+uuid.uuid4().hex[:10]);raw=skill/'examples/portrait/source.mp4';plan=skill/'examples/portrait/plan.json'
 command([sys.executable,str(skill/'scripts/edit.py'),'validate-plan','--input',str(raw),'--plan',str(plan),'--workdir',str(job)],cwd=temp,env=env)
 command([sys.executable,str(skill/'scripts/edit.py'),'render','--input',str(raw),'--plan',str(plan),'--workdir',str(job)],cwd=temp,env=env)
 command([sys.executable,str(skill/'scripts/edit.py'),'qc','--workdir',str(job)],cwd=temp,env=env);qc=json.loads((job/'qc.json').read_text());assert qc['machinePass']
 # All distinct stored MP4 bodies are decoded; duplicates have already passed per-path SHA checks.
 video_decode=[];seen=set();frozen=json.loads(Path(s['freezes'][label]).read_text())
 for rel,x in frozen['files'].items():
  if not rel.lower().endswith(('.mp4','.mov','.m4v','.avi','.webm'))or x['sha256']in seen:continue
  seen.add(x['sha256']);r=subprocess.run([str(binary),'-v','error','-i',str(root/rel),'-map','0:v:0','-an','-vf','setpts=N/(FRAME_RATE*TB)','-fps_mode','passthrough','-f','null','-'],capture_output=True,text=True)
  video_decode.append({'path':rel,'sha256':x['sha256'],'exit_code':r.returncode,'error_output':r.stderr[:500]})
 assert all(x['exit_code']==0 and not x['error_output']for x in video_decode),'A stored video did not fully decode; inspect original status before cleanup'
 # Post-test hashes: bytecode creation and job output are outside the archive, so no source is modified.
 verified_after=json.loads(command([sys.executable,str(root/'scripts/verify_archive.py'),'--root',str(root),'--expected',s['freezes'][label]],env=env));assert verified_after['result']=='PASS'
 result={'result':'PASS','verifiedAtUtc':now(),'commit':commit,'method':'Fresh public Git clone and pinned checkout, independent of HTTPS ZIP verification; full original expected path/size/SHA/mode comparison.','archive_files':verified['archive_files'],'source_files_restored_byte_exact':restore_result['restored_original_files'],'source_copy_paths':verified['source_copies_checked'],'all_sha256_and_modes_match':True,'skill_entries_checked':len(verified['skill_entries']),'local_skill_links_checked':verified['local_skill_links_checked'],'documentation_policy_pass':True,'lfs_pointers':verified['lfs_pointers'],'video_paths_retrieved':verified['video_path_count'],'unique_videos_fully_decoded':len(video_decode),'all_video_decodes_pass':True,'video_decode_method':'Complete video decode with passthrough frames and monotonic frame-counter timestamps on a discarded verification sink only; source bytes/timestamps unchanged.','timestamp_advisory':'Original and identical archived style-reference-v2 both triggered a null-muxer DTS diagnostic; this content-decoding check does not certify original presentation timestamps.','canonical_skill_validation':skill_result['result'],'standalone_render':{'machinePass':qc['machinePass'],'frames':qc['decodedFrames'],'size':[qc['width'],qc['height']],'voice_lag_ms':[x['lag_ms']for x in qc['sourceLagWindows']]},'archive_unchanged_after_tests':True,'independence_note':'Code/media/fonts/transcript/FFmpeg were read from the fresh remote archive; normal host Python scientific packages were used as declared dependencies. No original-workspace project file was needed.'}
 s=load(sp);s['verifications'][label].update({'fresh':result,'fresh_checkout':str(clone),'restored_tree':str(restored),'standalone_job':str(job)});s.setdefault('task_temp_paths',[]).extend([str(clone),str(restored),str(job)]);s['phase']='twice-verified';save(sp,s)
 (sp.parent/'verification-report.txt').write_text('BOTH INDEPENDENT VERIFICATIONS PASSED\nFIRST\n'+json.dumps(s['verifications'][label]['http'],indent=2)+'\nSECOND\n'+json.dumps(result,indent=2)+'\nCleanup has not yet been performed.\n')
 (sp.parent/('video-decodes-'+label+'.json')).write_text(json.dumps(video_decode,indent=2)+'\n')
 print(json.dumps(result,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['http','fresh']);ap.add_argument('--state',required=True,type=Path);ap.add_argument('--label',required=True);ap.add_argument('--commit',required=True);a=ap.parse_args()
 if a.action=='http':first(a.state,a.label,a.commit)
 else:second(a.state,a.label,a.commit)
