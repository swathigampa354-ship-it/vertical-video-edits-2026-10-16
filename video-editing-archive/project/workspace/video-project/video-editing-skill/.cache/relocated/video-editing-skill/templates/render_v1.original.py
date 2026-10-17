"""Original, speech-led 9:16 motion edit. No reference footage/audio is used.

Run from video-project: python source/render.py --stills
                       python source/render.py --render
"""
from pathlib import Path
from functools import lru_cache
import argparse, bisect, json, math, subprocess, sys, time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'edits/voice-agents-9x16'
OUT.mkdir(parents=True, exist_ok=True)
FONTS = ROOT / 'assets/fonts'
W,H,FPS = 1080,1920,30
DURATION = 21.37
SOURCE_END = 20.687
CUT = 4.9049
WHITE=(250,249,242)
LIME=(207,255,70)
RED=(255,63,75)
GRAY=(151,155,153)
DARK=(8,10,11)
HITS=[1.58,2.98,4.905,8.44,11.04,13.68,15.52,16.6,17.38,18.34,19.74,20.02]
FLASHES=[1.58,4.905,8.44,13.68,19.74]

@lru_cache(maxsize=96)
def font(size, kind='heavy'):
    filename={'heavy':'BarlowCondensed-BlackItalic.ttf','semi':'BarlowCondensed-SemiBold.ttf','body':'Barlow-Medium.ttf'}[kind]
    return ImageFont.truetype(str(FONTS/filename),int(size))

def ease(x):
    x=max(0.,min(1.,x));return 1-(1-x)**3

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def mix(a,b,x):
    return tuple(int(u*(1-x)+v*x) for u,v in zip(a,b))

def accent(t):
    return mix(RED,LIME,smooth((t-8.35)/.20))

def pulse(t, times=HITS, decay=.14):
    return max([math.exp(-(t-hit)/decay) for hit in times if 0<=t-hit<.65]+[0.])

def tracked(draw, xy, text, size=27, color=GRAY, spacing=3, kind='body', anchor='left'):
    f=font(size,kind)
    width=sum(f.getlength(c) for c in text)+max(0,len(text)-1)*spacing
    x,y=xy
    if anchor=='center':x-=width/2
    elif anchor=='right':x-=width
    for c in text:
        draw.text((x,y),c,font=f,fill=color,anchor='lt')
        x+=f.getlength(c)+spacing

@lru_cache(maxsize=160)
def text_asset(text,size,color=WHITE,kind='heavy',stroke=5,glow=False):
    f=font(size,kind)
    bb=f.getbbox(text,stroke_width=stroke)
    pad=22 if glow else 13
    tw=bb[2]-bb[0]+pad*2;th=bb[3]-bb[1]+pad*2
    xy=(pad-bb[0],pad-bb[1])
    layer=Image.new('RGBA',(tw,th),(0,0,0,0))
    sd=ImageDraw.Draw(layer)
    sd.text((xy[0]+2,xy[1]+7),text,font=f,fill=(0,0,0,230),stroke_width=stroke+2,stroke_fill=(0,0,0,230))
    layer=layer.filter(ImageFilter.GaussianBlur(3))
    if glow:
        g=Image.new('RGBA',(tw,th),(0,0,0,0));gd=ImageDraw.Draw(g)
        gd.text(xy,text,font=f,fill=(*color,110),stroke_width=stroke,stroke_fill=(*color,90))
        g=g.filter(ImageFilter.GaussianBlur(10))
        layer=Image.alpha_composite(layer,g)
    d=ImageDraw.Draw(layer)
    d.text(xy,text,font=f,fill=(*color,255),stroke_width=stroke,stroke_fill=(6,7,8,245))
    return layer

def text(im,text,center,y,size=110,color=WHITE,kind='heavy',scale=1.,alpha=1.,stroke=5,glow=False):
    a=text_asset(text,int(size),tuple(color),kind,stroke,glow)
    if abs(scale-1)>.008:
        a=a.resize((max(1,int(a.width*scale)),max(1,int(a.height*scale))),Image.Resampling.LANCZOS)
    if alpha<.998:
        a=a.copy();a.putalpha(a.getchannel('A').point(lambda p:int(p*max(0,alpha))))
    im.paste(a,(int(center-a.width/2),int(y-a.height/2)),a)


