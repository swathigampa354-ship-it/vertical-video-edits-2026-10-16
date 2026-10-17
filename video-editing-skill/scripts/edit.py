#!/usr/bin/env python3
"""Portable, plan-driven editorial compositor. No credentials or fixed source clock.
Inspect first; an AI director must author a source-bound plan from the actual speech.
"""
from pathlib import Path
from functools import lru_cache
import argparse,hashlib,json,math,os,re,shutil,subprocess,sys,time,importlib.util
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageChops
import soundfile as sf
from scipy.signal import butter,sosfilt,correlate,correlation_lags
from scipy.ndimage import uniform_filter1d

PACKAGE=Path(__file__).resolve().parents[1]
PRESET=json.loads((PACKAGE/'templates/editorial-preset.json').read_text())
W,H=1080,1920

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ffmpeg():
    p=os.environ.get('FFMPEG_BIN')or shutil.which('ffmpeg')
    if p:return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:raise RuntimeError('Install core requirements or set FFMPEG_BIN to a working FFmpeg executable.')
def run(args):
    r=subprocess.run(args,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-3500:])
    return r

def dump(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def ease(p):return 1-(1-max(0.,min(1.,p)))**3

def box(rect):return [rect[0]*W,rect[1]*H,rect[2]*W,rect[3]*H]
def overlaps(a,b):return a[0]<b[0]+b[2]and a[0]+a[2]>b[0]and a[1]<b[1]+b[3]and a[1]+a[3]>b[1]
def inside(a,s):return a[0]>=s[0]-.5 and a[1]>=s[1]-.5 and a[0]+a[2]<=s[2]+.5 and a[1]+a[3]<=s[3]+.5

def rect_at(layer,t):
    keys=layer.get('keyframes',[])
    if not keys:return layer['rect']
    if t<=keys[0]['time']:return keys[0]['rect']
    for a,b in zip(keys,keys[1:]):
        if a['time']<=t<=b['time']:
            p=ease((t-a['time'])/(b['time']-a['time']))
            return [x+(y-x)*p for x,y in zip(a['rect'],b['rect'])]
    return keys[-1]['rect']

@lru_cache(maxsize=128)
def font(kind,size,weight=800):
    path=Path(kind)
    if not path.is_file():path=PACKAGE/'assets/fonts'/PRESET['type'].get(kind,kind)
    f=ImageFont.truetype(str(path),int(size))
    try:
        axes=f.get_variation_axes();values=[]
        for axis in axes:
            name=axis['name'].decode()if isinstance(axis['name'],bytes)else str(axis['name'])
            values.append(weight if'Weight'in name else min(axis['maximum'],32)if'Optical'in name else axis['default'])
        f.set_variation_by_axes(values)
    except OSError:pass
    return f

@lru_cache(maxsize=256)
def glyph(s,kind,size,color,weight):
    f=font(kind,size,weight);bb=f.getbbox(s);a=Image.new('RGBA',(max(1,bb[2]-bb[0]+24),max(1,bb[3]-bb[1]+24)))
    ImageDraw.Draw(a).text((12-bb[0],12-bb[1]),s,font=f,fill=(*color,255));return a

def tokens(transcript,clip_start=0,clip_end=1e12):
    words=[]
    for seg in transcript.get('segments',[]):
        for w in seg.get('words',[]):
            if w['start']>=clip_start-.001 and w['start']<clip_end:
                words.append({'word':str(w['word']).strip(),'start':w['start']-clip_start,'end':w['end']-clip_start})
    return words

def groups(words):
    out=[];g=[]
    for w in words:
        if g and(w['start']-g[-1]['end']>.38 or len(g)>=5 or w['end']-g[0]['start']>1.45):out.append(g);g=[]
        g.append(w)
        if w['word'].endswith(('.',',','?','!'))and len(g)>=2:out.append(g);g=[]
    if g:out.append(g)
    return out

def write_srt(path,words):
    def ts(t):
        ms=max(0,round(t*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    text=[]
    for i,g in enumerate(groups(words),1):text.append(f"{i}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'])}\n{' '.join(w['word']for w in g)}\n")
    path.write_text('\n'.join(text))

class Source:
    def __init__(self,path):
        self.cap=cv2.VideoCapture(str(path));self.fps=self.cap.get(cv2.CAP_PROP_FPS);self.count=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT));self.last=-1;self.frame=None
        if not self.cap.isOpened()or self.fps<=0 or self.count<1:raise ValueError('Cannot open source video')
    def get(self,t):
        i=min(self.count-1,max(0,math.floor(t*self.fps+1e-8)))
        if i==self.last:return self.frame.copy()
        if i!=self.last+1:self.cap.set(cv2.CAP_PROP_POS_FRAMES,i)
        ok,a=self.cap.read()
        if not ok:raise RuntimeError(f'Cannot decode source frame {i}; refusing to silently repeat a stale frame.')
        self.last=i;self.frame=cv2.cvtColor(a,cv2.COLOR_BGR2RGB);return self.frame.copy()
    def close(self):self.cap.release()

def inspect_source(path,work):
    work.mkdir(parents=True,exist_ok=True);src=Source(path)
    r=subprocess.run([ffmpeg(),'-hide_banner','-i',str(path)],capture_output=True,text=True);description=r.stderr
    m=re.search(r'Duration: (\d+):(\d+):([\d.]+)',description)
    duration=(int(m[1])*3600+int(m[2])*60+float(m[3]))if m else src.count/src.fps
    times=np.linspace(0,max(0,src.count/src.fps-.1),12);sheet=Image.new('RGB',(1200,780),(24,24,24));d=ImageDraw.Draw(sheet)
    frames=[]
    for i,t in enumerate(times):
        a=Image.fromarray(src.get(float(t)));frames.append(a.copy())
        a.thumbnail((300,230));x=i%4*300;y=i//4*260;sheet.paste(a,(x+(300-a.width)//2,y));d.text((x+10,y+236),f'{t:.3f}s',fill='white')
    sheet.save(work/'source-contact.jpg',quality=94)
    # Full low-resolution temporal pass: candidate cuts only, not semantic selection.
    c=cv2.VideoCapture(str(path));previous=None;cuts=[];idx=0
    while True:
        ok,f=c.read()
        if not ok:break
        small=cv2.resize(f,(160,90));hist=cv2.calcHist([small],[0,1],None,[24,24],[0,256,0,256]);cv2.normalize(hist,hist)
        if previous is not None:
            score=cv2.compareHist(previous,hist,cv2.HISTCMP_BHATTACHARYYA)
            if score>.55:cuts.append({'time':idx/src.fps,'histogram_distance':score})
        previous=hist;idx+=1
    c.release()
    vfr=run([ffmpeg(),'-hide_banner','-i',str(path),'-vf','vfrdet','-frames:v','1000','-an','-f','null','-']).stderr.decode(errors='replace')
    vf=re.findall(r'VFR:([\d.]+)',vfr)
    first=frames[0];report={'sha256':digest(path),'decoded_width':first.width,'decoded_height':first.height,'fps':src.fps,'video_frames':src.count,'video_duration':src.count/src.fps,'container_duration':duration,'audio_present':bool(re.search(r'Stream.*Audio:',description)),'candidate_cuts':cuts,'vfr_sample_ratio':float(vf[-1])if vf else None,'rotation_metadata':src.cap.get(cv2.CAP_PROP_ORIENTATION_META),'hdr_suspected':any(v in description.lower()for v in ['smpte2084','arib-std-b67','bt2020']),'notes':['Cuts are visual heuristics, not a ranking of best speech. Inspect the contact and listen to the source.','VFR detection covers at most the first 1000 frames. Investigate uncertain/variable timing before using frame-index source sampling.','Aspect/crop coordinates refer to decoded orientation; no face identity/tracking or stabilization is inferred.']}
    src.close();dump(work/'source.json',report);(work/'source-stream-info.txt').write_text(description);print(json.dumps(report,indent=2));return report

def transcribe_source(path,work,model_name,language):
    from faster_whisper import WhisperModel
    work.mkdir(parents=True,exist_ok=True);audio=work/'asr.wav'
    run([ffmpeg(),'-y','-v','error','-i',str(path),'-vn','-ac','1','-ar','16000',str(audio)])
    samples,sr=sf.read(audio,dtype='float32');assert sr==16000
    model=WhisperModel(model_name,device='cpu',compute_type='int8',cpu_threads=max(1,min(2,os.cpu_count()or 1)))
    segments,info=model.transcribe(samples,language=None if language=='auto'else language,word_timestamps=True,beam_size=5,vad_filter=False)
    data={'source_sha256':digest(path),'language':info.language,'segments':[]}
    for s in segments:data['segments'].append({'start':s.start,'end':s.end,'text':s.text,'words':[{'word':w.word.strip(),'start':w.start,'end':w.end,'probability':w.probability}for w in(s.words or [])]})
    if not tokens(data):raise RuntimeError('No word-timed transcript. Review source/model/language; do not invent captions.')
    dump(work/'transcript.json',data);print('TRANSCRIPT_WRITTEN; review spelling, names, low-confidence words and timing.')

class Film:
    def __init__(self,input_path,plan_path):
        self.input=Path(input_path).resolve();self.plan_path=Path(plan_path).resolve();self.plan=json.loads(self.plan_path.read_text());self.base=self.plan_path.parent
        transcript=json.loads(self.resolve(self.plan['transcript']).read_text())
        if transcript.get('source_sha256')!=digest(self.input):raise ValueError('Transcript fingerprint mismatch/missing: transcribe or inspect/review and bind it to this actual source; do not reuse old timings.')
        self.words=tokens(transcript,self.plan.get('clip_start',0),self.plan['clip_end']);self.cues=groups(self.words)
        self.src=Source(self.input);self.fps=int(self.plan.get('fps',30));self.start=float(self.plan.get('clip_start',0));self.clip_length=self.plan['clip_end']-self.start;self.duration=float(self.plan['duration']);self.frames=round(self.duration*self.fps)
        self.safe=PRESET['safe_profiles'][self.plan.get('safe_profile','mobile-conservative')];self.safe=[self.safe[0]*W,self.safe[1]*H,self.safe[2]*W,self.safe[3]*H];self.logos=self.plan.get('logos',[]);self.scene_cache={}
        try:self.validate()
        except Exception:
            self.src.close();raise
    def resolve(self,p):return(Path(p)if Path(p).is_absolute()else self.base/p).resolve()
    def font_name(self,kind):
        override=self.plan.get('font_overrides',{}).get(kind)
        return str(self.resolve(override))if override else kind
    def validate(self):
        p=self.plan
        if p.get('version')!=1:raise ValueError('Plan version must be 1')
        if p['source_sha256']!=digest(self.input):raise ValueError('Source fingerprint mismatch: inspect this new footage and write a new source-bound plan.')
        if self.fps not in[24,25,30,50,60]:raise ValueError('Choose an explicit supported CFR output fps')
        if not(0<=self.start<p['clip_end']<=self.src.count/self.src.fps+.16):raise ValueError('Clip timestamps outside source')
        if not(self.clip_length<=self.duration<=self.clip_length+1.5):raise ValueError('Duration must preserve selected speech and use at most 1.5 seconds explicit postroll')
        if not self.words:raise ValueError('Word timing is required for speech-led editing')
        def check_motion(item):
            for key in ['keyframes','roi_keyframes']:
                previous=-1e20
                for k in item.get(key,[]):
                    if k['time']<=previous or not 0<=k['time']<=self.duration:raise ValueError('Motion keyframes must be strictly ordered on the edit clock')
                    previous=k['time'];r=k['rect']
                    if len(r)!=4 or r[2]<=0 or r[3]<=0:raise ValueError('Invalid motion rectangle')
        for event in p.get('sfx',[]):
            if not 0<=event['at']<self.duration:raise ValueError('SFX event outside new edit timeline')
        for item in p.get('logos',[])+p.get('avoid_regions',[]):check_motion(item)
        last=0.
        for s in p['scenes']:
            if abs(s['start']-last)>1/self.fps or s['end']<=s['start']:raise ValueError('Scene gaps/overlap/order; use contiguous timeline')
            last=s['end']
            for layer in s['layers']:
                check_motion(layer)
                if layer['kind']=='video'and layer.get('fit','contain')=='cover'and'roi'not in layer:raise ValueError('Cover crop requires an explicitly inspected normalized source ROI')
                if layer['kind']=='image'and not self.resolve(layer['asset']).is_file():raise FileNotFoundError(layer['asset'])
        if abs(last-self.duration)>1/self.fps:raise ValueError('Scenes must cover the entire output')
        for logo in self.logos:
            if not self.resolve(logo['asset']).is_file():raise FileNotFoundError('Required logo asset missing')
            if logo.get('required',True)and(logo.get('start',0)>0 or logo.get('end',self.duration)<self.duration):raise ValueError('Required logo is not scheduled throughout the film')
            if logo.get('plate')is None:raise ValueError('Supply an approved solid logo plate for deterministic contrast; do not guess on moving backgrounds')
            rgba=np.asarray(Image.open(self.resolve(logo['asset'])).convert('RGBA'),dtype=np.float32)/255.;alpha=rgba[:,:,3];visible=alpha>.25
            if not np.any(visible):raise ValueError('Logo asset is fully transparent')
            bg=np.asarray(logo['plate'],dtype=np.float32)/255.;rgb=rgba[:,:,:3]*alpha[:,:,None]+bg*(1-alpha[:,:,None])
            def luminance(c):
                linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);return np.sum(linear*np.array([.2126,.7152,.0722]),axis=-1)
            fg=luminance(rgb);back=float(luminance(bg));ratio=(np.maximum(fg,back)+.05)/(np.minimum(fg,back)+.05)
            if float(np.max(ratio[visible]))<3:raise ValueError('Logo has no sufficiently contrasting pixels on its plate; choose an approved alternate variant/backing')
        # Bundled Latin fonts do not magically cover all scripts.
        from fontTools.ttLib import TTFont
        chars=set(''.join(w['word']for w in self.words)+''.join(l.get('text','')for s in p['scenes']for l in s['layers']))
        for kind in ['serif','italic','sans']:
            name=self.font_name(kind);path=Path(name)if Path(name).is_file()else PACKAGE/'assets/fonts'/PRESET['type'][kind];f=TTFont(path);cmap=f.getBestCmap();missing={c for c in chars if not c.isspace()and ord(c)not in cmap};f.close()
            if missing:raise ValueError('Font coverage missing '+repr(''.join(sorted(missing)))+'; provide/review language-appropriate fonts rather than tofu glyphs.')
    def close(self):self.src.close()
    def draw_text(self,im,s,rect,kind,size,color,weight,alpha,records,role='headline',rotation=0,fixed=False):
        kind=self.font_name(kind);x,y,w,h=rect;minimum={'caption':46,'headline':72,'quote':72,'label':26,'decorative':16}.get(role,40)
        while size>=minimum:
            a=glyph(s,kind,size,tuple(color),weight)
            if rotation:a=a.rotate(rotation,expand=True,resample=Image.Resampling.BICUBIC)
            if fixed or(a.width-24<=w and a.height-24<=h):break
            size-=1
        if size<minimum:raise ValueError(f'Text cannot fit at readable size ({role}): {s!r}. Redesign/reflow; do not squeeze it.')
        a=a.copy();a.putalpha(a.getchannel('A').point(lambda v:round(v*max(0,min(1,alpha)))))
        xx=x+(w-a.width)/2;yy=y+(h-a.height)/2;im.paste(a,(round(xx),round(yy)),a)
        if alpha>.20:records.append({'id':s,'role':role,'rect':[xx+12,yy+12,a.width-24,a.height-24]})
    def draw_quote(self,im,layer,t,records):
        rect=box(rect_at(layer,t));kind=self.font_name(layer.get('font','sans'));size=layer.get('font_px',88);start,end=layer['range'];selected=[w.copy()for w in self.words if start-.001<=w['start']<end-.001]
        if not selected:raise ValueError('Quote range contains no actual words')
        for w in selected:
            if layer.get('uppercase',True):w['word']=w['word'].upper()
        if layer.get('quotation_marks',True):selected[0]['word']='“'+selected[0]['word'];selected[-1]['word']+='”'
        while size>=72:
            f=font(kind,size,layer.get('weight',800));rows=[[]]
            for w in selected:
                trial=' '.join(x['word']for x in rows[-1]+[w])
                if rows[-1]and f.getlength(trial)>rect[2]:rows.append([])
                rows[-1].append(w)
            leading=size*1.20
            if len(rows)*leading<=rect[3]and all(f.getlength(' '.join(w['word']for w in row))<=rect[2]for row in rows):break
            size-=1
        if size<72:raise ValueError('Quote too dense. Shorten to a faithful excerpt or split the beat; do not speed unreadable text.')
        for i,row in enumerate(rows):
            x=rect[0]
            for w in row:
                ww=f.getlength(w['word']);alpha=ease((t-w['start'])/.065)
                self.draw_text(im,w['word'],[x,rect[1]+i*leading+4*(1-alpha),ww,leading],kind,size,layer.get('color',[11,12,12]),800,alpha,records,'quote',fixed=True);x+=ww+f.getlength(' ')
    def draw_captions(self,im,layer,t,records):
        for i,g in enumerate(self.cues):
            end=min(self.cues[i+1][0]['start']if i+1<len(self.cues)else g[-1]['end']+.18,g[-1]['end']+.38)
            if g[0]['start']<=t<end:
                s=' '.join(w['word']for w in g);rect=box(rect_at(layer,t));size=layer.get('font_px',54);kind=self.font_name(layer.get('font','serif'))
                while size>=46 and font(kind,size).getlength(s)>rect[2]:size-=1
                if size<46:raise ValueError('Caption too dense for its box; split/reflow')
                f=font(kind,size);x=rect[0]+(rect[2]-f.getlength(s))/2;right=None
                for w in g:
                    ww=f.getlength(w['word'])
                    if t>=w['start']:
                        alpha=ease((t-w['start'])/.065)
                        self.draw_text(im,w['word'],[x,rect[1],ww,rect[3]],kind,size,layer.get('color',[255,252,244]),800,alpha,records,'caption',fixed=True)
                        if alpha>.05:right=x+ww
                    x+=ww+f.getlength(' ')
                if right is not None:
                    rr=[right+5,rect[1]+rect[3]*.2,3,rect[3]*.6];ImageDraw.Draw(im).rectangle((rr[0],rr[1],rr[0]+rr[2],rr[1]+rr[3]),fill=tuple(PRESET['palette']['orange']));records.append({'id':'caption-caret','role':'caption','rect':rr})
                return
    def scene(self,scene,raw,t,records):
        im=Image.new('RGB',(W,H),tuple(scene.get('background',[3,3,3])));d=ImageDraw.Draw(im)
        if scene.get('grid'):
            for x in range(-12,W,34):d.line([(x,0),(x,H)],fill=(205,201,199),width=1)
            for y in range(-12,H,34):d.line([(0,y),(W,y)],fill=(205,201,199),width=1)
        for layer in scene['layers']:
            if not layer.get('start',scene['start'])<=t<layer.get('end',scene['end']):continue
            kind=layer['kind'];rect=box(rect_at(layer,t))if'rect'in layer or'keyframes'in layer else None
            alpha=ease((t-layer.get('reveal_at',layer.get('start',scene['start'])))/layer.get('reveal_seconds',.18))
            if kind in['video','image']:
                a=Image.fromarray(raw)if kind=='video'else Image.open(self.resolve(layer['asset'])).convert('RGBA')
                if kind=='video':
                    roi=rect_at({'rect':layer.get('roi',[0,0,1,1]),'keyframes':layer.get('roi_keyframes',[])},t);sw,sh=a.size;x,y,w,h=roi
                    if not(0<=x<1 and 0<=y<1 and w>0 and h>0 and x+w<=1.00001 and y+h<=1.00001):raise ValueError('Invalid inspected source ROI')
                    a=a.crop((round(x*sw),round(y*sh),round((x+w)*sw),round((y+h)*sh)))
                x,y,w,h=map(round,rect);w=max(1,w);h=max(1,h);scale=(max if layer.get('fit','contain')=='cover'else min)(w/a.width,h/a.height)
                resized=a.resize((max(1,round(a.width*scale)),max(1,round(a.height*scale))),Image.Resampling.BICUBIC)
                plate=Image.new('RGBA',(w,h),(*PRESET['palette']['black'],255)if kind=='video'else(0,0,0,0));plate.alpha_composite(resized.convert('RGBA'),((w-resized.width)//2,(h-resized.height)//2))
                mask=Image.new('L',(w*2,h*2),0);md=ImageDraw.Draw(mask)
                if layer.get('mask')=='circle':md.ellipse((0,0,w*2-1,h*2-1),fill=255)
                else:md.rounded_rectangle((0,0,w*2-1,h*2-1),radius=layer.get('radius',0)*2,fill=255)
                mask=ImageChops.multiply(mask.resize((w,h),Image.Resampling.LANCZOS),plate.getchannel('A'));im.paste(plate.convert('RGB'),(x,y),mask)
            elif kind=='text':
                r=rect.copy();r[1]+=layer.get('enter_dy',.008)*H*(1-alpha)
                self.draw_text(im,layer['text'],r,layer.get('font','italic'),layer.get('font_px',120),layer.get('color',[255,252,244]),layer.get('weight',800),alpha,records,layer.get('role','headline'),layer.get('rotation',0))
            elif kind=='quote':self.draw_quote(im,layer,t,records)
            elif kind=='caption':self.draw_captions(im,layer,t,records)
            elif kind=='shape':
                x,y,w,h=rect;c=tuple(layer.get('color',[251,73,8]));which=layer.get('shape','rect')
                if which=='ellipse':d.ellipse((x,y,x+w,y+h),fill=c)
                else:d.rounded_rectangle((x,y,x+w,y+h),radius=layer.get('radius',0),fill=c)
            elif kind=='line':
                pts=[(x*W,y*H)for x,y in layer['points']];d.line(pts,fill=tuple(layer.get('color',[251,73,8])),width=layer.get('width',3))
            elif kind=='waveform':
                x,y,w,h=rect;n=layer.get('bars',61)
                for i in range(n):
                    xx=x+w*i/(n-1);hh=h*(.15+.75*abs(math.sin(i*.67+t*2.8))*abs(math.sin(i*.11+t*.3)))
                    d.rounded_rectangle((xx-3,y+h/2-hh/2,xx+3,y+h/2+hh/2),radius=3,fill=tuple(layer.get('color',[251,73,8])))
            else:raise ValueError('Unsupported layer kind: '+kind)
        return im
    def frame(self,t):
        raw=self.src.get(self.start+min(t,self.clip_length));records=[];scenes=self.plan['scenes'];index=next((i for i,s in enumerate(scenes)if s['start']<=t<s['end']),len(scenes)-1);s=scenes[index];im=self.scene(s,raw,t,records)
        dt=t-s['start'];transition=s.get('transition',{})
        if index>0 and dt<transition.get('seconds',.14):
            prev_records=[];old=self.scene(scenes[index-1],raw,s['start']-.0001,prev_records);q=ease(dt/transition.get('seconds',.14))
            if transition.get('kind','crossfade')=='wipe':edge=round(W*q);old.paste(im.crop((0,0,edge,H)),(0,0));im=old
            else:im=Image.blend(old,im,q)
            if q<.8:records+=prev_records
        problems=[]
        for r in records:
            if not inside(r['rect'],[0,0,W,H]):problems.append('canvas-text:'+r['id'])
            if r['role']!='decorative'and not inside(r['rect'],self.safe):problems.append('safe-text:'+r['id'])
            if r['role']!='decorative':
                for avoid in self.plan.get('avoid_regions',[]):
                    if avoid['start']<=t<avoid['end']and overlaps(r['rect'],box(rect_at(avoid,t))):problems.append('text-protected-region:'+r['id'])
        # Logo pass is AFTER every footage transform and scene transition.
        for logo in self.logos:
            if not logo.get('start',0)<=t<logo.get('end',self.duration):continue
            rect=box(rect_at(logo,t));x,y,w,h=map(round,rect)
            envelope=[x-8,y-8,w+16,h+16]
            if not inside(envelope,self.safe):problems.append('logo-safe')
            for r in records:
                if r['role']!='decorative'and overlaps(envelope,r['rect']):problems.append('logo-text:'+r['id'])
            for avoid in self.plan.get('avoid_regions',[]):
                if avoid['start']<=t<avoid['end']and overlaps(envelope,box(rect_at(avoid,t))):problems.append('logo-protected-region')
            ImageDraw.Draw(im).rounded_rectangle((x-8,y-8,x+w+8,y+h+8),radius=8,fill=tuple(logo['plate']))
            a=Image.open(self.resolve(logo['asset'])).convert('RGBA');a.thumbnail((w,h),Image.Resampling.LANCZOS);im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2),a)
            records.append({'id':'logo','role':'logo','rect':envelope})
        return im,{'time':t,'source_time':self.start+min(t,self.clip_length),'scene':s.get('id',str(index)),'objects':records,'violations':sorted(set(problems))}

