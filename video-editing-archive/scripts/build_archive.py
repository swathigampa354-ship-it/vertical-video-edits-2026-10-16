#!/usr/bin/env python3
"""Build/freeze an exhaustive archive from the immutable phase-1 inventory.
All original files are read-only. Authentication is not accepted or persisted.
"""
from pathlib import Path
from collections import Counter
import argparse,datetime,hashlib,json,os,re,shutil,subprocess

SCRIPT_NAMES=['build_archive.py','verify_archive.py','restore_archive.py','run_verifications.py','cleanup_verified.py','scan_secrets.py']

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
def dump(p,data):write(p,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def load_state(path):return json.loads(path.read_text())
def md_visible(text):
 out=[];fence=None
 for line in text.splitlines():
  m=re.match(r'^\s*(`{3,}|~{3,})',line)
  if m:
   t=m[1]
   if fence is None:fence=(t[0],len(t));continue
   if t[0]==fence[0]and len(t)>=fence[1]:fence=None;continue
  if fence is None:out.append(line)
 return '\n'.join(out)
def category(rel):
 p=Path(rel);ext=p.suffix.lower();name=p.name
 if name=='SKILL.md'or ext=='.md':return'skills-and-skill-references'
 if ext in['.py','.pyc','.js','.mjs','.ts','.tsx','.sh']:return'code'
 if ext in['.mp4','.mov','.m4v','.avi','.webm']:return'videos'
 if ext in['.wav','.mp3','.ogg','.flac','.aac','.m4a']:return'audio'
 if ext in['.png','.jpg','.jpeg','.webp','.svg','.gif']:return'images-and-logos'
 if ext in['.ttf','.otf','.woff','.woff2']:return'fonts'
 if ext in['.json','.jsonl','.yaml','.yml','.toml','.ini','.cfg']or name in['.gitignore','.gitattributes','METADATA','RECORD','WHEEL','INSTALLER']or name.startswith('requirements'):return'configs-and-manifests'
 if ext in['.txt','.pdf']:return'documentation'
 return'other-assets-dependencies'

def build(sp):
 s=load_state(sp);p=Path(s['project']);a=p/s['archive_name'];control=sp.parent
 assert not a.exists(),'Refusing to overwrite an existing archive folder'
 assert all((control/x).is_file()for x in SCRIPT_NAMES),'Archive helper source missing'
 included=[x for x in s['files']if x['disposition'].startswith('include')]
 src={Path(x['absolute_source']):x for x in included};skill_roots={f.parent for f in src if f.name=='SKILL.md'}
 kept_md={}
 for f in src:
  if f.suffix.lower()not in['.md','.markdown']:continue
  parents=[r for r in skill_roots if f.is_relative_to(r)]
  if parents:
   closest=max(parents,key=lambda r:len(r.parts));rel=f.relative_to(closest)
   if '.cache'not in rel.parts:kept_md[f]='Actual agent skill file/resource under '+closest.name
 # Preserve external Markdown that is really linked by a retained skill resource.
 pending=list(kept_md);visited=set()
 while pending:
  f=pending.pop()
  if f in visited:continue
  visited.add(f)
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md_visible(f.read_text(errors='replace'))):
   if re.match(r'^[a-zA-Z][\w+.-]*:',target)or target.startswith('#'):continue
   from urllib.parse import unquote
   target=(f.parent/unquote(target.split('#',1)[0].split('?',1)[0])).resolve()
   if target in src and target.suffix.lower()in['.md','.markdown']and target not in kept_md:
    kept_md[target]='Necessary local reference linked by an actual agent skill';pending.append(target)
 a.mkdir();copies=[];targets=set()
 def cp(row,dest,role='source-mirror'):
  source=Path(row['absolute_source']);assert source.is_file()and source.stat().st_size==row['size']and sha(source)==row['sha256'],'Source changed after inventory: '+str(source)
  rel=Path(dest).as_posix();assert rel not in targets,'Archive destination collision '+rel;targets.add(rel);out=a/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,out)
  assert out.stat().st_size==row['size']and sha(out)==row['sha256']
  copies.append({'source_group':row['source_group'],'source_relative':row['relative_path'],'archive_path':rel,'size':row['size'],'sha256':row['sha256'],'mode':row['mode'],'category':category(rel),'role':role,'source_hidden':row['hidden'],'documentation_filename_only_conversion':source.suffix.lower()in['.md','.markdown']and out.suffix=='.txt','markdown_exception_reason':kept_md.get(source)if out.suffix.lower()=='.md'else None})
 for row in included:
  group=row['source_group'];rel=Path(row['relative_path']);source=Path(row['absolute_source'])
  if group=='project':dest=Path('project/workspace/video-project')/rel
  elif group=='pdf-pages':dest=Path('project/external/pdf-pages')/rel
  elif group=='uploads':dest=Path('project/external/uploads')/rel
  else:dest=Path('assets/dependencies/cache-origin/pip')/rel
  if source.suffix.lower()in['.md','.markdown']and source not in kept_md:dest=dest.with_suffix('.txt')
  cp(row,dest)
 tracked={x['path']for x in s['original_remote_files']}
 for row in included:
  rel=row['relative_path']
  if row['source_group']=='project'and rel.startswith('video-editing-skill/')and rel in tracked:
   cp(row,Path('skills/video-editing-skill')/Path(rel).relative_to('video-editing-skill'),'standalone-canonical-skill')
 wheel_row=next(x for x in included if x['absolute_source']==s['wheel']['source'])
 cp(wheel_row,Path('assets/dependencies')/s['wheel']['filename'],'installable-wheel-alias')
 for name in SCRIPT_NAMES:shutil.copyfile(control/name,a/'scripts'/name)if(a/'scripts').exists()else(write(a/'scripts'/name,(control/name).read_text()))
 for f in(a/'scripts').glob('*.py'):f.chmod(0o755)
 public_inventory=[]
 for row in s['files']:public_inventory.append({k:v for k,v in row.items()if k!='absolute_source'})
 dump(a/'configs/source-inventory.json',{'capturedAtUtc':s['createdAtUtc'],'rows':public_inventory,'note':'Pre-task source inventory, including protected metadata/shared-cache rows. Actual copy coverage is source-map.json, not a claim every inventory row was uploaded.'})
 dump(a/'configs/source-map.json',{'original_source_files_included':len(included),'copies':copies,'note':'Each copy contains actual original bytes. Ordinary documentation renames only its extension; restore_archive.py reverses names/layout. Canonical skill and wheel aliases are intentional duplicate paths, not missing originals.'})
 allowed=sorted(x['archive_path']for x in copies if Path(x['archive_path']).suffix.lower()=='.md')
 dump(a/'configs/layout.json',{'allowed_markdown':allowed,'exception_rule':'Only actual SKILL.md and its necessary local skill resources/references. New general documentation is TXT/PDF. Original immutable wheel/ZIP internals retain their functional formats.','ordinary_markdown_conversions':[{'source_group':x['source_group'],'source':x['source_relative'],'archive':x['archive_path']}for x in copies if x['documentation_filename_only_conversion']]})
 protected=[x for x in s['files']if x['disposition']=='protected']
 txt=['PROTECTED / EXCLUDED FROM PAYLOAD\n\n','No required ordinary project file was omitted.\n','Protected Git metadata is retained locally and its published commit history remains in the same repository; do not recursively embed .git or publish credentials.\n','Eight shared global pip metadata/cache files are retained without publishing HTTP metadata. The identified imageio-ffmpeg wheel is included in full and also retained globally.\n\n']
 for x in protected:txt.append(f"{x['source_group']}/{x['relative_path']}\t{x['size']} bytes\t{x['reason']}\n")
 write(a/'documentation/exclusions.txt',''.join(txt))
 write(a/'documentation/project-context.txt',f'''COMPLETE VIDEO-EDITING PROJECT ARCHIVE\n\nExisting repository: {s['remote_url']}\nDestination branch: {s['branch']}\nStarting commit: {s['initial_commit']}\n\nThe project produced three separate 9:16,1080x1920 source-speech edits and a reusable editing skill. V1 sports, V2 orange/black/cream editorial, V3 cobalt/off-white continuous UI morph. Source is640x360; V1/V2 30fps, V3 60fps graphics. Do not claim native1080p source detail.\n\nAll available project source, raw/reference footage, final movies, intermediate renders/WAVs, original PDF/page images, complete skills, fonts/licences, test/draft caches and the actual installed FFmpeg dependency are preserved. Failed/draft test artifacts remain evidence, not necessarily valid production plans.\n\nThe most accessible production entry is skills/video-editing-skill/SKILL.md. Its references/scripts/fonts/examples are present; no previous chat/agent ID is required. The full original tree is mirrored under project/workspace/video-project/. Recover original documentation names with restore_archive.py when an exact workspace is desired.\n\nShared Python/system packages are not project-owned files. Their observed versions/requirements are preserved; a compatible Python/runtime still needs those normal dependencies. The installed imageio-ffmpeg tree, binary and exact wheel are included. No credential is required to render supplied local media.\n''')
 write(a/'documentation/workflow.txt','''RECOVER AND USE\n\n1. Clone the same public GitHub repository and locate video-editing-archive/.\n2. Run: python scripts/verify_archive.py --root /path/to/video-editing-archive\n3. Read skills/video-editing-skill/SKILL.md and its bundled references. Supply NEW raw footage; do not blindly reuse old timestamps/coordinates.\n4. Use the documented inspect/transcribe/plan/stills/render/QC/review workflow. No logo is invented; original edits had no added brand logo.\n5. For an exact original workspace layout: python scripts/restore_archive.py --root /path/to/archive --destination /new/empty/restore\n   Original filenames/document extensions are restored under workspace/video-project, external PDF/page-image directories and dependency-cache. No original absolute path/global cache is overwritten.\n6. The same-source regressions, portrait adaptation and actual test evidence are preserved. No universal creative-quality, multilingual/HDR/VFR/tracked-logo or second-model guarantee is inferred from those tests.\n\nDEPENDENCIES\nThe exact FFmpeg wheel is under assets/dependencies. The installed package/binary is also preserved inside the mirrored project runtime cache. Use its PYTHONPATH/binary from the new archive location or install the archived wheel into an isolated environment. Other direct requirements and observed versions are inside the skill.\n''')
 write(a/'documentation/storage-policy.txt','''STORAGE AND FORMAT\n\nOfficial policy checked: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github\nOrdinary Git warns above50MiB and blocks above100MiB. Largest payload file is79,826,272 bytes (~76.13MiB), so no file requires LFS. Git LFS is not installed; no pointer substitution is used. All movies and runtime binaries are actual Git objects. Push/archive limits and repository policy are checked before publication.\n\nNew documentation is TXT (and original PDFs). Original Markdown is retained only where required by real agent skills/reference relationships, explicitly enumerated in configs/layout.json. Other Markdown documentation is copied byte-for-byte under a .txt filename. Source/config/media formats and functional package metadata/licences are not renamed. Original immutable portable-skill ZIPs and the dependency wheel keep their internal files/checksums.\n\nThe full mirror preserves nested/hidden/generated files; Git ignore rules do not remove them from this archive. Protected .git data and shared global caches are not project payload and are explicitly listed rather than silently omitted. Source-mirror and canonical-skill/wheel alias duplicates are intentional.\n''')
 write(a/'documentation/verification-report.txt','PRE-PUBLICATION RECORD\nCopies checked against original source hashes. Remote publication and the two independent verification gates have not yet been claimed. Actual receipts will be recorded after observation.\n')
 write(a/'.gitattributes','''# Byte-exact archival objects: no line-ending conversions or LFS filters.\n* -text -filter\n# Immutable source copies retain original whitespace; new docs/scripts still checked.\nproject/** -whitespace\nskills/** -whitespace\nassets/** -whitespace\n''')
 write(a/'documentation/file-inventory.txt','\n'.join(['SOURCE INVENTORY (pre-task originals; copied status is explicit in source-map.json)','group/path\ttype\tsize\tsha256\tdisposition']+[f"{x['source_group']}/{x['relative_path']}\t{x['file_type']}\t{x['size']}\t{x['sha256']}\t{x['disposition']}"for x in s['files']])+'\n')
 s['archive_root']=str(a);s['source_payload_count']=len(included);s['source_copy_count']=len(copies);s['phase']='copied';dump(sp,s)
 print('ARCHIVE_COPY_COMPLETE',len(included),'original files;',len(copies),'actual copy destinations;',len(allowed),'skill Markdown exceptions;',sum(x['documentation_filename_only_conversion']for x in copies),'ordinary Markdown conversions.')

