"""Second, original style interpretation: orange / black / cream editorial.
Uses only the original raw footage, not any reference imagery or audio.

python source/render_editorial_v2.py --stills
python source/render_editorial_v2.py --render
"""
from pathlib import Path
from functools import lru_cache
import argparse, json, math, subprocess, time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edits/voice-agents-editorial-v2'
OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'cache'
CACHE.mkdir(parents=True,exist_ok=True)
FONTS=ROOT/'assets/fonts'
W,H,FPS=1080,1920,30
DURATION=21.37
ORANGE=(251,73,8)
BLACK=(3,3,3)
WHITE=(255,252,244)
CREAM=(237,234,230)
INK=(11,12,12)
GRAY=(153,149,146)
CUTS=[2.98,4.905,7.98,12.54,15.52,18.66]
TRANSCRIPT=json.loads((ROOT/'analysis/transcript.json').read_text())
WORDS=[w for s in TRANSCRIPT['segments'] for w in s['words']]

@lru_cache(maxsize=120)
def font(size,kind='serif',weight=800):
    filename={'serif':'InstrumentSerif-Regular.ttf','italic':'InstrumentSerif-Italic.ttf','sans':'Inter-Variable.ttf'}[kind]
    f=ImageFont.truetype(str(FONTS/filename),int(size))
    if kind=='sans':f.set_variation_by_axes([32,weight])
    return f

def ease(x):
    x=max(0.,min(1.,x));return 1-(1-x)**3

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def lerp(a,b,p):return a+(b-a)*p

def blend_color(a,b,p):return tuple(int(lerp(x,y,p)) for x,y in zip(a,b))

@lru_cache(maxsize=256)
def text_layer(s,size,color=WHITE,kind='serif',weight=800):
    f=font(size,kind,weight)
    bb=f.getbbox(s)
    pad=12
    layer=Image.new('RGBA',(bb[2]-bb[0]+pad*2,bb[3]-bb[1]+pad*2),(0,0,0,0))
    ImageDraw.Draw(layer).text((pad-bb[0],pad-bb[1]),s,font=f,fill=color)
    return layer

def text(im,s,x,y,size,color=WHITE,kind='serif',alpha=1.,align='center',weight=800):
    a=text_layer(s,int(size),tuple(color),kind,weight)
    if alpha<.995:
        a=a.copy();a.putalpha(a.getchannel('A').point(lambda v:int(v*max(0,alpha))))
    xx=x-a.width/2 if align=='center' else x-12
    yy=y-a.height/2
    im.paste(a,(int(xx),int(yy)),a)
    return a.width-24,a.height-24

def tracked(d,xy,s,size=24,color=GRAY,spacing=3,align='left',weight=600):
    f=font(size,'sans',weight)
    width=sum(f.getlength(c)for c in s)+max(0,len(s)-1)*spacing
    x,y=xy
    if align=='center':x-=width/2
    if align=='right':x-=width
    for c in s:
        d.text((x,y),c,font=f,fill=color,anchor='lt');x+=f.getlength(c)+spacing

def fit_size(s,max_size,max_width,kind='sans',weight=800):
    size=max_size
    while size>20 and font(size,kind,weight).getlength(s)>max_width:size-=1
    return size

@lru_cache(maxsize=20)
def mask_round(w,h,r):
    mask=Image.new('L',(w,h),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=r,fill=255)
    return mask

@lru_cache(maxsize=12)
def mask_circle(d):
    # Supersample the curved edge for a clean 1080p cutout.
    a=Image.new('L',(d*2,d*2),0)
    ImageDraw.Draw(a).ellipse((0,0,d*2-1,d*2-1),fill=255)
    return a.resize((d,d),Image.Resampling.LANCZOS)

