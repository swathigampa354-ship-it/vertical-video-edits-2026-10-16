"""Preserve the original speech; compose a quiet, original electronic bed/SFX.
No samples or music are taken from the style reference.
"""
from pathlib import Path
import json, math, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
from scipy.ndimage import uniform_filter1d
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edits/voice-agents-9x16'
SR=48000;DURATION=21.37
ff=imageio_ffmpeg.get_ffmpeg_exe()
voicefile=ROOT/'analysis/voice-normalized.wav'
subprocess.run([ff,'-y','-hide_banner','-loglevel','error','-i',str(ROOT/'assets/raw.mp4'),'-vn','-af','highpass=f=65,loudnorm=I=-16:TP=-1.8:LRA=9','-ar',str(SR),'-ac','2','-c:a','pcm_f32le',str(voicefile)],check=True)
voice,sr=sf.read(voicefile,dtype='float32',always_2d=True)
n=round(DURATION*SR)
speech=np.zeros((n,2),np.float32);speech[:min(len(voice),n)]=voice[:n]
rng=np.random.default_rng(4619)
bed=np.zeros((n,2),np.float32);fx=np.zeros((n,2),np.float32)

def add(dst,clip,at,gain=1.,pan=0.):
    start=round(at*SR)
    if start<0:clip=clip[-start:];start=0
    end=min(n,start+len(clip))
    if end<=start:return
    clip=clip[:end-start]
    dst[start:end,0]+=clip*gain*math.sqrt((1-pan)*.5)
    dst[start:end,1]+=clip*gain*math.sqrt((1+pan)*.5)

def kick(length=.28):
    t=np.arange(int(length*SR))/SR
    f=44+88*np.exp(-t*34)
    phase=2*np.pi*np.cumsum(f)/SR
    return (np.sin(phase)*np.exp(-t*19)+.07*rng.normal(size=len(t))*np.exp(-t*140)).astype(np.float32)

def hat(length=.065):
    t=np.arange(int(length*SR))/SR
    noise=rng.normal(size=len(t))
    hp=sosfilt(butter(2,7000,fs=SR,btype='highpass',output='sos'),noise)
    return (hp*np.exp(-t*68)).astype(np.float32)

def click(length=.065,pitch=850):
    t=np.arange(int(length*SR))/SR
    return (np.sin(2*np.pi*pitch*t)*np.exp(-t*100)+.12*rng.normal(size=len(t))*np.exp(-t*140)).astype(np.float32)

beat=60/132
for k in range(-20,30):
    at=8.44+k*beat
    if not 0<=at<DURATION:continue
    build=1. if at>=8.44 else .50
    if k%4 in (0,2):add(bed,kick(),at,.063*build)
    if k%4==2:
        c=hat(.11)
        add(bed,c,at+.008,.023*build)
    add(bed,hat(),at+beat*.5,.020*build,pan=(-.25 if k%2 else .25))
    if at>=12.54:add(bed,hat(.04),at+beat*.75,.010,pan=.35)

# Original, restrained D-minor pulse sequence, not a recognizable melody.
notes=[73.416,73.416,87.307,65.406]
for k in range(12):
    at=.12+k*beat*4
    length=beat*3.6;t=np.arange(round(length*SR))/SR
    f=notes[k%4]
    envelope=(1-np.exp(-t*24))*np.exp(-t*2.3)
    wave=(np.sin(2*np.pi*f*t)+.2*np.sin(2*np.pi*f*2*t))*.012*envelope
    add(bed,wave,at,1.)

# Phrase-linked motion effects: an air movement and a very short soft low-end impact.
for at in [1.58,2.98,4.905,8.44,11.04,13.68,19.74,20.02]:
    length=.14;t=np.arange(round(length*SR))/SR
    noise=rng.normal(size=len(t))
    air=sosfilt(butter(2,2300,fs=SR,btype='highpass',output='sos'),noise)
    air*=np.sin(np.pi*np.arange(len(t))/len(t))**2
    add(fx,air,at-.11,.008)
    low=np.sin(2*np.pi*(48*t+2.2*(1-np.exp(-t*32))))*np.exp(-t*24)
    add(fx,low,at,.048 if at!=19.74 else .073)
for i,at in enumerate([15.52,16.6,17.38,18.34]):
    add(fx,click(pitch=740+i*150),at,.025,pan=(i-1.5)*.12)

# Speech-dependent ducking keeps the original voice decisively in front.
env=np.sqrt(uniform_filter1d(np.mean(speech**2,axis=1),size=int(SR*.075))+1e-9)
duck=np.clip(1-env*8,.35,1.)
fade=np.ones(n,np.float32)
fade[:int(.24*SR)]=np.linspace(0,1,int(.24*SR))
tail=round(.78*SR);fade[-tail:]=np.linspace(1,0,tail)**1.5
bed*=duck[:,None]*fade[:,None]
fx*=np.clip(duck+.15,.45,1)[:,None]*fade[:,None]
mix=speech+bed+fx
peak=float(np.max(np.abs(mix)))
if peak>.93:mix*=.93/peak
sf.write(ROOT/'analysis/original-bed.wav',bed+fx,SR,subtype='PCM_24')
sf.write(ROOT/'analysis/final-audio.wav',mix,SR,subtype='PCM_24')
print('Audio length:',len(mix)/SR,'seconds; peak dBFS:',round(20*np.log10(np.max(np.abs(mix))+1e-9),2),flush=True)

# Full speech captions (visual emphasis phrases are intentionally more concise).
trans=json.loads((ROOT/'analysis/transcript.json').read_text())
words=[w for s in trans['segments'] for w in s['words']]
cues=[];current=[]
for i,w in enumerate(words):
    if current and (w['start']-current[-1]['end']>.38 or len(current)>=5 or w['end']-current[0]['start']>1.45):
        cues.append(current);current=[]
    current.append(w)
    if w['word'].endswith(('.',',','?','!')) and len(current)>=2:
        cues.append(current);current=[]
if current:cues.append(current)

def stamp(s):
    ms=round(s*1000);h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000
    return f'{h:02d}:{m:02d}:{ms//1000:02d},{ms%1000:03d}'

lines=[]
for i,c in enumerate(cues):
    start=c[0]['start'];end=max(start+.2,c[-1]['end'])
    if i+1<len(cues):end=min(end+.07,cues[i+1][0]['start'])
    txt=' '.join(w['word'] for w in c)
    if len(txt)>37:
        ws=txt.split();best=min(range(1,len(ws)),key=lambda k:abs(len(' '.join(ws[:k]))-len(' '.join(ws[k:]))))
        txt=' '.join(ws[:best])+'\n'+' '.join(ws[best:])
    lines.append(f'{i+1}\n{stamp(start)} --> {stamp(end)}\n{txt}\n')
(OUT/'captions.srt').write_text('\n'.join(lines))
print('Captions:',len(cues),'cues',flush=True)
print('AUDIO_COMPLETE',flush=True)