def mix_audio(film,work):
    voice=work/'voice.wav';ff=ffmpeg();run([ff,'-y','-v','error','-ss',str(film.start),'-i',str(film.input),'-t',str(film.clip_length),'-vn','-af','highpass=f=65,loudnorm=I=-16:TP=-1.8:LRA=9','-ar','48000','-ac','2','-c:a','pcm_f32le',str(voice)])
    a,sr=sf.read(voice,dtype='float32',always_2d=True);n=round(film.frames/film.fps*sr);speech=np.zeros((n,2),np.float32);speech[:min(n,len(a))]=a[:n];fx=np.zeros_like(speech);rng=np.random.default_rng(1889)
    events=film.plan.get('sfx',[{'at':s['start'],'kind':'transition','gain':.011}for s in film.plan['scenes'][1:]])
    for event in events:
        at=event['at'];gain=event.get('gain',.011)
        if gain>.03:raise ValueError('SFX gain exceeds quiet editorial ceiling; explicit new sound design/review required')
        length=.19 if event['kind']=='transition'else .07;t=np.arange(round(length*sr))/sr
        if event['kind']=='transition':
            b=sosfilt(butter(2,[900,4200],fs=sr,btype='bandpass',output='sos'),rng.normal(size=len(t)))*np.sin(np.pi*np.arange(len(t))/len(t))**2
        else:b=np.sin(2*np.pi*event.get('frequency',1100)*t)*np.exp(-t*110)
        start=round(at*sr);end=min(n,start+len(b))
        if 0<=start<end:fx[start:end]+=b[:end-start,None]*gain*.707
    env=np.sqrt(uniform_filter1d(np.mean(speech**2,axis=1),size=int(sr*.075))+1e-9);fx*=np.clip(1-env*5,.5,1)[:,None]
    fade=min(n,round(.5*sr));fx[-fade:]*=np.linspace(1,0,fade)[:,None];mixed=speech+fx
    if np.max(np.abs(mixed))>.93:mixed*=.93/np.max(np.abs(mixed))
    sf.write(work/'mix.wav',mixed,sr,subtype='PCM_24')

