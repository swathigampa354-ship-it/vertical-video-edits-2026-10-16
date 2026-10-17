"""Original editorial transition SFX over unchanged source narration; no music bed."""
from pathlib import Path
import shutil,subprocess,math
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
from scipy.ndimage import uniform_filter1d
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edits/voice-agents-editorial-v2';OUT.mkdir(parents=True,exist_ok=True)
CACHE=Path('/home/user/.cache/video-project-editorial-v2');CACHE.mkdir(parents=True,exist_ok=True)
voicefile=ROOT/'analysis/voice-normalized.wav'
SR=48000;DURATION=21.37
if not voicefile.exists():
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-hide_banner','-loglevel','error','-i',str(ROOT/'assets/raw.mp4'),'-vn','-af','highpass=f=65,loudnorm=I=-16:TP=-1.8:LRA=9','-ar',str(SR),'-ac','2','-c:a','pcm_f32le',str(voicefile)],check=True)
voice,sr=sf.read(voicefile,dtype='float32',always_2d=True)
assert sr==SR
n=round(DURATION*SR);speech=np.zeros((n,2),np.float32);speech[:min(len(voice),n)]=voice[:n]
fx=np.zeros_like(speech);rng=np.random.default_rng(1889)

def add(a,at,gain,pan=0):
 start=round(at*SR)
 if start<0:a=a[-start:];start=0
 end=min(n,start+len(a))
 if end<=start:return
 a=a[:end-start]
 fx[start:end,0]+=a*gain*math.sqrt((1-pan)*.5)
 fx[start:end,1]+=a*gain*math.sqrt((1+pan)*.5)

def tick(pitch=1300,length=.055):
 t=np.arange(round(length*SR))/SR
 return np.sin(2*np.pi*pitch*t)*np.exp(-t*110)

for at in [2.98,4.905,7.98,12.54,15.52,18.66]:
 length=.19;t=np.arange(round(length*SR))/SR
 a=sosfilt(butter(2,[900,4200],fs=SR,btype='bandpass',output='sos'),rng.normal(size=len(t)))
 a*=np.sin(np.pi*np.arange(len(t))/len(t))**2
 add(a,at-.1,.010)
 add(tick(630,.07),at,.012)
for i,at in enumerate([8.44,9.28,10.22,11.04,15.52,16.6,17.38,18.34]):
 add(tick(950+(i%4)*140),at,.011,pan=(-.15 if i%2 else .15))
# An original, very quiet two-tone editorial payoff. No sampled melody or music.
for at,f,g in [(19.74,440,.013),(20.02,660,.013)]:
 t=np.arange(round(.52*SR))/SR
 a=np.sin(2*np.pi*f*t)*np.exp(-t*8)*(1-np.exp(-t*120))
 add(a,at,g)
env=np.sqrt(uniform_filter1d(np.mean(speech**2,axis=1),size=int(SR*.075))+1e-9)
fx*=np.clip(1-env*5,.5,1)[:,None]
fade=np.ones(n,np.float32);fade[-round(.5*SR):]=np.linspace(1,0,round(.5*SR))
fx*=fade[:,None]
mix=speech+fx
peak=float(np.max(np.abs(mix)))
if peak>.93:mix*=.93/peak
sf.write(CACHE/'editorial-v2-audio.wav',mix,SR,subtype='PCM_24')
shutil.copyfile(ROOT/'edits/voice-agents-9x16/captions.srt',OUT/'captions.srt')
print('Editorial audio duration:',len(mix)/SR,'peak dBFS:',round(20*np.log10(np.max(np.abs(mix))+1e-9),2))
print('EDITORIAL_AUDIO_COMPLETE')
