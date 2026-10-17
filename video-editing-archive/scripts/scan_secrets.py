#!/usr/bin/env python3
"""Read-only pattern/exact-known-value scan, including ZIP/wheel member bytes.
Supply known sensitive values only through ARCHIVE_SECRET_1..3, never arguments.
Findings show paths/types only, not captured secret text.
"""
from pathlib import Path
import argparse,base64,json,os,re,urllib.parse,zipfile

PATTERNS=[('github-token',re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}')),('private-key-material',re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\r?\n(?:[A-Za-z0-9+/=]{20,}\r?\n){2,}-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'))]

def scan(root):
 root=Path(root);known=[os.environ.get('ARCHIVE_SECRET_'+str(i),'')for i in range(1,4)];known=[x for x in known if x];variants=[]
 for i,x in enumerate(known,1):
  for b in {x.encode(),base64.b64encode(x.encode()),urllib.parse.quote(x,safe='').encode()}:variants.append(('known-value-'+str(i),b))
 findings=[];files=0;members=0
 def stream_scan(stream,label):
  tail=b'';found=set()
  for b in iter(lambda:stream.read(1024*1024),b''):
   data=tail+b
   for kind,pat in PATTERNS:
    if pat.search(data):found.add(kind)
   for kind,value in variants:
    if value in data:found.add(kind)
   tail=data[-16384:]
  for kind in found:findings.append({'path':label,'type':kind})
 for p in root.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(root).as_posix();files+=1
  if p.name.startswith('.env')or p.name in['.netrc','.git-credentials','cookies.txt']:
   findings.append({'path':rel,'type':'sensitive-file-name-review-required'})
  with p.open('rb')as f:stream_scan(f,rel)
  if p.suffix.lower()in['.zip','.whl','.body']and zipfile.is_zipfile(p):
   with zipfile.ZipFile(p)as z:
    for item in z.infolist():
     if item.is_dir():continue
     members+=1
     with z.open(item)as f:stream_scan(f,rel+'!/'+item.filename)
 report={'result':'PASS'if not findings else'BLOCKED','files_scanned':files,'distribution_members_scanned':members,'known_sensitive_values_checked':len(known),'secret_values_printed_or_saved':False,'findings':findings,'note':'Pattern/exact-value scan with source review, not a mathematical guarantee no unknown secret exists.'}
 return report

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);a=ap.parse_args();r=scan(a.root);print(json.dumps(r,indent=2));raise SystemExit(r['result']!='PASS')
