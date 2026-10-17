"""V3: a continuous, one-container product-motion interpretation.

Original graphics and raw source footage only. Inspiration is documented in
analysis/scene-plan-morph-v3.md. No third-party code is executed.

python source/render_morph_v3.py --stills
python source/render_morph_v3.py --render
"""
from pathlib import Path
from functools import lru_cache
import argparse, bisect, json, math, subprocess, time
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import soundfile as sf
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edits/voice-agents-morph-v3';OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'cache';CACHE.mkdir(parents=True,exist_ok=True)
FONTS=ROOT/'assets/fonts'
W,H,FPS=1080,1920,60
DURATION=21.37
PAPER=(242,241,237)
WHITE=(255,255,253)
INK=(15,16,20)
BLUE=(66,70,245)
GRAY=(121,124,128)
PALE=(225,227,255)
WORDS=[w for s in json.loads((ROOT/'analysis/transcript.json').read_text())['segments']for w in s['words']]
AUDIO,AR=sf.read(ROOT/'analysis/raw-audio.wav',dtype='float32')

@lru_cache(maxsize=120)
def font(size,kind='sans',weight=650):
    name='Geist-Variable.ttf' if kind=='sans' else 'GeistMono-Variable.ttf'
    f=ImageFont.truetype(str(FONTS/name),max(8,int(size)))
    f.set_variation_by_axes([weight]);return f

def ease(x):
    x=max(0.,min(1.,x));return 1-(1-x)**3

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def critical(t,omega=18.):
    if t<=0:return 0.
    return 1-(1+omega*t)*math.exp(-omega*t)

def color_mix(a,b,p):return tuple(int(max(0,min(255,x+(y-x)*p)))for x,y in zip(a,b))

def fit(s,size,width,kind='sans',weight=650):
    while size>16 and font(size,kind,weight).getlength(s)>width:size-=1
    return size

@lru_cache(maxsize=192)
def glyph(s,size,col=INK,kind='sans',weight=650):
    f=font(size,kind,weight);bb=f.getbbox(s);pad=10
    a=Image.new('RGBA',(bb[2]-bb[0]+pad*2,bb[3]-bb[1]+pad*2),(0,0,0,0))
    ImageDraw.Draw(a).text((pad-bb[0],pad-bb[1]),s,font=f,fill=(*col,255))
    return a

def text(im,s,x,y,size=40,col=INK,kind='sans',weight=650,alpha=1.,align='center'):
    a=glyph(s,int(size),tuple(col),kind,weight)
    if alpha<.998:
        a=a.copy();a.putalpha(a.getchannel('A').point(lambda p:int(p*max(0,alpha))))
    xx=x-a.width/2 if align=='center' else x-10
    im.paste(a,(int(xx),int(y-a.height/2)),a)
    return a.width-20

@lru_cache(maxsize=32)
def rounded_mask(w,h,r):
    a=Image.new('L',(w,h),0);ImageDraw.Draw(a).rounded_rectangle((0,0,w-1,h-1),radius=r,fill=255)
    return a

class Source:
    def __init__(self):
        self.cap=cv2.VideoCapture(str(ROOT/'assets/raw.mp4'));self.fps=self.cap.get(cv2.CAP_PROP_FPS);self.idx=-1;self.a=None
    def get(self,t):
        i=min(619,max(0,int(min(t,20.665)*self.fps)))
        if i==self.idx:return self.a.copy()
        if i!=self.idx+1:self.cap.set(cv2.CAP_PROP_POS_FRAMES,i)
        ok,b=self.cap.read()
        if not ok:
            if self.a is not None:return self.a.copy()
            raise RuntimeError('Source decode failed')
        b=cv2.cvtColor(b,cv2.COLOR_BGR2RGB)
        self.a=b;self.idx=i;return b.copy()
    def close(self):self.cap.release()