def freeze(sp,label):
 s=load_state(sp);a=Path(s['archive_root']);assert a.is_dir()
 # Index lists itself and the hash manifest, but no self-referential checksum is promised.
 write(a/'ARCHIVE_INDEX.txt','Archive index being generated.\n');write(a/'SHA256SUMS.txt','Manifest being generated.\n')
 paths=sorted(p.relative_to(a).as_posix()for p in a.rglob('*')if p.is_file())
 mapping=json.loads((a/'configs/source-map.json').read_text());bycat=Counter(category(x)for x in paths)
 text=[f"VIDEO EDITING ARCHIVE\nRepository: https://github.com/{s['repository']}\nFolder: {s['archive_name']}\nBranch: {s['branch']}\n\nOriginal included source files: {s['source_payload_count']}\nActual source-copy paths (including canonical aliases): {s['source_copy_count']}\nArchive files: {len(paths)}\n\nCATEGORIES\n"]
 text +=[f'{k}: {v}\n'for k,v in sorted(bycat.items())]
 text +=['\nENTRY POINTS\nskills/video-editing-skill/SKILL.md (standalone production skill)\nproject/workspace/video-project/ (complete mirrored project including hidden/generated data)\nassets/dependencies/ (exact wheel and preserved cache-origin bytes)\ndocumentation/ (TXT reports)\nconfigs/source-map.json (actual copied bytes/provenance)\nscripts/verify_archive.py and scripts/restore_archive.py\n\nCHECKSUMS\nSHA256SUMS.txt covers every archive file except itself. Git commit identity and independent frozen expectations additionally bind that manifest.\n\nALL ARCHIVED FILES\n']
 text +=[x+'\n'for x in paths];write(a/'ARCHIVE_INDEX.txt',''.join(text))
 lines=[]
 for rel in paths:
  if rel!='SHA256SUMS.txt':lines.append(sha(a/rel)+'  '+rel+'\n')
 write(a/'SHA256SUMS.txt',''.join(lines))
 expected={'label':label,'files':{rel:{'size':(a/rel).stat().st_size,'sha256':sha(a/rel),'mode':oct((a/rel).stat().st_mode&0o777)}for rel in paths},'counts_by_category':dict(bycat),'source_files':s['source_payload_count'],'copy_paths':s['source_copy_count'],'largest':max(({'path':rel,'size':(a/rel).stat().st_size}for rel in paths),key=lambda x:x['size'])}
 dump(sp.parent/('frozen-'+label+'.json'),expected);s.setdefault('freezes',{})[label]=str(sp.parent/('frozen-'+label+'.json'));s['final_label']=label;s['phase']='frozen';dump(sp,s)
 print('FROZEN',label,len(paths),'archive files',sum(x['size']for x in expected['files'].values()),'bytes; largest',expected['largest'])