def render(film,work,stills=False):
    work.mkdir(parents=True,exist_ok=True)
    if (work/'final.mp4').exists():raise FileExistsError('Use a new job/revision directory; refusing to overwrite a delivered render.')
    if stills:
        times=sorted(set([min(film.duration-.05,max(0,(s['start']+s['end'])/2))for s in film.plan['scenes']]+[max(0,s['start']+.08)for s in film.plan['scenes'][1:]]))
        cols=4;sheet=Image.new('RGB',(1080,math.ceil(len(times)/cols)*510),(24,24,24));d=ImageDraw.Draw(sheet)
        for i,t in enumerate(times):
            im,meta=film.frame(t);im.save(work/f'still-{i:02d}.jpg',quality=94);sheet.paste(im.resize((270,480),Image.Resampling.LANCZOS),(i%cols*270,i//cols*510));d.text((i%cols*270+7,i//cols*510+486),f'{t:.3f}s',fill='white')
        sheet.save(work/'stills-contact.jpg',quality=95);print('STILLS_READY: visually inspect these before full rendering.');return
    placements=work/'placements.jsonl';visual=work/'visuals.mp4';ff=ffmpeg()
    command=[ff,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(film.fps),'-i','-','-an','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(visual)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE);violations=[];started=time.monotonic()
    try:
        with placements.open('w')as log:
            for i in range(film.frames):
                im,meta=film.frame(i/film.fps);log.write(json.dumps(meta)+'\n')
                if meta['violations']:violations.append({'frame':i,'violations':meta['violations']})
                proc.stdin.write(im.tobytes())
                if i%90==0:print(f'{i}/{film.frames} frames ({time.monotonic()-started:.1f}s)',flush=True)
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Visual encode failed')
    dump(work/'placement-qc.json',{'framesChecked':film.frames,'violations':violations,'pass':not violations,'scope':'All-frame geometric checks only. Semantic crop/brand readability/contrast/manual viewing remain required.'})
    if violations:raise ValueError('Placement violations: inspect placement-qc.json and redesign; not delivering a failed layout')
    mix_audio(film,work)
    run([ff,'-y','-v','error','-i',str(visual),'-i',str(work/'mix.wav'),'-map','0:v:0','-map','1:a:0','-map_metadata','-1','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(work/'final.mp4')])
    write_srt(work/'captions.srt',film.words)
    poster,_=film.frame(max(0,film.duration-.45));poster.save(work/'poster.jpg',quality=95)
    dump(work/'job.json',{'source':str(film.input),'source_sha256':digest(film.input),'plan':str(film.plan_path),'plan_sha256':digest(film.plan_path),'frames':film.frames,'fps':film.fps,'duration':film.frames/film.fps,'clip_start':film.start,'clip_duration':film.clip_length,'logo_count':len(film.logos)})
    print('RENDERED; run QC and visually inspect the encoded output before delivery.')

def qc(work):
    job=json.loads((work/'job.json').read_text());final=work/'final.mp4';ff=ffmpeg();run([ff,'-v','error','-i',str(final),'-f','null','-'])
    cap=cv2.VideoCapture(str(final));width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));fps=cap.get(cv2.CAP_PROP_FPS);count=0;black=[]
    while True:
        ok,a=cap.read()
        if not ok:break
        if np.mean(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)>3)<.0001:black.append(count)
        count+=1
    cap.release()
    def audio(path,extra=[]):return np.frombuffer(run([ff,'-v','error',*extra,'-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','-']).stdout,dtype=np.float32)
    source=audio(job['source'],['-ss',str(job['clip_start'])]);encoded=audio(final);lags=[]
    length=min(job['clip_duration'],len(source)/16000);window=min(2.,max(.4,length/4))
    for t in np.linspace(.05,max(.05,length-window-.05),3):
        n=round(window*16000);start=round(t*16000);a=source[start:start+n];b=encoded[start:start+n]
        if len(a)!=n or len(b)!=n or np.std(a)<.0001:continue
        c=correlate(b,a,method='fft');ll=correlation_lags(len(b),len(a));mask=np.abs(ll)<=1600;lag=int(ll[mask][np.argmax(c[mask])]);lags.append({'at':float(t),'lag_ms':lag/16})
    r=subprocess.run([ff,'-hide_banner','-i',str(final),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-vn','-f','null','-'],capture_output=True,text=True);m=re.search(r'\{\s*"input_i".*?\}',r.stderr,re.S);loud=json.loads(m.group())if m else None
    placement=json.loads((work/'placement-qc.json').read_text());passed=width==W and height==H and abs(fps-job['fps'])<.01 and count==job['frames']and not black and placement['pass']and bool(lags)and all(abs(x['lag_ms'])<=10 for x in lags)and loud is not None and abs(float(loud['input_i'])+16)<=1.5 and float(loud['input_tp'])<=-1.0
    report={'machinePass':passed,'width':width,'height':height,'fps':fps,'decodedFrames':count,'blackFrames':black,'sourceLagWindows':lags,'loudness':loud,'allFramePlacementPass':placement['pass'],'sha256':digest(final),'manualInspectionRequired':True,'manualInspectionComplete':False,'warning':'Machine pass does not certify visual/semantic quality. Inspect encoded frames and moving crop/logo placement, then complete the human/agent review checklist.'}
    dump(work/'qc.json',report);print(json.dumps(report,indent=2))
    if not passed:raise ValueError('QC failed; do not deliver')

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ['inspect','transcribe','validate-plan','stills','render']:
        p=sub.add_parser(name);p.add_argument('--input',required=True,type=Path);p.add_argument('--workdir',required=True,type=Path)
        if name in['validate-plan','stills','render']:
            p.add_argument('--plan',required=True,type=Path);p.add_argument('--scene-module',type=Path,help='Optional reviewed job module exporting a Film subclass')
        if name=='transcribe':p.add_argument('--model',default='base');p.add_argument('--language',default='auto')
    p=sub.add_parser('qc');p.add_argument('--workdir',required=True,type=Path);args=ap.parse_args()
    if args.cmd=='inspect':inspect_source(args.input.resolve(),args.workdir.resolve())
    elif args.cmd=='transcribe':transcribe_source(args.input.resolve(),args.workdir.resolve(),args.model,args.language)
    elif args.cmd=='qc':qc(args.workdir.resolve())
    else:
        cls=Film
        if args.scene_module:
            spec=importlib.util.spec_from_file_location('job_scene',args.scene_module.resolve());module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);cls=module.Film
            if not issubclass(cls,Film):raise TypeError('Custom Film must subclass edit.Film to retain source/overlay/QC behavior')
        f=cls(args.input,args.plan)
        try:
            if args.cmd=='validate-plan':print('PLAN_VALID; source binding/timing/fonts checked. Full placements checked during render; manual semantic review required.')
            else:render(f,args.workdir.resolve(),args.cmd=='stills')
        finally:f.close()
if __name__=='__main__':
    sys.modules.setdefault('edit',sys.modules[__name__]);main()