# Each state changes the geometry of the same underlying object.
# at, name, width, height, center-y, corner radius, fill
STATES=[
 (0.,'video',900,680,1080,38,WHITE),
 (2.26,'years',860,370,1080,58,INK),
 (3.52,'globe',560,560,1080,280,INK),
 (4.905,'effort',900,400,1080,55,INK),
 (7.52,'toggle',720,330,1060,165,INK),
 (9.28,'invest',900,720,1090,42,WHITE),
 (12.54,'market',900,580,1080,42,WHITE),
 (15.52,'audience',920,720,1080,42,WHITE),
 (18.66,'converge',780,440,1080,80,INK),
 (19.74,'final',1000,1500,1000,64,BLUE),
]
STATE_TIMES=[s[0]for s in STATES]

def geometry(t):
    vals=np.array([*STATES[0][2:6],*STATES[0][6]],dtype=float)
    for i in range(1,len(STATES)):
        at=STATES[i][0]
        if at>t:break
        prev=np.array([*STATES[i-1][2:6],*STATES[i-1][6]],dtype=float)
        target=np.array([*STATES[i][2:6],*STATES[i][6]],dtype=float)
        vals+=(target-prev)*critical(t-at,17.5 if i!=9 else 15.)
    width,height,cy,r=vals[:4]
    width=max(80,int(round(width)));height=max(80,int(round(height)))
    r=int(max(0,min(r,min(width,height)/2)))
    return width,height,float(cy),r,tuple(int(max(0,min(255,x)))for x in vals[4:])


def waveform_values(t,n=57):
    result=[]
    for j in range(n):
        at=t-.8+j*.8/max(1,n-1)
        start=max(0,int(at*AR));end=min(len(AUDIO),start+int(.018*AR))
        rms=float(np.sqrt(np.mean(AUDIO[start:end]**2)))if end>start and at>=0 else 0.
        result.append(min(1,rms*6))
    return result


def wave(d,cx,cy,width,height,t,col,n=57):
    for j,v in enumerate(waveform_values(t,n)):
        x=cx-width/2+j*width/(n-1);hh=3+height*v
        d.rounded_rectangle((x-3,cy-hh,x+3,cy+hh),radius=3,fill=col)