class Source:
    def __init__(self):
        self.cap=cv2.VideoCapture(str(ROOT/'assets/raw.mp4'))
        self.fps=self.cap.get(cv2.CAP_PROP_FPS);self.last=-1;self.frame=None
    def get(self,t):
        idx=min(619,max(0,int(min(t,20.665)*self.fps)))
        if idx==self.last:return self.frame.copy()
        if idx!=self.last+1:self.cap.set(cv2.CAP_PROP_POS_FRAMES,idx)
        ok,a=self.cap.read()
        if not ok:
            if self.frame is not None:return self.frame.copy()
            raise RuntimeError('Cannot decode source')
        a=cv2.cvtColor(a,cv2.COLOR_BGR2RGB)
        # Editorial variant keeps a softer, almost-original colour response.
        a=np.clip((a.astype(np.float32)-5)*1.015+5,0,255).astype(np.uint8)
        self.frame=a;self.last=idx
        return a.copy()
    def close(self):self.cap.release()


def panel(im,raw,x,y,w,h=None,radius=0,zoom=1.):
    if h is None:h=round(w*raw.shape[0]/raw.shape[1])
    rw,rh=raw.shape[1],raw.shape[0]
    cw=rw/zoom;ch=rh/zoom
    crop=raw[int((rh-ch)/2):int((rh+ch)/2),int((rw-cw)/2):int((rw+cw)/2)]
    scale=min(w/crop.shape[1],h/crop.shape[0])
    nw,nh=round(crop.shape[1]*scale),round(crop.shape[0]*scale)
    p=Image.new('RGB',(w,h),BLACK)
    image=Image.fromarray(cv2.resize(crop,(nw,nh),interpolation=cv2.INTER_CUBIC))
    p.paste(image,((w-nw)//2,(h-nh)//2))
    if radius:im.paste(p,(int(x),int(y)),mask_round(w,h,radius))
    else:im.paste(p,(int(x),int(y)))


def circle_video(im,raw,cx,cy,d,border=None):
    p=Image.new('RGB',(d,d),BLACK)
    nh=round(d*9/16)
    a=Image.fromarray(cv2.resize(raw,(d,nh),interpolation=cv2.INTER_CUBIC))
    p.paste(a,(0,(d-nh)//2))
    im.paste(p,(int(cx-d/2),int(cy-d/2)),mask_circle(d))
    if border:
        ImageDraw.Draw(im).ellipse((cx-d/2,cy-d/2,cx+d/2,cy+d/2),outline=border,width=3)


def make_grid():
    rng=np.random.default_rng(318)
    noise=rng.normal(0,.65,(H,W,1))
    a=np.clip(np.array(CREAM)[None,None,:]+noise,0,255).astype(np.uint8)
    im=Image.fromarray(a);d=ImageDraw.Draw(im)
    for x in range(-12,W,34):
        c=(205,201,199) if (x+12)%170 else (191,187,185)
        d.line([(x,0),(x,H)],fill=c,width=1)
    for y in range(-12,H,34):
        c=(205,201,199) if (y+12)%170 else (191,187,185)
        d.line([(0,y),(W,y)],fill=c,width=1)
    return im

GRID=make_grid()
INTRO_BASE=Image.new('RGB',(W,H),BLACK)
yy=np.arange(280)[:,None,None]
a=np.broadcast_to(np.array(ORANGE)[None,None,:]*.70*np.exp(-yy/53),(280,W,3)).astype(np.uint8)
INTRO_BASE.paste(Image.fromarray(a),(0,0))

# Normal serif captions are composed from the complete actual word transcript.
CAPTION_GROUPS=[]
current=[]
for w in WORDS:
    if current and (w['start']-current[-1]['end']>.38 or len(current)>=5 or w['end']-current[0]['start']>1.45):
        CAPTION_GROUPS.append(current);current=[]
    current.append(w)
    if w['word'].endswith(('.',',','?','!')) and len(current)>=2:
        CAPTION_GROUPS.append(current);current=[]
if current:CAPTION_GROUPS.append(current)


def captions(im,t,y=1450,size=54,max_width=900,color=WHITE):
    idx=None
    for i,c in enumerate(CAPTION_GROUPS):
        next_start=CAPTION_GROUPS[i+1][0]['start'] if i+1<len(CAPTION_GROUPS) else c[-1]['end']+.18
        end=min(next_start,c[-1]['end']+.38)
        if c[0]['start']<=t<end:idx=i;break
    if idx is None:return
    c=CAPTION_GROUPS[idx]
    full=' '.join(w['word']for w in c)
    fs=fit_size(full,size,max_width,'serif')
    f=font(fs,'serif')
    total=f.getlength(full);x=(W-total)/2
    d=ImageDraw.Draw(im)
    last_right=None
    for w in c:
        ww=f.getlength(w['word'])
        if t>=w['start']:
            # Fixed word slots prevent the caption from recentering at every syllable.
            p=ease((t-w['start'])/.065)
            text(im,w['word'],x,y+3*(1-p),fs,color,'serif',alpha=p,align='left')
            last_right=x+ww
        x+=ww+f.getlength(' ')
    if last_right is not None:
        d.rectangle((last_right+5,y-fs*.31,last_right+8,y+fs*.36),fill=ORANGE if color==WHITE else WHITE)


def opening(im,raw,t):
    p=ease(t/.25)
    d=ImageDraw.Draw(im)
    text(im,'THE STARTUP',540,239+16*(1-p),59,WHITE,'italic',alpha=p)
    fs=fit_size('PLAYBOOK',157,920,'sans')
    text(im,'PLAYBOOK',540,369+18*(1-p),fs,WHITE,'sans',alpha=p)
    text(im,'Going Global',540,514+15*(1-p),132,ORANGE,'italic',alpha=p)
    panel(im,raw,0,697,1080,608,zoom=1.+.008*min(t,2.98))
    captions(im,t,1495,56)
    # Small editorial baseline gives the black layout a deliberate finish.
    d.line([(476,1675),(604,1675)],fill=ORANGE,width=3)


def years_card(im,raw,t):
    p=ease((t-2.98)/.18)
    d=ImageDraw.Draw(im)
    tracked(d,(540,545),'MANY',30,WHITE,7,'center')
    text(im,'Years',540,823+15*(1-p),330,WHITE,'italic',alpha=p)
    if t>=3.52:
        pp=ease((t-3.52)/.16)
        text(im,'before they go',540,1089+10*(1-pp),78,WHITE,'italic',alpha=pp)
    if t>=4.12:
        pp=ease((t-4.12)/.14)
        text(im,'international',540,1183+10*(1-pp),91,WHITE,'italic',alpha=pp)
    d.line([(476,1475),(604,1475)],fill=WHITE,width=2)
    tracked(d,(540,1551),'THE LONG WAY',25,WHITE,3,'center',500)


def interview_effort(im,raw,t):
    text(im,'Going global',540,313,103,WHITE,'italic')
    if t>=5.68:
        p=ease((t-5.68)/.2)
        text(im,'takes effort.',540,431+10*(1-p),116,ORANGE,'italic',alpha=p)
    panel(im,raw,0,686,1080,608,zoom=1.+.007*math.sin(t*.8)**2)
    captions(im,t,1492,56)
    d=ImageDraw.Draw(im)
    d.line([(476,1675),(604,1675)],fill=ORANGE,width=3)

# Verbatim words, laid out as a quote and revealed at their own speech timestamps.
QUOTE_WORDS=[w for w in WORDS if 7.98-.001<=w['start']<11.93]
QUOTE_COUNTS=[3,2,2,3,2,1,3,4]
QUOTE_LAYOUT=[]
qi=0
for count in QUOTE_COUNTS:
    QUOTE_LAYOUT.append(QUOTE_WORDS[qi:qi+count]);qi+=count
assert qi==len(QUOTE_WORDS),(qi,len(QUOTE_WORDS))


def quote_plate(im,raw,t):
    d=ImageDraw.Draw(im)
    reveal=ease((t-7.98)/.2)
    d.rectangle((92,145,104,145+100*reveal),fill=ORANGE)
    tracked(d,(133,172),'THE SHIFT',25,(97,91,86),3)
    fs=88
    f=font(fs,'sans',800)
    left=85;top=330;lineheight=105
    for row,words in enumerate(QUOTE_LAYOUT):
        x=left;y=top+row*lineheight
        for j,w in enumerate(words):
            s=w['word'].upper().replace("'",'’')
            if row==0 and j==0:s='“'+s
            if row==len(QUOTE_LAYOUT)-1 and j==len(words)-1:s=s+'”'
            if t>=w['start']:
                p=ease((t-w['start'])/.07)
                text(im,s,x,y+4*(1-p),fs,INK,'sans',alpha=p,align='left')
            x+=f.getlength(s+' ')
    # Both real speakers remain visible, with the actual audio/video clock unchanged.
    circle_video(im,raw,540,1530,520)
    text(im,'Global, early.',540,1202,54,(91,86,81),'italic')


def waveform(d,cx,cy,width,height,t,col,bars=65):
    for i in range(bars):
        x=cx-width/2+width*i/(bars-1)
        h=height*(.15+.75*abs(math.sin(i*.67+t*2.8))*abs(math.sin(i*.11+t*.3)))
        d.rounded_rectangle((x-3,cy-h,x+3,cy+h),radius=3,fill=col)


def product_layout(im,raw,t):
    d=ImageDraw.Draw(im)
    p=ease((t-12.54)/.25)
    y=int(127+20*(1-p))
    d.rounded_rectangle((60,y,1020,y+687),radius=40,fill=BLACK)
    d.rounded_rectangle((60,875,1020,1695),radius=40,fill=BLACK)
    tracked(d,(108,y+52),'VOICE AI',27,WHITE,4)
    tracked(d,(970,y+56),'CONCEPT',19,(117,113,109),2,'right',500)
    waveform(d,540,y+265,680,82,t,ORANGE,61)
    # Product-to-market concept rather than unrelated stock footage.
    text(im,'Product',309,y+464,100,WHITE,'italic')
    text(im,'Market',786,y+464,100,WHITE,'italic')
    q=ease((t-13.38)/.6)
    d.line([(472,y+468),(472+125*q,y+468)],fill=ORANGE,width=4)
    if q>.85:d.line([(585,y+457),(600,y+468),(585,y+479)],fill=ORANGE,width=4)
    for x in [310,786]:d.ellipse((x-5,y+571,x+5,y+581),fill=ORANGE)
    d.line([(320,y+576),(776,y+576)],fill=(77,38,19),width=1)
    panel(im,raw,60,926,960,540)
    captions(im,t,1567,52,870)


def icon(d,kind,cx,cy,r,col=INK):
    line=6
    if kind=='people':
        d.ellipse((cx-r*.25,cy-r*.64,cx+r*.25,cy-r*.14),outline=col,width=line)
        d.arc((cx-r*.52,cy-r*.07,cx+r*.52,cy+r*.91),180,358,fill=col,width=line)
        for side in [-1,1]:
            xx=cx+side*r*.65
            d.ellipse((xx-r*.15,cy-r*.42,xx+r*.15,cy-r*.12),outline=ORANGE,width=5)
            d.arc((xx-r*.28,cy+r*.02,xx+r*.28,cy+r*.59),180,358,fill=ORANGE,width=5)
    elif kind=='businesses':
        d.rounded_rectangle((cx-r*.57,cy-r*.75,cx+r*.57,cy+r*.73),radius=10,outline=col,width=line)
        for row in range(3):
            for column in range(2):
                x=cx-r*.30+column*r*.49;y=cy-r*.47+row*r*.37
                d.rectangle((x-10,y-10,x+10,y+10),fill=ORANGE)
        d.rectangle((cx-r*.13,cy+r*.37,cx+r*.13,cy+r*.73),outline=col,width=5)
        d.line([(cx-r*.79,cy+r*.75),(cx+r*.79,cy+r*.75)],fill=col,width=5)
    elif kind=='developers':
        d.rounded_rectangle((cx-r*.93,cy-r*.65,cx+r*.93,cy+r*.68),radius=17,outline=col,width=line)
        d.line([(cx-r*.92,cy-r*.35),(cx+r*.92,cy-r*.35)],fill=col,width=4)
        for k in range(3):d.ellipse((cx-r*.71+k*22,cy-r*.52-4,cx-r*.71+k*22+8,cy-r*.52+4),fill=ORANGE)
        d.line([(cx-r*.26,cy-r*.08),(cx-r*.58,cy+r*.13),(cx-r*.26,cy+r*.34)],fill=col,width=7)
        d.line([(cx+r*.26,cy-r*.08),(cx+r*.58,cy+r*.13),(cx+r*.26,cy+r*.34)],fill=col,width=7)
        d.line([(cx+r*.10,cy-r*.08),(cx-r*.10,cy+r*.37)],fill=ORANGE,width=7)
    else:
        d.line([(cx-r*.88,cy-r*.33),(cx,cy-r*.82),(cx+r*.88,cy-r*.33),(cx-r*.88,cy-r*.33)],fill=col,width=line)
        for dx in [-.58,0,.58]:
            d.line([(cx+r*dx,cy-r*.15),(cx+r*dx,cy+r*.61)],fill=col,width=7)
        d.line([(cx-r*.89,cy+r*.76),(cx+r*.89,cy+r*.76)],fill=ORANGE,width=7)
        d.line([(cx-r*.96,cy+r*.90),(cx+r*.96,cy+r*.90)],fill=col,width=5)

AUDIENCES=[('PEOPLE','people',15.52),('BUSINESSES','businesses',16.6),('DEVELOPERS','developers',17.38),('GOVERNMENTS','governments',18.34)]

@lru_cache(maxsize=8)
def vertical_word(word):
    fs=fit_size(word,100,500,'sans')
    a=text_layer(word,fs,WHITE,'sans')
    return a.rotate(-90,expand=True,resample=Image.Resampling.BICUBIC)


def audience_layout(im,raw,t):
    text(im,'Built for',540,201,115,WHITE,'italic')
    panel(im,raw,0,372,1080,608)
    captions(im,t,1070,54)
    active=0
    for i,item in enumerate(AUDIENCES):
        if t>=item[2]:active=i
    word,kind,at=AUDIENCES[active]
    p=ease((t-at)/.18)
    top=int(1184+19*(1-p))
    d=ImageDraw.Draw(im)
    # Slight card shadow and a warm paper insert, not a copied photo from the reference.
    d.rounded_rectangle((93,top+9,897,top+525),radius=39,fill=(20,17,15))
    d.rounded_rectangle((84,top,888,top+516),radius=35,fill=CREAM)
    tracked(d,(126,top+34),f'0{active+1}',22,(107,98,91),3)
    d.rectangle((829,top+35,845,top+51),fill=ORANGE)
    icon(d,kind,486,top+238,136)
    tracked(d,(486,top+425),word,25,INK,3,'center')
    d.line([(410,top+473),(562,top+473)],fill=ORANGE,width=3)
    v=vertical_word(word)
    im.paste(v,(912,1168),v)
    d.rectangle((948,1115,966,1133),fill=ORANGE)


def payoff(im,raw,t):
    d=ImageDraw.Draw(im)
    tracked(d,(540,205),'BUILD GREAT',30,WHITE,5,'center')
    circle_video(im,raw,540,597,526)
    if t<19.74:
        p=ease((t-18.66)/.25)
        text(im,'Build great',540,1165+15*(1-p),180,WHITE,'italic',alpha=p)
    else:
        p=ease((t-19.74)/.15)
        text(im,'Voice',540,1102+18*(1-p),264,WHITE,'italic',alpha=p)
        if t>=20.02:
            q=ease((t-20.02)/.18)
            text(im,'Agents',540,1352+18*(1-q),278,WHITE,'italic',alpha=q)
    if t>20.1:
        q=ease((t-20.1)/.25)
        d.line([(540-298*q,1532),(540+298*q,1532)],fill=WHITE,width=2)
        waveform(d,540,1610,620,32,t,WHITE,53)
        text(im,'Voice AI, for everyone.',540,1690,47,WHITE,'italic',alpha=q)


def _scene_at(t):
    if t<2.98:return 'opening'
    if t<4.905:return 'years'
    if t<7.98:return 'effort'
    if t<12.54:return 'quote'
    if t<15.52:return 'product'
    if t<18.66:return 'audience'
    return 'payoff'


def compose(raw,t,forced=None):
    scene=forced or _scene_at(t)
    if scene=='opening':im=INTRO_BASE.copy();opening(im,raw,t)
    elif scene=='years':im=Image.new('RGB',(W,H),ORANGE);years_card(im,raw,t)
    elif scene=='effort':im=Image.new('RGB',(W,H),BLACK);interview_effort(im,raw,t)
    elif scene=='quote':im=GRID.copy();quote_plate(im,raw,t)
    elif scene=='product':im=Image.new('RGB',(W,H),ORANGE);product_layout(im,raw,t)
    elif scene=='audience':im=Image.new('RGB',(W,H),BLACK);audience_layout(im,raw,t)
    else:im=Image.new('RGB',(W,H),ORANGE);payoff(im,raw,t)
    return im


def render_frame(src,t):
    raw=src.get(t)
    im=compose(raw,t)
    # Short connected editorial reveals, not impact flashes or sports shakes.
    recent=next((cut for cut in CUTS if 0<=t-cut<.14),None)
    if recent is not None:
        old_t=recent-.015
        old=compose(raw,old_t)
        p=ease((t-recent)/.14)
        if recent in [2.98,12.54,18.66]:
            edge=int(W*p)
            old.paste(im.crop((0,0,edge,H)),(0,0));im=old
        else:
            im=Image.blend(old,im,p)
    return im


def stills():
    src=Source()
    times=[.80,2.1,3.70,5.90,8.70,10.55,12.18,13.90,15.85,16.95,17.64,18.45,19.25,20.42]
    tw,th=270,480;cols=7
    sheet=Image.new('RGB',(tw*cols,(th+30)*2),(27,27,27));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        a=render_frame(src,t)
        a.save(ROOT/f'analysis/editorial-v2-frame-{i:02d}.jpg',quality=93)
        x=(i%cols)*tw;y=(i//cols)*(th+30)
        sheet.paste(a.resize((tw,th),Image.Resampling.LANCZOS),(x,y))
        d.text((x+8,y+th+7),f'{t:.2f}s',font=font(18,'sans',500),fill=WHITE)
    sheet.save(ROOT/'analysis/editorial-v2-contact.jpg',quality=95)
    render_frame(src,20.50).save(OUT/'poster.jpg',quality=95)
    src.close();print('EDITORIAL_STILLS_COMPLETE',flush=True)


def render():
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ff,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(CACHE/'visuals-editorial-v2.mp4')]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    src=Source();total=round(DURATION*FPS);start=time.monotonic()
    try:
        for i in range(total):
            a=render_frame(src,i/FPS)
            p.stdin.write(a.tobytes())
            if i%90==0:print(f'Editorial render {i}/{total} frames; {time.monotonic()-start:.1f}s',flush=True)
    finally:
        if p.stdin:p.stdin.close()
        src.close()
    if p.wait()!=0:raise RuntimeError('Editorial render encode failed')
    print('EDITORIAL_VISUAL_RENDER_COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stills',action='store_true');parser.add_argument('--render',action='store_true');args=parser.parse_args()
    if args.stills:stills()
    if args.render:render()
