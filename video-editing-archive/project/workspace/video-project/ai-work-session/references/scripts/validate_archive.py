#!/usr/bin/env python3
"""Validate this archive without running media generation or installing packages.

Optional exact-secret values must be supplied transiently through
SESSION_ARCHIVE_SECRET_1..3. Values are never printed or saved.
"""
from pathlib import Path
import argparse, ast, base64, datetime, hashlib, json, os, re, subprocess, sys
from urllib.parse import unquote, quote
import yaml

A=Path(__file__).resolve().parents[2]
P=A.parent
REQUIRED=['SKILL.md','SESSION_ARCHIVE.md','PROJECT_CONTEXT.md','DECISION_LOG.md','COMMANDS_AND_TOOLS.md','ERRORS_AND_SOLUTIONS.md','FILE_CHANGE_LOG.md','VERIFICATION_REPORT.md','CONTINUE.md','references/requirements.md','references/technical_details.md','references/troubleshooting.md','references/session_index.md']
EXPECTED_REMOTE='https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16.git'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args):
 r=subprocess.run(['git','-C',str(P),*args],capture_output=True,text=True)
 if r.returncode:raise RuntimeError('Git command failed: '+' '.join(args)+'; '+r.stderr.strip())
 return r.stdout

def visible_markdown(text):
 result=[];fence=None
 for line in text.splitlines():
  m=re.match(r'^\s*(`{3,}|~{3,})',line)
  if m:
   mark=m.group(1)
   if fence is None:fence=(mark[0],len(mark));continue
   if mark[0]==fence[0]and len(mark)>=fence[1]:fence=None;continue
  if fence is None:result.append(line)
 return '\n'.join(result)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--check-original-workspace',action='store_true');ap.add_argument('--require-staged-scope',action='store_true');ap.add_argument('--expect-staged',action='store_true');ap.add_argument('--no-write-report',action='store_true');args=ap.parse_args()
 errors=[];checks={};files=sorted(p for p in A.rglob('*')if p.is_file()and'__pycache__'not in p.parts)
 missing=[s for s in REQUIRED if not(A/s).is_file()]
 checks['requiredFiles']={'expected':len(REQUIRED),'missing':missing}
 if missing:errors.append('Missing required files: '+', '.join(missing))
 s=(A/'SKILL.md').read_text()if(A/'SKILL.md').exists()else''
 try:
  if not s.startswith('---\n'):raise ValueError('Missing YAML frontmatter')
  front=s.split('---\n',2)[1];meta=yaml.safe_load(front)
  if not isinstance(meta,dict):raise ValueError('Frontmatter is not a mapping')
  name=meta.get('name','');description=meta.get('description','')
  if not isinstance(name,str)or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name)or not 1<=len(name)<=64 or name!=A.name:raise ValueError('Invalid name/directory match')
  if not isinstance(description,str)or not 1<=len(description)<=1024:raise ValueError('Invalid description')
  if 'compatibility'in meta and(not isinstance(meta['compatibility'],str)or not 1<=len(meta['compatibility'])<=500):raise ValueError('Invalid compatibility field')
  if 'metadata'in meta and(not isinstance(meta['metadata'],dict)or any(not isinstance(k,str)or not isinstance(v,str)for k,v in meta['metadata'].items())):raise ValueError('Metadata must map strings to strings')
  if len(s.splitlines())>=500:raise ValueError('Main skill exceeds recommended 500 lines')
  checks['skill']={'format':'Agent Skills YAML + Markdown','name':name,'lines':len(s.splitlines()),'valid':True,'nativeClientRegistrationTested':False}
 except Exception as e:errors.append('SKILL.md: '+str(e));checks['skill']={'valid':False}
 links=0;bad=[]
 for p in files:
  if p.suffix.lower()!='.md':continue
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',visible_markdown(p.read_text(errors='replace'))):
   target=target.strip().split(' "',1)[0].strip('<>')
   if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target)or target.startswith('#'):continue
   path=unquote(target.split('#',1)[0].split('?',1)[0])
   if not path:continue
   links+=1;dest=(p.parent/path).resolve()
   if not dest.exists():bad.append({'file':str(p.relative_to(A)),'target':target})
 checks['localLinks']={'checked':links,'broken':bad,'externalUrls':'Not exhaustively fetched; historical/fresh HTTP evidence recorded separately.'}
 if bad:errors.append('Broken local Markdown links')
 syntax=[]
 for p in files:
  if p.suffix=='.py':
   try:ast.parse(p.read_text(),filename=str(p));syntax.append(str(p.relative_to(A)))
   except SyntaxError as e:errors.append('Python syntax: '+str(p.relative_to(A))+': '+str(e))
 checks['pythonAst']={'checked':len(syntax),'files':syntax,'executesCode':False}
 json_count=0
 for p in files:
  if p.suffix=='.json':
   try:json.loads(p.read_text());json_count+=1
   except Exception as e:errors.append('Invalid JSON '+str(p.relative_to(A))+': '+type(e).__name__)
 checks['json']={'parsed':json_count}
 provenance=json.loads((A/'references/evidence/copied-artifact-provenance.json').read_text())
 bad_copies=[]
 for item in provenance['copies']:
  p=A/item['archived']
  if not p.exists()or p.stat().st_size!=item['bytes']or sha(p)!=item['sha256']:bad_copies.append(item['archived'])
 checks['exactCopies']={'checked':len(provenance['copies']),'mismatches':bad_copies}
 if bad_copies:errors.append('Copied artifact hash mismatch')
 inventory=json.loads((A/'references/evidence/initial-workspace-inventory.json').read_text())['files']
 if args.check_original_workspace:
  changed=[];missing_old=[]
  for item in inventory:
   p=P/item['path']
   if not p.exists():missing_old.append(item['path'])
   elif sha(p)!=item['sha256']:changed.append(item['path'])
  checks['originalWorkspace']={'checked':len(inventory),'changed':changed,'missing':missing_old,'strict':True}
  if changed or missing_old:errors.append('Original workspace files changed/missing')
 else:checks['originalWorkspace']={'strict':False,'note':'Use --check-original-workspace in the original workspace; a fresh clone legitimately lacks formerly untracked originals.'}
 secret_values=[os.environ.get('SESSION_ARCHIVE_SECRET_'+str(i),'')for i in range(1,4)]
 secret_values=[v for v in secret_values if v]
 patterns=[('github-token',re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}')),('private-key',re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'))]
 findings=[]
 for p in files:
  if p.is_symlink():errors.append('Symlink in archive: '+str(p.relative_to(A)));continue
  data=p.read_bytes()
  for label,pat in patterns:
   if pat.search(data):findings.append({'file':str(p.relative_to(A)),'type':label})
  for i,v in enumerate(secret_values,1):
   variants={v.encode(),base64.b64encode(v.encode()),quote(v,safe='').encode()}
   if any(x in data for x in variants):findings.append({'file':str(p.relative_to(A)),'type':'known-credential-'+str(i)})
 checks['secretScan']={'filesScanned':len(files),'knownValuesChecked':len(secret_values),'findings':findings,'valuesLogged':False}
 if findings:errors.append('Potential secrets detected; do not commit/push')
 try:
  remotes=run('remote','get-url','origin').strip();branch=run('branch','--show-current').strip();head=run('rev-parse','HEAD').strip()
  staged=[x for x in run('diff','--cached','--name-only','-z').split('\0')if x]
  outside=[x for x in staged if not x.startswith('ai-work-session/')]
  mismatch=[]
  index={}
  for entry in run('ls-files','--stage','-z','--','ai-work-session').split('\0'):
   if entry:
    fields,path=entry.split('\t',1);index[path]=fields.split()[1]
  for path in staged:
   p=P/path
   if not p.is_file():mismatch.append(path);continue
   data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
   if index.get(path)!=blob:mismatch.append(path)
  checks['git']={'origin':remotes,'branch':branch,'headAtCheck':head,'stagedPathCount':len(staged),'stagedOutsideArchive':outside,'stagedContentDiffersFromWorkingTree':mismatch}
  if args.require_staged_scope and mismatch:errors.append('Staged bytes differ from validated working files')
  if remotes!=EXPECTED_REMOTE:errors.append('Unexpected origin remote')
  if branch!='main':errors.append('Unexpected destination branch')
  if args.require_staged_scope and outside:errors.append('Staged paths outside archive')
  if args.expect_staged and not staged:errors.append('Expected staged archive files')
 except Exception as e:errors.append(str(e))
 report={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'PASS'if not errors else'FAIL','archiveFileCount':len(files),'checks':checks,'errors':errors,'scope':'Archive validation only; not a render, Flick benchmark, native skill-host activation test, or guarantee no unknown secret exists.'}
 if not args.no_write_report:(A/'references/evidence/archive-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 raise SystemExit(0 if not errors else 1)
