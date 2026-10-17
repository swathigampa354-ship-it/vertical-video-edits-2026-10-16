#!/usr/bin/env python3
"""Build one deterministic transfer ZIP; exclude runtime/cache/secrets and itself."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'portable-skill.zip','BUILD_MANIFEST.json','tests/evidence/initial-state.json','tests/evidence/package-validation.json','tests/evidence/delivery.json'}
def include(p):
 rel=p.relative_to(ROOT).as_posix()
 return p.is_file()and rel not in EXCLUDE and not any(x in p.relative_to(ROOT).parts for x in['.cache','.venv','__pycache__'])and not p.name.endswith('.pyc')and not p.name.startswith('.env')
files=sorted(p for p in ROOT.rglob('*')if include(p))
manifest={'package':'video-editing-skill','version':'1.0','note':'Hashes cover distribution members except this manifest; ZIP does not contain itself. Host setup/dependencies are not bundled. Project-only initial-state/delivery/validator reports are excluded.','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files]}
(ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(ROOT/'BUILD_MANIFEST.json')
with zipfile.ZipFile(ROOT/'portable-skill.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files:
  info=zipfile.ZipInfo('video-editing-skill/'+p.relative_to(ROOT).as_posix(),date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
p=ROOT/'portable-skill.zip';print('BUNDLE_CREATED',len(files),'members',p.stat().st_size,'bytes','sha256',hashlib.sha256(p.read_bytes()).hexdigest())