def receipts(sp):
 s=load_state(sp);label=s['final_label'];v=s['verifications'][label];assert v['http']['result']=='PASS'and v['fresh']['result']=='PASS'
 a=Path(s['archive_root']);commit=v['commit'];report=['INDEPENDENT VERIFICATION RECEIPTS\n\n',f"Verified archive commit: {commit}\n",f"Source files included: {s['source_payload_count']}\nActual copied source paths: {s['source_copy_count']}\n",'\nFIRST VERIFICATION — public GitHub tree and HTTPS codeload bytes, not local status\n',json.dumps(v['http'],indent=2),'\n\nSECOND VERIFICATION — new remote clone/checkout, hashes, restoration and standalone render\n',json.dumps(v['fresh'],indent=2),'\n\nThis report records two already observed verifications of the complete source archive. A receipt-only follow-up commit updates this file/checksum manifest, then both independent checks are repeated on that final commit before cleanup. The final verification/cleanup audit is kept in protected local Git metadata and the final response, avoiding a self-referential commit-hash claim inside its own bytes.\n']
 write(a/'documentation/verification-report.txt',''.join(report));print('Observed receipts recorded; freeze/push and repeat both gates before deletion.')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','freeze','receipts']);ap.add_argument('--state',required=True,type=Path);ap.add_argument('--label',default='initial');x=ap.parse_args()
 if x.action=='build':build(x.state)
 elif x.action=='freeze':freeze(x.state,x.label)
 else:receipts(x.state)