def paste_video(card,raw,x,y,w,h,r=16):
    w=max(2,int(w));h=max(2,int(h));p=Image.new('RGB',(w,h),INK)
    scale=min(w/raw.shape[1],h/raw.shape[0]);nw=int(raw.shape[1]*scale);nh=int(raw.shape[0]*scale)
    a=Image.fromarray(cv2.resize(raw,(nw,nh),interpolation=cv2.INTER_CUBIC));p.paste(a,((w-nw)//2,(h-nh)//2))
    card.paste(p,(int(x),int(y)),rounded_mask(w,h,min(r,min(w,h)//2)))


def video_view(card,raw,t,w,h,invest=False):
    d=ImageDraw.Draw(card)
    fs=max(14,min(23,int(w*.026)))
    text(card,'GLOBAL THINKING'if invest else'VOICE AI / CONVERSATION',29,38,fs,GRAY,'mono',500,align='left')
    if w>760:text(card,'SOURCE AUDIO',w-130,38,17,GRAY,'mono',450)
    vh=max(40,min((w-44)*9/16,h-170))
    paste_video(card,raw,22,77,w-44,int(vh),17)
    cy=h-58
    d.ellipse((31,cy-25,81,cy+25),fill=BLUE)
    if invest and t>=11.04:
        d.line([(43,cy),(53,cy+8),(69,cy-10)],fill=WHITE,width=4)
        text(card,'INVESTED',103,cy,28,BLUE,'sans',720,align='left')
        start=303
    elif invest:
        d.line([(47,cy-8),(47,cy+8)],fill=WHITE,width=4);d.line([(62,cy-8),(62,cy+8)],fill=WHITE,width=4)
        text(card,'A PRIORITY',102,cy,26,INK,'sans',650,align='left');start=298
    else:
        d.line([(47,cy-8),(47,cy+8)],fill=WHITE,width=4);d.line([(62,cy-8),(62,cy+8)],fill=WHITE,width=4)
        start=110
    end=w-40
    if end>start:
        d.rounded_rectangle((start,cy-3,end,cy+3),radius=3,fill=(222,223,226))
        progress=min(1,t/20.735)
        d.rounded_rectangle((start,cy-3,start+(end-start)*progress,cy+3),radius=3,fill=BLUE)


def years_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    text(card,'THE WAIT',w/2,h*.16,max(15,int(h*.06)),(163,165,172),'mono',500)
    fs=fit('YEARS',int(h*.32),w-110,'sans',700)
    text(card,'YEARS',w/2,h*.43,fs,WHITE,'sans',700)
    yy=h*.75
    progress=.08+.20*ease((t-2.26)/1.26)
    for j in range(32):
        x=65+(w-130)*j/31
        col=BLUE if j/31<progress else(69,70,78)
        d.rounded_rectangle((x-3,yy-14,x+3,yy+14),radius=3,fill=col)
    text(card,'before going global',w/2,h*.91,max(16,int(h*.055)),(164,166,174),'mono',450)


def sphere(d,cx,cy,r,t,col=WHITE):
    yaw=(t-3.52)*.56;tilt=.16
    def project(lat,lon):
        x=math.cos(lat)*math.sin(lon+yaw);y=-math.sin(lat);z=math.cos(lat)*math.cos(lon+yaw)
        yy=y*math.cos(tilt)-z*math.sin(tilt);zz=y*math.sin(tilt)+z*math.cos(tilt)
        return(cx+r*x,cy+r*yy,zz)
    def curve(pts):
        for a,b in zip(pts,pts[1:]):
            if a[2]>0 and b[2]>0:d.line([(a[0],a[1]),(b[0],b[1])],fill=col,width=2)
            elif a[2]<0 and b[2]<0:d.line([(a[0],a[1]),(b[0],b[1])],fill=(49,51,64),width=1)
    for lat in np.linspace(-math.pi*.36,math.pi*.36,7):curve([project(lat,l)for l in np.linspace(-math.pi,math.pi,95)])
    for lon in np.linspace(-math.pi,math.pi,12,endpoint=False):curve([project(l,lon)for l in np.linspace(-math.pi/2,math.pi/2,65)])
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=col,width=3)
    for i in range(25):
        z=1-2*(i+.5)/25;lat=math.asin(z);lon=i*2.399963
        x,y,zz=project(lat,lon)
        if zz>.04:
            rr=3+3*zz;d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=BLUE if i%3 else WHITE)


def globe_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card);r=min(w,h)*.355
    sphere(d,w/2,h*.46,r,t)
    fs=fit('INTERNATIONAL',24,w-100,'mono',500)
    text(card,'INTERNATIONAL',w/2,h*.91,fs,(183,186,200),'mono',500)


def effort_progress(t):
    p=.18+.73*ease((t-5.68)/1.42)
    if t>7.12:p-=.025*critical(t-7.12,18)
    return p


def effort_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    text(card,'EFFORT',w/2,h*.20,max(19,int(h*.063)),(166,168,180),'mono',500)
    text(card,'to go global',w/2,h*.43,fit('to go global',int(h*.15),w-100,'sans',650),WHITE,'sans',650)
    x1,x2=67,w-67;y=h*.71
    p=effort_progress(t);x=x1+(x2-x1)*p
    d.rounded_rectangle((x1,y-8,x2,y+8),radius=8,fill=(61,63,75))
    d.rounded_rectangle((x1,y-8,x,y+8),radius=8,fill=BLUE)
    d.ellipse((x-25,y-25,x+25,y+25),fill=WHITE,outline=BLUE,width=3)
    text(card,'LOCAL',x1,y+53,17,(163,166,179),'mono',450)
    text(card,'GLOBAL',x2,y+53,17,(163,166,179),'mono',450)


def toggle_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    diameter=h-46;gap=w-46-diameter
    slow=critical(t-8.44,18);fast=critical(t-8.44,24)
    left=23+gap*slow;right=23+diameter+gap*fast
    col=color_mix(WHITE,BLUE,ease((t-8.44)/.22))
    text(card,'EARLY',w*.30,h/2,max(30,int(h*.17)),WHITE,'sans',700,alpha=slow)
    text(card,'EARLY',w*.72,h/2,max(30,int(h*.17)),WHITE,'sans',700,alpha=1-fast)
    d.rounded_rectangle((left,23,right,h-23),radius=diameter/2,fill=col)
    if fast>.75:
        cx=(left+right)/2;cy=h/2
        d.line([(cx-34,cy),(cx-10,cy+24),(cx+40,cy-29)],fill=WHITE,width=max(5,int(h*.025)))


def market_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    text(card,'CONCEPT / PRODUCT TO MARKET',30,41,fit('CONCEPT / PRODUCT TO MARKET',22,w-60,'mono',500),GRAY,'mono',500,align='left')
    cy=h*.46;l=w*.25;r=w*.76;size=min(174,h*.31)
    d.rounded_rectangle((l-size/2,cy-size/2,l+size/2,cy+size/2),radius=29,fill=INK)
    for j in range(7):
        x=l+(j-3)*16;hh=(19+23*abs(math.sin(j*.8+t*2)))
        d.rounded_rectangle((x-4,cy-hh,x+4,cy+hh),radius=4,fill=BLUE if j%2 else WHITE)
    rr=size*.48
    d.ellipse((r-rr,cy-rr,r+rr,cy+rr),outline=INK,width=3)
    d.ellipse((r-rr*.4,cy-rr,r+rr*.4,cy+rr),outline=BLUE,width=3)
    d.ellipse((r-rr,cy-rr*.4,r+rr,cy+rr*.4),outline=INK,width=2)
    x1=l+size*.65;x2=r-rr-30
    d.line([(x1,cy),(x2,cy)],fill=(210,213,227),width=4)
    p=ease((t-13.38)/.8)
    if x2>x1:
        d.line([(x1,cy),(x1+(x2-x1)*p,cy)],fill=BLUE,width=5)
        sx=x1+(x2-x1)*p;d.ellipse((sx-12,cy-12,sx+12,cy+12),fill=BLUE)
        d.line([(x2-12,cy-10),(x2,cy),(x2-12,cy+10)],fill=BLUE,width=4)
    text(card,'PRODUCT',l,h*.78,fit('PRODUCT',34,w*.4,'sans',700),INK,'sans',700)
    text(card,'MARKET',r,h*.78,fit('MARKET',34,w*.4,'sans',700),BLUE if t>=14 else INK,'sans',700)


def icon(d,kind,cx,cy,r,col=BLUE):
    line=4
    if kind=='people':
        d.ellipse((cx-r*.24,cy-r*.61,cx+r*.24,cy-r*.13),outline=col,width=line)
        d.arc((cx-r*.5,cy-r*.05,cx+r*.5,cy+r*.85),180,358,fill=col,width=line)
        for side in [-1,1]:
            xx=cx+side*r*.68
            d.ellipse((xx-r*.14,cy-r*.38,xx+r*.14,cy-r*.1),outline=col,width=3)
            d.arc((xx-r*.25,cy+r*.05,xx+r*.25,cy+r*.56),180,358,fill=col,width=3)
    elif kind=='businesses':
        d.rounded_rectangle((cx-r*.57,cy-r*.72,cx+r*.57,cy+r*.73),radius=5,outline=col,width=line)
        for row in range(3):
            for cl in range(2):
                x=cx-r*.27+cl*r*.5;y=cy-r*.43+row*r*.35;d.rectangle((x-4,y-4,x+4,y+4),fill=col)
        d.line([(cx-r*.75,cy+r*.76),(cx+r*.75,cy+r*.76)],fill=col,width=3)
    elif kind=='developers':
        d.line([(cx-r*.23,cy-r*.45),(cx-r*.67,cy),(cx-r*.23,cy+r*.45)],fill=col,width=line)
        d.line([(cx+r*.23,cy-r*.45),(cx+r*.67,cy),(cx+r*.23,cy+r*.45)],fill=col,width=line)
        d.line([(cx+r*.1,cy-r*.6),(cx-r*.1,cy+r*.6)],fill=col,width=line)
    else:
        d.line([(cx-r*.8,cy-r*.3),(cx,cy-r*.75),(cx+r*.8,cy-r*.3),(cx-r*.8,cy-r*.3)],fill=col,width=line)
        for dx in [-.53,0,.53]:d.line([(cx+r*dx,cy-r*.1),(cx+r*dx,cy+r*.59)],fill=col,width=line)
        d.line([(cx-r*.8,cy+r*.75),(cx+r*.8,cy+r*.75)],fill=col,width=line)

AUDIENCES=[('PEOPLE','people',15.52,.25,.26),('BUSINESSES','businesses',16.6,.75,.26),('DEVELOPERS','developers',17.38,.25,.74),('GOVERNMENTS','governments',18.34,.75,.74)]

def audience_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    cw=w*.40;ch=h*.32
    for label,kind,at,px,py in AUDIENCES:
        cx=w*px;cy=h*py;p=ease((t-at)/.20)
        col=color_mix((211,214,222),BLUE,p)
        end=(w/2+(cx-w/2)*p,h/2+(cy-h/2)*p)
        d.line([(w/2,h/2),end],fill=col,width=3)
        d.rounded_rectangle((cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2),radius=23,fill=(247,248,250),outline=color_mix((230,231,235),(184,189,255),p),width=2)
        if p>.01:
            icon(d,kind,cx,cy-ch*.12,min(48,ch*.23),color_mix((218,220,229),BLUE,p))
            fs=fit(label,32,cw-25,'sans',700)
            text(card,label,cx,cy+ch*.30,fs,color_mix((238,239,243),INK,p),'sans',700)
    d.ellipse((w/2-43,h/2-43,w/2+43,h/2+43),fill=BLUE)
    for j in range(5):
        hh=9+10*abs(math.sin(j*.9+t*3));xx=w/2+(j-2)*10
        d.rounded_rectangle((xx-2,h/2-hh,xx+2,h/2+hh),radius=2,fill=WHITE)


def converge_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card);p=ease((t-18.66)/.62)
    for i,(label,kind,at,px,py)in enumerate(AUDIENCES):
        x=w*.5+(px-.5)*w*(1-p);y=h*.5+(py-.5)*h*(1-p)
        d.line([(x,y),(w/2,h/2)],fill=(79,82,134),width=2)
        rr=6+9*(1-p);d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=BLUE)
    wave(d,w/2,h*.53,w*.67,h*.17,t,WHITE,41)
    text(card,'BUILD GREAT',w/2,h*.17,25,(159,164,190),'mono',500)


