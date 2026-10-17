#!/usr/bin/env python3
"""Controlled different-aspect/duration fixture and negative geometry/source tests.
Prepare -> inspect stills with vision tools -> render -> inspect encoded output.
"""
from pathlib import Path
import argparse,json,sys,subprocess
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from edit import Film,PACKAGE,digest,ffmpeg,run,inspect_source,render,qc

def prepare(work):
    if work.exists():raise FileExistsError('Use a fresh test work directory')
    work.mkdir(parents=True)
    source=work/'portrait.mp4'
    run([ffmpeg(),'-y','-v','error','-ss','9.54','-i',str(ROOT/'tests/fixtures/original-raw.mp4'),'-t','2.39','-vf','crop=202:360:40:0,fps=30','-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-ar','44100',str(source)])
    original=json.loads((ROOT/'tests/fixtures/original-transcript.json').read_text());words=[]
    for seg in original['segments']:
        for w in seg['words']:
            if 9.54-.001<=w['start']<11.93:words.append({**w,'start':w['start']-9.54,'end':w['end']-9.54})
    transcript={'language':'en','segments':[{'start':0,'end':1.89,'text':' '.join(w['word']for w in words),'words':words}]};(work/'transcript.json').write_text(json.dumps(transcript,indent=2))
    logo=Image.new('RGBA',(240,96),(0,0,0,0));d=ImageDraw.Draw(logo);d.text((16,15),'TEST',font=__import__('edit').font('sans',80,800),fill=(0,0,0,255));logo.save(work/'test-logo.png')
    captions={'kind':'caption','rect':[.09,.77,.76,.055],'font_px':54}
    plan={'version':1,'source_sha256':digest(source),'transcript':'transcript.json','clip_start':0,'clip_end':2.39,'duration':3.0,'fps':30,'safe_profile':'mobile-conservative','logos':[{'asset':'test-logo.png','rect':[.08,.10,.16,.026],'plate':[255,252,244],'required':True}],'avoid_regions':[{'start':0,'end':1.0,'rect':[.28,.30,.44,.38]},{'start':1.0,'end':1.8,'rect':[.30,.53,.4,.225]}],'scenes':[
    {'id':'portrait-intro','start':0,'end':1.0,'background':[3,3,3],'layers':[{'kind':'text','text':'A priority.','font':'italic','font_px':130,'rect':[.12,.17,.72,.08]}, {'kind':'video','rect':[.28,.30,.44,.43],'fit':'contain','radius':28},captions]},
    {'id':'faithful-quote','start':1.0,'end':1.8,'background':[237,234,230],'grid':True,'transition':{'kind':'crossfade','seconds':.14},'layers':[{'kind':'quote','range':[.68,1.14],'rect':[.10,.21,.72,.23],'font_px':112,'color':[11,12,12]}, {'kind':'video','rect':[.30,.53,.4,.225],'mask':'circle','fit':'contain'}]},
    {'id':'payoff','start':1.8,'end':3.0,'background':[251,73,8],'transition':{'kind':'wipe','seconds':.14},'layers':[{'kind':'text','text':'Invested.','font':'italic','font_px':220,'rect':[.12,.28,.72,.16]}, {'kind':'text','text':'a lot in that.','font':'italic','font_px':105,'rect':[.12,.48,.72,.09]}, {'kind':'waveform','rect':[.18,.70,.64,.06],'color':[255,252,244]}]}
    ]}
    (work/'plan.json').write_text(json.dumps(plan,indent=2))
    info=inspect_source(source,work/'inspection');assert(info['decoded_width'],info['decoded_height'])==(202,360);f=Film(source,work/'plan.json')
    try:render(f,work,True)
    finally:f.close()
    print('PREPARED. Test logo is synthetic TEST ONLY, never a real user logo. Inspect portrait crop/quote/transition stills before render.')

