#!/usr/bin/env python3
"""Read/hash/decode existing final videos; never encode or modify media."""
from pathlib import Path
import datetime,hashlib,json
import cv2
A=Path(__file__).resolve().parents[2];P=A.parent
items=[('V1','edits/voice-agents-9x16/voice-agents-9x16.mp4',30,641),('V2','edits/voice-agents-editorial-v2/voice-agents-editorial-v2.mp4',30,641),('V3','edits/voice-agents-morph-v3/voice-agents-morph-v3.mp4',60,1282)]
initial=json.loads((A/'references/evidence/initial-remote-state.json').read_text())
remote={x['path']:x for x in initial['tracked_files']}
reports=[]
for version,rel,fps,frames in items:
 p=P/rel;data=p.read_bytes();sha256=hashlib.sha256(data).hexdigest();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 cap=cv2.VideoCapture(str(p));w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));rate=cap.get(cv2.CAP_PROP_FPS);metadata_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));decoded=0
 while True:
  ok,frame=cap.read()
  if not ok:break
  if frame is None or frame.size==0:raise RuntimeError('Empty decoded frame in '+rel)
  decoded+=1
 cap.release()
 passed=(w,h)==(1080,1920)and abs(rate-fps)<.01 and decoded==frames and metadata_count==frames and blob==remote[rel]['sha']
 r={'version':version,'path':rel,'bytes':len(data),'sha256':sha256,'gitBlobMatchesInitialRemote':blob==remote[rel]['sha'],'width':w,'height':h,'fps':rate,'metadataFrames':metadata_count,'decodedFrames':decoded,'fullVideoDecodePassed':passed,'audioReanalysedNow':False}
 reports.append(r);print(version,'PASS'if passed else'FAIL',w,h,rate,decoded,'frames',len(data),'bytes')
 if not passed:raise RuntimeError('Existing video validation failed: '+rel)
report={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'OpenCV full video decode + SHA-256 + Git blob comparison; no media encoding','result':'PASS','videos':reports,'audioNote':'Audio alignment/loudness were measured during historical export. This read-only check does not reanalyse audio; matching file bytes preserve linkage to the historical reports.'}
(A/'references/evidence/current-media-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('CURRENT_MEDIA_CHECK_PASS; no new video created.')