def make_base():
    yy,xx=np.mgrid[0:H,0:W]
    rad=np.clip(1-np.sqrt(((xx-470)/920)**2+((yy-800)/1600)**2),0,1)
    arr=np.zeros((H,W,3),np.uint8)
    for k,v in enumerate([9,12,14]):arr[:,:,k]=v+(rad*8).astype(np.uint8)
    im=Image.fromarray(arr)
    d=ImageDraw.Draw(im)
    for x in range(0,W,90):d.line([(x,0),(x,H)],fill=(20,23,25),width=1)
    for y in range(0,H,90):d.line([(0,y),(W,y)],fill=(20,23,25),width=1)
    return im

BASE=make_base()
# The source panel fades into the original graphic world, instead of ending in a hard edge.
_yy=np.arange(H)[:,None]
_alpha=np.clip((_yy-1000)/440,0,1)*.98
_bottom=np.zeros((H,W,4),dtype=np.uint8)
_bottom[:,:,:3]=np.array(DARK,dtype=np.uint8)
_bottom[:,:,3]=np.broadcast_to((_alpha*255).astype(np.uint8),(H,W))
BOTTOM=Image.fromarray(_bottom,'RGBA')
_top=np.zeros((240,W,4),np.uint8)
_top[:,:,:3]=DARK
_top[:,:,3]=np.broadcast_to((np.linspace(235,0,240)[:,None]).astype(np.uint8),(240,W))
TOP=Image.fromarray(_top,'RGBA')

class Source:
    def __init__(self):
        self.cap=cv2.VideoCapture(str(ROOT/'assets/raw.mp4'))
        self.fps=self.cap.get(cv2.CAP_PROP_FPS)
        self.last_index=-1;self.last_frame=None
    def get(self,t):
        i=min(619,max(0,int(min(SOURCE_END-.02,t)*self.fps)))
        if i==self.last_index:return self.last_frame.copy()
        if i!=self.last_index+1:self.cap.set(cv2.CAP_PROP_POS_FRAMES,i)
        ok,f=self.cap.read()
        if not ok:
            if self.last_frame is not None:return self.last_frame.copy()
            raise RuntimeError('Cannot decode source frame')
        f=cv2.cvtColor(f,cv2.COLOR_BGR2RGB)
        # Modest grade: warm highlights, deeper blacks, no generative face changes.
        a=f.astype(np.float32)/255
        lum=a[:,:,0]*.213+a[:,:,1]*.715+a[:,:,2]*.072
        a=lum[:,:,None]+(a-lum[:,:,None])*1.09
        a=(a-.08)*1.07+.065
        a[:,:,0]*=1.015;a[:,:,2]*=.985
        f=np.clip(a*255,0,255).astype(np.uint8)
        self.last_frame=f;self.last_index=i
        return f.copy()
    def close(self):self.cap.release()


def crop_resize(arr,box,out_size):
    x0,y0,x1,y1=box
    x0=max(0,int(x0));y0=max(0,int(y0));x1=min(arr.shape[1],int(x1));y1=min(arr.shape[0],int(y1))
    return cv2.resize(arr[y0:y1,x0:x1],out_size,interpolation=cv2.INTER_CUBIC)


def scene_video(im,raw,t):
    hit=pulse(t)
    # The first establishing shot is intact; then crop the actual speaker, never fake a speaking frame.
    if t<1.58:
        p=ease(t/.5)
        scale=1.00+.025*t/1.58
        cw=640/scale;ch=360/scale
        ar=crop_resize(raw,((640-cw)/2,(360-ch)/2,(640+cw)/2,(360+ch)/2),(1080,608))
        panel=Image.fromarray(ar)
        im.paste(panel,(0,int(596-18*p)))
        d=ImageDraw.Draw(im)
        d.line([(68,579),(1012,579)],fill=(*RED,),width=3)
        d.line([(68,1185),(1012,1185)],fill=(68,41,43),width=2)
        return
    zoom=1.01+.025*math.sin(t*.7)**2+.068*hit
    if 10.9<t<11.98:zoom+=.025
    cx=158 if t<CUT else 160
    if t<CUT:cx=151
    # A brief, synchronous listener cutaway in the natural speech pause.
    if 11.98<=t<12.54:cx=480
    cw=320/zoom;ch=360/zoom
    cy=178
    cx+=2.8*math.sin(t*.72)
    crop=crop_resize(raw,(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2),(1080,1215))
    panel=Image.fromarray(crop)
    dx=int(7*hit*math.sin((t%1)*116))
    dy=int(5*hit*math.cos((t%1)*132))
    if hit>.4:
        panel=panel.filter(ImageFilter.GaussianBlur(.35*hit))
    im.paste(panel,(dx,150+dy))
    # A light side vignette keeps the face intact and separates it from typography.
    im.paste(BOTTOM,(0,0),BOTTOM)