def negatives(work):
    original=json.loads((work/'plan.json').read_text());results=[]
    bad={**original,'source_sha256':'0'*64};(work/'bad-source.json').write_text(json.dumps(bad))
    try:f=Film(work/'portrait.mp4',work/'bad-source.json');f.close();raise AssertionError('Fingerprint mismatch was accepted')
    except ValueError as e:results.append({'test':'different source rejected','pass':'fingerprint'in str(e)})
    bad=json.loads(json.dumps(original));bad['logos'][0]['rect']=[.91,.10,.08,.026];(work/'bad-boundary.json').write_text(json.dumps(bad));f=Film(work/'portrait.mp4',work/'bad-boundary.json')
    try:_,meta=f.frame(.5);assert'logo-safe'in meta['violations'];results.append({'test':'out-of-safe logo detected','pass':True})
    finally:f.close()
    bad=json.loads(json.dumps(original));bad['logos'][0]['rect']=[.31,.35,.16,.026];(work/'bad-collision.json').write_text(json.dumps(bad));f=Film(work/'portrait.mp4',work/'bad-collision.json')
    try:_,meta=f.frame(.5);assert'logo-protected-region'in meta['violations'];results.append({'test':'logo/face-region collision detected','pass':True})
    finally:f.close()
    bad=json.loads(json.dumps(original));bad['scenes'][1]['start']=1.4;(work/'bad-gap.json').write_text(json.dumps(bad))
    try:f=Film(work/'portrait.mp4',work/'bad-gap.json');f.close();raise AssertionError('Timeline gap accepted')
    except ValueError as e:results.append({'test':'timeline gap rejected','pass':'gap'in str(e)})
    bad=json.loads(json.dumps(original));bad['logos'][0]['keyframes']=[{'time':0,'rect':[.08,.10,.16,.026]},{'time':1,'rect':[.95,.10,.16,.026]}];(work/'bad-moving-logo.json').write_text(json.dumps(bad));f=Film(work/'portrait.mp4',work/'bad-moving-logo.json')
    try:
        _,first=f.frame(0);_,later=f.frame(1.1);assert'logo-safe'not in first['violations']and'logo-safe'in later['violations'];results.append({'test':'moving logo late boundary crossing detected','pass':True})
    finally:f.close()
    f=Film(work/'portrait.mp4',work/'plan.json')
    try:
        _,meta=f.frame(1.4);assert not any(r['id'].strip('“”')=='SO'for r in meta['objects']);results.append({'test':'quote end boundary excludes next sentence','pass':True})
        logo_crops=[]
        for i in range(f.frames):
            im,meta=f.frame(i/f.fps);logo_crops.append(np.asarray(im.crop((86,192,259,242))))
        assert all(np.array_equal(logo_crops[0],x)for x in logo_crops);results.append({'test':'screen logo unchanged across every pre-encode frame and background transition','frames':f.frames,'pass':True})
    finally:f.close()
    white=Image.new('RGBA',(60,60),(255,255,255,255));white.save(work/'white-logo.png');bad=json.loads(json.dumps(original));bad['logos'][0]['asset']='white-logo.png';(work/'bad-contrast.json').write_text(json.dumps(bad))
    try:f=Film(work/'portrait.mp4',work/'bad-contrast.json');f.close();raise AssertionError('Invisible white-on-white logo accepted')
    except ValueError as e:results.append({'test':'white-on-white logo rejected','pass':'contrast'in str(e)})
    assert all(r['pass']for r in results);(work/'negative-tests.json').write_text(json.dumps(results,indent=2));print('NEGATIVE_TESTS_PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workdir',required=True,type=Path);ap.add_argument('--phase',choices=['prepare','render','negative'],required=True);a=ap.parse_args();work=a.workdir.resolve()
    if a.phase=='prepare':prepare(work)
    elif a.phase=='negative':negatives(work)
    else:
        f=Film(work/'portrait.mp4',work/'plan.json')
        try:render(f,work,False)
        finally:f.close()
        qc(work);negatives(work)
if __name__=='__main__':main()
