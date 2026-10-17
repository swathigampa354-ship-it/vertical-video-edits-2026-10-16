#!/usr/bin/env python3
"""Read project/public GitHub evidence and copy selected non-secret artifacts.
Writes only inside ai-work-session/. Does not render, install, or authenticate.
"""
from pathlib import Path
import datetime, hashlib, importlib.metadata, json, os, platform, shutil, subprocess
import requests

ARCHIVE=Path(__file__).resolve().parents[2]
PROJECT=ARCHIVE.parent
REPO='swathigampa354-ship-it/vertical-video-edits-2026-10-16'
EVIDENCE=ARCHIVE/'references/evidence'
SNAPSHOT=ARCHIVE/'references/source-snapshot'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def copy(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 return {'original':str(source.relative_to(PROJECT))if source.is_relative_to(PROJECT)else'uploads/'+source.name,'archived':str(dest.relative_to(ARCHIVE)),'bytes':dest.stat().st_size,'sha256':sha(dest)}

if __name__=='__main__':
 if (EVIDENCE/'initial-workspace-inventory.json').exists():raise SystemExit('Initial evidence already exists; do not overwrite it. Use a dated future-session capture instead.')
 EVIDENCE.mkdir(parents=True,exist_ok=True)
 inventory=[]
 for p in sorted(PROJECT.rglob('*')):
  if p.is_file()and not p.is_relative_to(ARCHIVE)and'.git'not in p.parts and'__pycache__'not in p.parts:
   inventory.append({'path':str(p.relative_to(PROJECT)),'bytes':p.stat().st_size,'sha256':sha(p)})
 write_json(EVIDENCE/'initial-workspace-inventory.json',{'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'Snapshot restoration changes mtimes; they are not used as original creation times. This inventory excludes the new archive and Git metadata.','files':inventory})
 sess=requests.Session();sess.headers['Accept']='application/vnd.github+json'
 def get(path):
  r=sess.get('https://api.github.com/repos/'+REPO+path,timeout=25);r.raise_for_status();return r.json()
 info=get('');branch=info['default_branch'];head=get('/commits/'+branch)
 tree=get('/git/trees/'+head['commit']['tree']['sha']+'?recursive=1')
 commits=get('/commits?sha='+branch+'&per_page=100')
 clean_commits=[{'sha':c['sha'],'committedAtUtc':c['commit']['committer']['date'],'message':c['commit']['message'],'parents':[x['sha']for x in c['parents']]}for c in commits]
 state={'repository':REPO,'url':info['html_url'],'clone_url':info['clone_url'],'default_branch':branch,'private':info['private'],'visibility':info['visibility'],'head':head['sha'],'tree':head['commit']['tree']['sha'],'tracked_files':[{'path':x['path'],'sha':x['sha'],'bytes':x.get('size')}for x in tree['tree']if x['type']=='blob'],'commits':clean_commits,'initialLocalGitMetadataPresent':(PROJECT/'.git').exists(),'trackedRootGitignorePresent':any(x['path']=='.gitignore'for x in tree['tree'])}
 if any(x['path'].startswith('ai-work-session/')for x in tree['tree']):raise SystemExit('Remote archive already exists; inspect it instead of overwriting.')
 write_json(EVIDENCE/'initial-remote-state.json',state)
 versions={}
 for name in ['requests','numpy','pillow','opencv-python','imageio-ffmpeg','soundfile','scipy','faster-whisper','ctranslate2','av','pymupdf','yt-dlp','PyYAML']:
  try:versions[name]=importlib.metadata.version(name)
  except importlib.metadata.PackageNotFoundError:versions[name]=None
 env={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'cpuCount':os.cpu_count(),'packagesObservedNow':versions,'node':subprocess.check_output(['node','--version'],text=True).strip(),'git':subprocess.check_output(['git','--version'],text=True).strip(),'shellHistoryFiles':{p:Path(p).exists()for p in ['/home/user/.bash_history','/home/user/.zsh_history']},'historicalPackageVersionLockRecovered':False,'priorCacheProjectDirectoriesPresent':[str(p)for p in Path('/home/user/.cache').glob('video-project*')]if Path('/home/user/.cache').exists()else[]}
 write_json(EVIDENCE/'environment-observed-now.json',env)
 copies=[]
 for p in sorted((PROJECT/'source').glob('*.py')):copies.append(copy(p,SNAPSHOT/'source'/p.name))
 for p in sorted((PROJECT/'assets/fonts').glob('*')):
  if p.is_file():copies.append(copy(p,SNAPSHOT/'assets/fonts'/p.name))
 for rel in ['assets/raw.mp4','analysis/transcript.json','analysis/raw-audio.wav','edits/voice-agents-9x16/captions.srt']:
  copies.append(copy(PROJECT/rel,SNAPSHOT/rel))
 for p in sorted((PROJECT/'analysis').iterdir()):
  if p.is_file()and p.suffix.lower()in['.json','.md','.txt']:
   copies.append(copy(p,EVIDENCE/'analysis'/p.name))
 for name in ['raw-contact.jpg','style-reference-contact.jpg','reference-v2-contact.jpg','design-contact.jpg','editorial-v2-contact.jpg','catalog-one-shape-contact.jpg','morph-v3-contact.jpg']:
  copies.append(copy(PROJECT/'analysis'/name,EVIDENCE/'visual-checks'/name))
 copies.append(copy(PROJECT/'README.md',EVIDENCE/'project-readme.before-archive.txt'))
 for p in sorted(Path('/home/user/uploads').glob('*.pdf')):
  copies.append(copy(p,ARCHIVE/'references/inputs/original-brief.pdf'))
 write_json(EVIDENCE/'copied-artifact-provenance.json',{'copies':copies,'omissions':'Final media already live in existing edits/ folders and are linked rather than duplicated. Full third-party reference videos and derived WAV/visual-render intermediates are inventoried but not republished. Original brief, raw input, source code, fonts, transcript and representative visual checks are retained.'})
 print('Captured',len(inventory),'pre-existing project files;',len(state['tracked_files']),'remote files;',len(clean_commits),'prior commits;',len(copies),'artifact copies.')
 print('Remote baseline:',state['head'],'branch',branch,'visibility',state['visibility'])