def globe(d,cx,cy,r,col,t,opacity=1.):
    c=tuple(int(x*opacity) for x in col)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=c,width=3)
    d.arc((cx-r,cy-r*.48,cx+r,cy+r*.48),0,360,fill=c,width=2)
    d.line([(cx-r,cy),(cx+r,cy)],fill=c,width=2)
    for phase in [t*.30,t*.30+1.05,t*.30+2.10]:
        width=abs(math.cos(phase))*r
        if width>4:d.ellipse((cx-width,cy-r,cx+width,cy+r),outline=c,width=2)


def glow_line(d,points,col,width=3):
    dim=tuple(int(c*.25) for c in col)
    d.line(points,fill=dim,width=width+7,joint='curve')
    d.line(points,fill=col,width=width,joint='curve')


def diagram_wait(im,t):
    d=ImageDraw.Draw(im)
    col=accent(t)
    y=1544
    tracked(d,(540,1440),'THE LONG WAY',26,(169,146,146),3,anchor='center')
    # Local starting point and international destination remain connected across the red/lime shift.
    d.ellipse((137,y-13,163,y+13),fill=RED)
    progress=min(1.,max(.05,(t-.4)/4.0))
    for x in range(180,850,22):
        c=(74,51,54) if (x-180)/670>progress else (171,56,64)
        d.line([(x,y),(x+10,y)],fill=c,width=4)
    for i in range(3):
        x=350+i*145
        if t>2.3+i*.25:
            v=ease((t-(2.3+i*.25))/.25)
            d.rounded_rectangle((x-6,y-16*v,x+6,y+16*v),radius=5,fill=RED)
    globe(d,922,y,48,RED,t)
    tracked(d,(150,1621),'STARTUP',26,WHITE,2,anchor='center')
    tracked(d,(925,1621),'GLOBAL',26,WHITE,2,anchor='center')
    text(im,'YEARS',540,1636,65,RED,kind='semi',stroke=0)


def diagram_early(im,t):
    d=ImageDraw.Draw(im)
    p=ease((t-8.44)/.55)
    col=accent(t)
    tracked(d,(540,1426),'A DIFFERENT PLAYBOOK',25,GRAY,3,anchor='center')
    cy=1556
    # Move the same destination globe inward before expanding the network.
    transition=ease((t-7.52)/.72)
    gcx=922+(540-922)*transition
    gcy=1544+(cy-1544)*transition
    gr=48+(75-48)*transition
    globe(d,gcx,gcy,gr,col,t)
    if transition<.99:
        fade=1-transition
        for x in range(180,int(gcx-gr-12),22):
            d.line([(x,1544),(x+10,1544)],fill=tuple(int(c*fade) for c in (171,56,64)),width=3)
    nodes=[(255,1510),(827,1500),(224,1632),(853,1632)]
    for i,(x,y) in enumerate(nodes):
        v=ease((t-8.44-i*.10)/.5)
        end=(540+(x-540)*v,cy+(y-cy)*v)
        glow_line(d,[(540,cy),end],mix((37,43,38),col,v),2)
        if v>.1:
            r=9+2*math.sin(t*3+i)
            d.ellipse((end[0]-r,end[1]-r,end[0]+r,end[1]+r),fill=col)
    text(im,'GLOBAL, EARLY.',540,1693,61,col,kind='semi',stroke=0)