def final_view(card,raw,t,w,h):
    d=ImageDraw.Draw(card)
    text(card,'VOICE AI',w/2,h*.075,25,WHITE,'mono',500)
    fs=min(182,int(h*.14),int(w*.19))
    p=ease((t-19.74)/.16)
    text(card,'Voice',w/2,h*.265+15*(1-p),fs,WHITE,'sans',720,alpha=p)
    if t>=20.02:
        q=ease((t-20.02)/.18)
        text(card,'agents.',w/2,h*.405+15*(1-q),fs,WHITE,'sans',720,alpha=q)
    if t>20.08:
        wave(d,w/2,h*.64,w*.70,h*.06,t,WHITE,61)
        d.line([(w*.14,h*.745),(w*.86,h*.745)],fill=(142,146,255),width=2)
        names=['PEOPLE','BUSINESSES','DEVELOPERS','GOVERNMENTS']
        for i,name in enumerate(names):
            cx=w*(.16+i*.226)
            d.ellipse((cx-5,h*.745-5,cx+5,h*.745+5),fill=WHITE)
            text(card,name,cx,h*.785,fit(name,28,w*.205,'mono',500),WHITE,'mono',500)
        text(card,'Built for everyone.',w/2,h*.89,min(42,int(w*.045)),WHITE,'sans',500)


