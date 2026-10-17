#!/usr/bin/env python3
"""Regression fixture ONLY. Replays the known V2; refuses any other source hash.
This is not the entry point for new footage; use edit.py with a new inspected plan.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
import cv2,numpy as np
from PIL import Image,ImageDraw
from edit import ffmpeg,digest,run,PACKAGE

def compare_audio(rendered,reference):
    def pcm(path):
        return np.frombuffer(run([ffmpeg(),'-v','error','-i',str(path),'-vn','-ac','2','-ar','48000','-f','f32le','-']).stdout,dtype=np.float32)
    a=pcm(rendered);b=pcm(reference)
    return {'decodedFloatSamplesRendered':len(a),'decodedFloatSamplesReference':len(b),'decodedPCMExactlyEqual':bool(len(a)==len(b)and np.array_equal(a,b)),'maxAbsSampleDifference':float(np.max(np.abs(a[:min(len(a),len(b))]-b[:min(len(a),len(b))])))if len(a)and len(b)else None,'scope':'Decoded stereo 48kHz sample comparison on the exact regression fixture, not independent perceptual listening.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workdir',required=True,type=Path);ap.add_argument('--reference',type=Path);ap.add_argument('--style',choices=['v1','v2','v3'],default='v2');args=ap.parse_args();work=args.workdir.resolve()
    if work.exists():raise FileExistsError('Choose a fresh regression work directory')
    work.mkdir(parents=True)
    provenance=json.loads((PACKAGE/'tests/evidence/copied-assets.json').read_text())
    for item in provenance:
        if digest(PACKAGE/item['bundled'])!=item['sha256']:raise ValueError('Bundled evidence changed: '+item['bundled'])
    for p in(PACKAGE/'assets/fonts').iterdir():
        dst=work/'assets/fonts'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    for src,dest in [('tests/fixtures/original-raw.mp4','assets/raw.mp4'),('tests/fixtures/original-transcript.json','analysis/transcript.json'),('tests/fixtures/original-asr.wav','analysis/raw-audio.wav'),('tests/fixtures/original-captions.srt','edits/voice-agents-9x16/captions.srt')]:
        dst=work/dest;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PACKAGE/src,dst)
    (work/'cache').mkdir()
    recipes={'v1':('render_v1.original.py','audio_v1.original.py',None),'v2':('editorial_v2.original.py','audio_editorial_v2.original.py','/home/user/.cache/video-project-editorial-v2'),'v3':('render_morph_v3.original.py','audio_morph_v3.original.py','/home/user/.cache/video-project-v3')}
    recipe=recipes[args.style];manifest=json.loads((PACKAGE/'templates/baseline-manifest.json').read_text())[args.style]
    for source,dest in [(recipe[0],'render.py'),(recipe[1],'audio.py')]:
        text=(PACKAGE/'templates'/source).read_text();old=f"CACHE=Path('{recipe[2]}')"
        if recipe[2]:
            assert text.count(old)==1
            text=text.replace(old,"CACHE=ROOT/'cache'")
        target=work/'source'/dest;target.parent.mkdir(exist_ok=True);target.write_text(text)
    subprocess.run([sys.executable,str(work/'source/audio.py')],check=True)
    subprocess.run([sys.executable,str(work/'source/render.py'),'--stills','--render'],check=True)
    final=work/'baseline-replay.mp4'
    visual=work/('analysis/visuals.mp4'if args.style=='v1'else'cache/visuals-editorial-v2.mp4'if args.style=='v2'else'cache/visuals-morph-v3.mp4')
    audio=work/('analysis/final-audio.wav'if args.style=='v1'else'cache/editorial-v2-audio.wav'if args.style=='v2'else'cache/morph-v3-audio.wav')
    run([ffmpeg(),'-y','-v','error','-i',str(visual),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-map_metadata','-1','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(final)])
    run([ffmpeg(),'-v','error','-i',str(final),'-f','null','-'])
    report={'test':'Original '+args.style+' regression, not a new-footage workflow','source_sha256':digest(work/'assets/raw.mp4'),'only_source_changes':('No source logic changed; ROOT relocates to the isolated fixture.'if args.style=='v1'else'Both runtime copies replace only the absolute cache assignment with ROOT/cache. No timing/layout/audio logic changed.'),'render_sha256':digest(final),'fullDecodePassed':True,'visualComparisonPerformed':False}
    if args.reference:
        expected=manifest['reference_sha256']
        if digest(args.reference)!=expected:raise ValueError('Reference is not the known approved V2 file')
        a=cv2.VideoCapture(str(final));b=cv2.VideoCapture(str(args.reference));errors=[];equal=0;count=0;thumbs=[]
        while True:
            oka,fa=a.read();okb,fb=b.read()
            if not oka or not okb:
                if oka!=okb:raise ValueError('Frame-count mismatch')
                break
            if fa.shape!=fb.shape:raise ValueError('Dimensions differ')
            error=float(np.mean(np.abs(fa.astype(np.int16)-fb.astype(np.int16))));errors.append(error);equal+=bool(np.array_equal(fa,fb))
            if count in[round(x*manifest['fps'])for x in[.8,3.7,10.55,13.9,18.45,20.5]]:
                thumbs.append((count,Image.fromarray(cv2.cvtColor(fb,cv2.COLOR_BGR2RGB)),Image.fromarray(cv2.cvtColor(fa,cv2.COLOR_BGR2RGB))))
            count+=1
        a.release();b.release();sheet=Image.new('RGB',(1080,3*510),(23,23,23));d=ImageDraw.Draw(sheet)
        for i,(frame,ref,new)in enumerate(thumbs):
            x=i%2*540;y=i//2*510
            for j,image in enumerate([ref,new]):sheet.paste(image.resize((270,480),Image.Resampling.LANCZOS),(x+j*270,y))
            d.text((x+8,y+485),f"{frame/manifest['fps']:.2f}s: approved | replay",fill='white')
        sheet.save(work/'comparison-contact.jpg',quality=94)
        report.update({'visualComparisonPerformed':True,'reference_sha256':expected,'decodedFramesCompared':count,'identicalDecodedFrames':equal,'meanFrameRGB_MAE':float(np.mean(errors)),'maxFrameRGB_MAE':max(errors),'comparisonPass':count==manifest['frames'] and np.mean(errors)<1.5 and max(errors)<3.,'warning':'Pixel similarity is a regression check on this exact fixture, not a guarantee of equivalent creative quality on unrelated footage.'})
        report['audioComparison']=compare_audio(final,args.reference)
        if not report['comparisonPass']:raise RuntimeError('Regression differs too much; inspect before claiming a match')
    (work/'replay-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