def product_market(im,t):
    d=ImageDraw.Draw(im)
    p=ease((t-12.54)/.7)
    tracked(d,(540,1424),'BUILD IT. BRING IT.',25,GRAY,3,anchor='center')
    x1,x2=540+(268-540)*p,540+(812-540)*p;y=1565
    for x,word in [(x1,'PRODUCT'),(x2,'MARKET')]:
        hw=75+93*p
        d.rounded_rectangle((x-hw,y-75,x+hw,y+75),radius=int(58-35*p),fill=(21,26,22),outline=(66,80,48),width=2)
        if p>.1:text(im,word,x,y,int(32+26*p),LIME,kind='semi',stroke=0,alpha=p)
    if p<.9:globe(d,540,y,75*(1-p),LIME,t,opacity=1-p)
    if p>.73:glow_line(d,[(x1+183,y),(x1+183+(x2-x1-366)*p,y)],LIME,4)
    if p>.90:
        tip=x2-183
        d.line([(tip-14,y-10),(tip,y),(tip-14,y+10)],fill=LIME,width=4)
    # Four short stems anticipate the recipient cards instead of an unrelated cut.
    q=ease((t-15.0)/.5)
    for k in range(4):
        x=330+k*140
        d.line([(540,1643),(540+(x-540)*q,1643+53*q)],fill=(60,73,43),width=2)


def icon(d,kind,cx,cy,r,col):
    if kind=='people':
        d.ellipse((cx-r*.28,cy-r*.67,cx+r*.28,cy-r*.1),outline=col,width=3)
        d.arc((cx-r*.55,cy-r*.12,cx+r*.55,cy+r*.75),180,360,fill=col,width=3)
    elif kind=='businesses':
        d.rounded_rectangle((cx-r*.65,cy-r*.28,cx+r*.65,cy+r*.55),radius=5,outline=col,width=3)
        d.rectangle((cx-r*.28,cy-r*.52,cx+r*.28,cy-r*.28),outline=col,width=3)
        d.line([(cx-r*.6,cy+.02*r),(cx+r*.6,cy+.02*r)],fill=col,width=2)
    elif kind=='developers':
        d.line([(cx-r*.24,cy-r*.42),(cx-r*.68,cy),(cx-r*.24,cy+r*.42)],fill=col,width=3)
        d.line([(cx+r*.24,cy-r*.42),(cx+r*.68,cy),(cx+r*.24,cy+r*.42)],fill=col,width=3)
        d.line([(cx+r*.12,cy-r*.6),(cx-r*.12,cy+r*.6)],fill=col,width=3)
    else:
        d.line([(cx-r*.7,cy-r*.3),(cx,cy-r*.7),(cx+r*.7,cy-r*.3),(cx-r*.7,cy-r*.3)],fill=col,width=3)
        for dx in [-.45,0,.45]:d.line([(cx+r*dx,cy-r*.22),(cx+r*dx,cy+r*.5)],fill=col,width=3)
        d.line([(cx-r*.7,cy+r*.6),(cx+r*.7,cy+r*.6)],fill=col,width=3)

AUDIENCES=[('PEOPLE','people',15.52,300,1509),('BUSINESSES','businesses',16.60,780,1509),('DEVELOPERS','developers',17.38,300,1645),('GOVERNMENTS','governments',18.34,780,1645)]

def audience_cards(im,t):
    d=ImageDraw.Draw(im)
    tracked(d,(540,1380),'BUILT FOR',24,GRAY,3,anchor='center')
    for label,kind,at,cx,cy in AUDIENCES:
        p=ease((t-at)/.24)
        c=mix((50,59,49),LIME,p)
        if p<.001:
            fill=(16,20,19);stroke=(39,45,40);fg=(79,86,80)
        else:
            fill=mix((18,23,20),(30,40,21),p);stroke=mix((43,52,40),(118,149,54),p);fg=c
        offset=(1-p)*18
        y=cy+offset
        d.rounded_rectangle((cx-211,y-56,cx+211,y+56),radius=20,fill=fill,outline=stroke,width=2)
        icon(d,kind,cx-153,y,32,fg)
        text(im,label,cx+22,y,48,fg,kind='semi',stroke=0)
        if 0<t-at<.26:
            d.rounded_rectangle((cx-211,y-56,cx+211,y+56),radius=20,outline=LIME,width=3)


