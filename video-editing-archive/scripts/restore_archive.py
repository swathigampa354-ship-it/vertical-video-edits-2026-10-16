#!/usr/bin/env python3
"""Restore byte-exact original filenames/layouts into a NEW chosen directory.
Does not write to original absolute paths, credentials, or a real global cache.
"""
from pathlib import Path
import argparse,json,shutil,hashlib

def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def restore(root,dest):
 root=Path(root).resolve();dest=Path(dest).resolve()
 if dest.exists():raise FileExistsError('Restore destination must be new; no overwriting existing user work.')
 mapping=json.loads((root/'configs/source-map.json').read_text());dest.mkdir(parents=True);seen=set();count=0
 prefixes={'project':'workspace/video-project','pdf-pages':'external/pdf-pages','uploads':'external/uploads','global-pip-cache':'dependency-cache/pip'}
 for x in mapping['copies']:
  key=(x['source_group'],x['source_relative'])
  if key in seen:continue
  seen.add(key);rel=Path(prefixes[x['source_group']])/x['source_relative'];assert not rel.is_absolute()and'..'not in rel.parts
  source=root/x['archive_path'];target=dest/rel
  assert digest(source)==x['sha256'],'Archive source changed'
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(int(x['mode'],8))
  assert target.stat().st_size==x['size']and digest(target)==x['sha256'];count+=1
 return {'result':'PASS','restored_original_files':count,'destination':'new caller-selected directory','original_filenames_restored':True,'git_metadata_restored':False,'note':'Protected repository metadata/credentials were intentionally never embedded. Documentation filename conversions are reversed without changing original bytes.'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--destination',required=True,type=Path);a=ap.parse_args();print(json.dumps(restore(a.root,a.destination),indent=2))