def view(name,raw,t,w,h,fill):
    card=Image.new('RGB',(w,h),fill)
    if name=='video':video_view(card,raw,t,w,h)
    elif name=='years':years_view(card,raw,t,w,h)
    elif name=='globe':globe_view(card,raw,t,w,h)
    elif name=='effort':effort_view(card,raw,t,w,h)
    elif name=='toggle':toggle_view(card,raw,t,w,h)
    elif name=='invest':video_view(card,raw,t,w,h,True)
    elif name=='market':market_view(card,raw,t,w,h)
    elif name=='audience':audience_view(card,raw,t,w,h)
    elif name=='converge':converge_view(card,raw,t,w,h)
    else:final_view(card,raw,t,w,h)
    return card


def draw_main(im,raw,t):
    idx=max(0,bisect.bisect_right(STATE_TIMES,t)-1)
    w,h,cy,r,fill=geometry(t);x=int(W/2-w/2);y=int(cy-h/2)
    # Small-scale soft shadow gives depth without blurry type or heavy glows.
    shadow=Image.new('L',(W//4,H//4),0)
    ImageDraw.Draw(shadow).rounded_rectangle((x/4,(y+20)/4,(x+w)/4,(y+h+20)/4),radius=r/4,fill=36)
    shadow=shadow.filter(ImageFilter.GaussianBlur(8)).resize((W,H),Image.Resampling.BILINEAR)
    im.paste(Image.new('RGB',(W,H),(28,29,37)),(0,0),shadow)
    card=view(STATES[idx][1],raw,t,w,h,fill)
    dt=t-STATES[idx][0]
    if idx>0 and dt<.28:
        p=ease(max(0,dt-.025)/.255)
        prev=view(STATES[idx-1][1],raw,t,w,h,fill)
        if p>.12:prev=prev.filter(ImageFilter.GaussianBlur(1.7*p))
        if p<.85:card=card.filter(ImageFilter.GaussianBlur(1.3*(1-p)))
        card=Image.blend(prev,card,p)
    if sum(fill)>540:
        ImageDraw.Draw(card).rounded_rectangle((1,1,w-2,h-2),radius=max(0,r-1),outline=(219,220,225),width=2)
    im.paste(card,(x,y),rounded_mask(w,h,r))
    return(x,y,w,h)

HEADS=[
 (0.,'Go global.','Why wait?'),
 (2.26,'The long','way around.'),
 (3.52,'Going','international.'),
 (4.905,'It takes','real effort.'),
 (7.52,'For us,','a new approach.'),
 (8.44,'Think global.','Early.'),
 (9.28,'Make it','a priority.'),
 (11.04,'Invest','early.'),
 (12.54,'From product','to market.'),
 (15.52,'Built for','everyone.'),
 (18.66,'Build','great.'),
]


def headline(im,t):
    if t>=19.74:return
    at,a,b=next(item for item in reversed(HEADS)if t>=item[0])
    p=ease((t-at)/.19)
    fs=fit(a,130,930,'sans',620);fs2=fit(b,146,930,'sans',720)
    text(im,a,540,355+22*(1-p),fs,INK,'sans',620,alpha=p)
    alpha=p
    if at==18.66:alpha*=ease((t-19.30)/.12)
    text(im,b,540,525+22*(1-p),fs2,BLUE,'sans',720,alpha=alpha)

CAPS=[];current=[]
for w in WORDS:
    if current and(w['start']-current[-1]['end']>.38 or len(current)>=5 or w['end']-current[0]['start']>1.45):CAPS.append(current);current=[]
    current.append(w)
    if w['word'].endswith(('.',',','?','!'))and len(current)>=2:CAPS.append(current);current=[]
if current:CAPS.append(current)


def caption(im,t):
    if t>=19.74:return
    group=None
    for i,c in enumerate(CAPS):
        end=CAPS[i+1][0]['start']if i+1<len(CAPS)else c[-1]['end']+.2
        if c[0]['start']<=t<min(end,c[-1]['end']+.38):group=c;break
    if group is None:return
    s=' '.join(w['word']for w in group);fs=fit(s,46,920,'sans',480);f=font(fs,'sans',480)
    x=(W-f.getlength(s))/2;y=1636
    for w in group:
        ww=f.getlength(w['word']);active=w['start']<=t<w['end']
        col=BLUE if active else(INK if t>=w['start']else(161,163,168))
        text(im,w['word'],x,y,fs,col,'sans',480,align='left')
        if active:ImageDraw.Draw(im).line([(x,y+31),(x+ww,y+31)],fill=BLUE,width=3)
        x+=ww+f.getlength(' ')

CURSOR_KEYS=[
 (0.,(932,1426)),(1.75,(923,1388)),(2.26,(923,1370)),
 (3.22,(810,1257)),(3.52,(765,1157)),(4.65,(715,1155)),
 (4.905,(289,1182)),(5.68,(320,1182)),(7.3,(857,1182)),
 (7.8,(790,1130)),(8.44,(733,1060)),(9.02,(768,1057)),
 (10.7,(356,1390)),(11.04,(286,1391)),(11.7,(420,1460)),
 (12.7,(330,1240)),(13.38,(330,1045)),(14.18,(765,1045)),
 (15.28,(763,1055)),(15.52,(300,909)),(16.6,(780,909)),
 (17.38,(300,1251)),(18.34,(780,1251)),(19.1,(698,1170)),
 (19.74,(700,1092)),(20.08,(927,1510)),(20.28,(1110,1970)),(21.37,(1110,1970))]
CLICKS=[2.26,3.52,8.44,11.04,13.38,15.52,16.6,17.38,18.34,19.74]


def cursor_position(t,box):
    if 5.68<=t<7.36:
        x,y,w,h=box
        return(x+67+(w-134)*effort_progress(t),y+h*.71+12)
    for (t0,p0),(t1,p1)in zip(CURSOR_KEYS,CURSOR_KEYS[1:]):
        if t0<=t<t1:
            p=smooth((t-t0)/(t1-t0));return(p0[0]+(p1[0]-p0[0])*p,p0[1]+(p1[1]-p0[1])*p)
    return CURSOR_KEYS[-1][1]


def cursor(im,t,box):
    x,y=cursor_position(t,box);d=ImageDraw.Draw(im)
    for at in CLICKS:
        dt=t-at
        if 0<=dt<.24:
            p=dt/.24;rr=10+21*p
            d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=color_mix(BLUE,PAPER,p),width=2)
    # Custom arrow, not a third-party asset. Crisp white edge on all backgrounds.
    pts=[(x,y),(x+1,y+37),(x+10,y+29),(x+18,y+44),(x+27,y+39),(x+19,y+25),(x+33,y+24)]
    d.polygon([(xx+2,yy+3)for xx,yy in pts],fill=(190,190,191))
    d.polygon(pts,fill=INK,outline=WHITE,width=2)

rng=np.random.default_rng(413)
noise=rng.normal(0,.35,(H,W,1))
BASE=Image.fromarray(np.clip(np.array(PAPER)[None,None,:]+noise,0,255).astype(np.uint8))


def render_frame(src,t):
    im=BASE.copy();raw=src.get(t)
    box=draw_main(im,raw,t)
    headline(im,t);caption(im,t)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((76,128,85,158),radius=4,fill=BLUE)
    text(im,'VOICE AI',102,143,25,INK,'mono',600,align='left')
    text(im,'CONCEPT FILM / 03',845,143,21,GRAY,'mono',450)
    cursor(im,t,box)
    return im


def stills():
    src=Source();times=[.85,2.92,4.2,6.5,8.85,10.35,11.5,13.95,15.93,17.65,18.5,19.2,20.12,20.55]
    tw,th=270,480;sheet=Image.new('RGB',(tw*7,(th+30)*2),(27,27,27));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        a=render_frame(src,t);a.save(ROOT/f'analysis/morph-v3-frame-{i:02d}.jpg',quality=93)
        x=i%7*tw;y=i//7*(th+30);sheet.paste(a.resize((tw,th),Image.Resampling.LANCZOS),(x,y));d.text((x+7,y+th+6),f'{t:.2f}s',font=font(18,'mono',500),fill=WHITE)
    sheet.save(ROOT/'analysis/morph-v3-contact.jpg',quality=95)
    render_frame(src,20.55).save(OUT/'poster.jpg',quality=95)
    src.close();print('MORPH_V3_STILLS_COMPLETE',flush=True)


def render():
    ff=imageio_ffmpeg.get_ffmpeg_exe();dest=CACHE/'visuals-morph-v3.mp4'
    cmd=[ff,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(dest)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE);src=Source();total=round(DURATION*FPS);start=time.monotonic()
    try:
        for i in range(total):
            im=render_frame(src,i/FPS);p.stdin.write(im.tobytes())
            if i%120==0:print(f'Morph v3 render {i}/{total}; elapsed {time.monotonic()-start:.1f}s',flush=True)
    finally:
        if p.stdin:p.stdin.close()
        src.close()
    if p.wait()!=0:raise RuntimeError('V3 visual encoding failed')
    print('MORPH_V3_VISUAL_RENDER_COMPLETE',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--render',action='store_true');a=ap.parse_args()
    if a.stills:stills()
    if a.render:render()