def final_graphic(im,t):
    d=ImageDraw.Draw(im)
    q=ease((t-18.66)/.62)
    # Recipient nodes visibly converge into a common voice system.
    for _,kind,at,cx,cy in AUDIENCES:
        nx=cx+(540-cx)*q;ny=cy+(1515-cy)*q
        if q<.99:
            glow_line(d,[(cx,cy),(nx,ny)],mix((72,88,46),LIME,q),2)
            d.ellipse((nx-8,ny-8,nx+8,ny+8),fill=LIME)
    if t<19.74:
        tracked(d,(540,1450),'ONE CONNECTED SYSTEM',25,GRAY,3,anchor='center')
        # Building waveform, not an invented product interface.
        for i in range(35):
            x=202+i*20
            hh=(12+46*abs(math.sin(i*.74+t*3.2)))*q
            d.rounded_rectangle((x-4,1566-hh,x+4,1566+hh),radius=4,fill=LIME)
        return
    p=ease((t-19.74)/.20)
    text(im,'VOICE',540,1376+20*(1-p),213,WHITE,scale=1+.035*pulse(t,[19.74],.11),glow=False)
    p2=ease((t-20.02)/.22)
    if p2>0:
        text(im,'AGENTS',540,1561+22*(1-p2),226,LIME,scale=1+.04*pulse(t,[20.02],.1),alpha=p2,glow=True)
    for i in range(39):
        x=237+i*16
        decay=1. if t<20.5 else max(.25,1-(t-20.5)*.6)
        hh=(6+15*abs(math.sin(i*.71+t*3.2)))*decay
        d.rounded_rectangle((x-3,1720-hh,x+3,1720+hh),radius=3,fill=mix((57,71,35),LIME,.75))

# Essential on-screen phrases, anchored to the actual spoken words.
PHRASES=[
 (0.00,1.58,['A LOT OF','COMPANIES'],108),
 (1.58,2.26,['STARTUPS'],157),
 (2.26,3.52,['SPEND MANY','YEARS'],131),
 (3.52,4.94,['BEFORE THEY GO','INTERNATIONAL'],106),
 (4.94,5.68,['BECAUSE,','YOU KNOW'],108),
 (5.68,6.70,['IT TAKES','A LOT OF'],123),
 (6.70,7.52,['EFFORT','TO DO THAT'],129),
 (7.52,8.44,['FOR US'],155),
 (8.44,9.28,['EARLY ON'],168),
 (9.28,10.22,['REALIZED'],157),
 (10.22,10.96,['SUPER','IMPORTANT'],139),
 (10.96,11.62,['WE INVESTED','A LOT'],133),
 (11.62,12.54,['IN THAT'],146),
 (12.54,13.68,['BRING THIS'],143),
 (13.68,14.38,['PRODUCT','TO MARKET'],133),
 (14.38,15.52,["WHAT WE'RE",'TRYING TO DO'],111),
 (15.52,16.60,['HELP PEOPLE'],146),
 (16.60,17.38,['BUSINESSES'],155),
 (17.38,17.90,['DEVELOPERS'],150),
 (17.90,18.66,['AND','GOVERNMENTS'],131),
 (18.66,19.74,['BUILD GREAT'],156),
]
WORDS=[]
for s in json.loads((ROOT/'analysis/transcript.json').read_text())['segments']:
    WORDS.extend(s['words'])

KEYWORDS={'STARTUPS','YEARS','INTERNATIONAL','EFFORT','EARLY','ON','IMPORTANT','INVESTED','PRODUCT','MARKET','PEOPLE','BUSINESSES','DEVELOPERS','GOVERNMENTS','BUILD','GREAT'}

def phrase_type(im,t):
    ph=next((p for p in PHRASES if p[0]<=t<p[1]),None)
    if ph is None:return
    start,end,lines,fs=ph
    enter=ease((t-start)/.12)
    leave=min(1,max(0,(end-t)/.055))
    alpha=min(enter,leave)
    # Each phrase is centered above the diagram strip, away from face and platform UI.
    y=1234 if t<15.52 else 1216
    if len(lines)==1:y+=16
    scale=1.+.038*pulse(t,[start],.10)
    current=next((w['word'].strip('.,!?').upper() for w in WORDS if w['start']<=t<w['end']),None)
    for j,line in enumerate(lines):
        liney=y+(j-(len(lines)-1)/2)*(fs*.91)+18*(1-enter)
        tokens=line.split(' ')
        keyword=any(tok.strip('.,!?') in KEYWORDS for tok in tokens)
        color=accent(t) if keyword else WHITE
        # A whole phrase gets the reference's strong colour coding; active speech gets a tiny scale accent.
        active=any(tok.strip('.,!?')==current for tok in tokens)
        text(im,line,540,liney,fs,color,scale=scale*(1.012 if active else 1),alpha=alpha,glow=keyword and t>=8.44)


def draw_ui(im,t):
    im.paste(TOP,(0,0),TOP)
    d=ImageDraw.Draw(im)
    col=accent(t)
    d.rounded_rectangle((67,110,77,153),radius=4,fill=col)
    tracked(d,(96,111),'VOICE AI',28,WHITE,3)
    stage=0 if t<7.52 else (1 if t<15.52 else 2)
    labels=['THE WAIT','THE SHIFT','THE PAYOFF']
    tracked(d,(1008,111),labels[stage],25,col,2,anchor='right')
    d.line([(70,1746),(1010,1746)],fill=(46,50,46),width=3)
    d.line([(70,1746),(70+940*min(1,t/20.42),1746)],fill=col,width=4)
    tracked(d,(70,1782),'FOUNDER INSIGHT',22,(132,137,132),2)
    tracked(d,(1008,1782),f'{stage+1:02d} / 03',22,(132,137,132),2,anchor='right')


def render_frame(src,t):
    im=BASE.copy()
    raw=src.get(t)
    scene_video(im,raw,t)
    if t<1.58:
        p=ease(t/.32)
        text(im,'GO',540,260+30*(1-p),176,WHITE,alpha=p,stroke=5)
        text(im,'GLOBAL?',540,427+25*(1-p),192,RED,alpha=p,stroke=5,glow=True)
        # The opening question stands alone: no small label overlaps its silhouette.
    if t<7.52:diagram_wait(im,t)
    elif t<12.54:diagram_early(im,t)
    elif t<15.52:product_market(im,t)
    elif t<18.66:audience_cards(im,t)
    else:final_graphic(im,t)
    phrase_type(im,t)
    draw_ui(im,t)
    # Short, low-intensity impact flashes. No sustained strobing.
    f=max([.13*math.exp(-(t-hit)/.038) for hit in FLASHES if 0<=t-hit<.1]+[0])
    if f>.005:im=Image.blend(im,Image.new('RGB',(W,H),WHITE),f)
    if t>DURATION-.18:
        p=smooth((t-(DURATION-.18))/.18)*.15
        im=Image.blend(im,Image.new('RGB',(W,H),DARK),p)
    return im


def stills():
    src=Source()
    ts=[.6,1.95,3.6,5.9,8.7,11.2,13.9,16.0,17.6,19.1,20.35]
    thumbs=[]
    for i,t in enumerate(ts):
        im=render_frame(src,t)
        im.save(ROOT/f'analysis/design-frame-{i:02d}.jpg',quality=92)
        small=im.resize((270,480),Image.Resampling.LANCZOS)
        thumbs.append((t,small))
    sheet=Image.new('RGB',(270*6,510*2),(27,28,29));d=ImageDraw.Draw(sheet)
    for i,(t,im) in enumerate(thumbs):
        x=(i%6)*270;y=(i//6)*510
        sheet.paste(im,(x,y));d.text((x+9,y+486),f'{t:.2f}s',font=font(19,'body'),fill=WHITE)
    sheet.save(ROOT/'analysis/design-contact.jpg',quality=92)
    # Poster comes from the actual export composition, not a separate misleading scene.
    render_frame(src,20.33).save(OUT/'poster.jpg',quality=95)
    src.close()
    print('STILLS_COMPLETE',flush=True)


def render():
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    visuals=ROOT/'analysis/visuals.mp4'
    cmd=[ff,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(visuals)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    src=Source();n=round(DURATION*FPS);start=time.monotonic()
    try:
        for i in range(n):
            frame=render_frame(src,i/FPS)
            p.stdin.write(frame.tobytes())
            if i%60==0:print(f'Rendered {i}/{n} frames; elapsed {time.monotonic()-start:.1f}s',flush=True)
    finally:
        if p.stdin:p.stdin.close()
        src.close()
    if p.wait()!=0:raise RuntimeError('FFmpeg visual encode failed')
    print('VISUAL_RENDER_COMPLETE',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--render',action='store_true');args=ap.parse_args()
    if args.stills:stills()
    if args.render:render()
