"""New quiet pulse / cursor sound design; all original, no reference samples."""
from pathlib import Path
import math,subprocess,shutil
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
from scipy.ndimage import uniform_filter1d
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edits/voice-agents-morph-v3';OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'cache';CACHE.mkdir(parents=True,exist_ok=True)
SR=48000;DURATION=21.37
voicefile=ROOT/'analysis/voice-normalized.wav'
if not voicefile.exists():
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-hide_banner','-loglevel','error','-i',str(ROOT/'assets/raw.mp4'),'-vn','-af','highpass=f=65,loudnorm=I=-16:TP=-1.8:LRA=9','-ar',str(SR),'-ac','2','-c:a','pcm_f32le',str(voicefile)],check=True)
voice,sr=sf.read(voicefile,dtype='float32',always_2d=True);assert sr==SR
n=round(DURATION*SR);speech=np.zeros((n,2),np.float32);speech[:min(n,len(voice))]=voice[:n]
fx=np.zeros_like(speech);bed=np.zeros_like(speech);rng=np.random.default_rng(3357)

def add(dst,a,at,gain=1.,pan=0.):
 start=round(at*SR)
 if start<0:a=a[-start:];start=0
 end=min(n,start+len(a))
 if end<=start:return
 a=a[:end-start]
 dst[start:end,0]+=a*gain*math.sqrt((1-pan)*.5)
 dst[start:end,1]+=a*gain*math.sqrt((1+pan)*.5)

def click(freq=1200):
 t=np.arange(round(.055*SR))/SR
 return (np.sin(2*np.pi*freq*t)+.14*rng.normal(size=len(t)))*np.exp(-t*125)

clicks=[2.26,3.52,8.44,11.04,13.38,15.52,16.6,17.38,18.34,19.74]
for i,at in enumerate(clicks):
 pan=0 if at<15.5 else(-.18 if i%2 else .18)
 add(fx,click(970+(i%4)*130),at,.028,pan)
for at in [2.26,3.52,4.905,7.52,9.28,12.54,15.52,18.66,19.74]:
 length=.17;t=np.arange(round(length*SR))/SR
 a=sosfilt(butter(2,[600,3900],fs=SR,btype='bandpass',output='sos'),rng.normal(size=len(t)))
 a*=np.sin(np.pi*np.arange(len(t))/len(t))**2
 add(fx,a,at-.075,.008)
# A low, original 120-BPM pulse, not a third-party track.
for k in range(42):
 at=.18+k*.5
 if at>=DURATION-.4:break
 t=np.arange(round(.21*SR))/SR
 phase=2*np.pi*np.cumsum(49+34*np.exp(-t*40))/SR
 pulse=np.sin(phase)*np.exp(-t*25)
 add(bed,pulse,at,.023 if k%2==0 else .011)
 if k%4==2:
  t=np.arange(round(.32*SR))/SR
  freq=[293.665,349.228,440][(k//4)%3]
  pluck=np.sin(2*np.pi*freq*t)*np.exp(-t*15)*(1-np.exp(-t*160))
  add(bed,pluck,at,.011,pan=(-.15 if k%8 else .15))
for at,freq in [(19.74,440),(20.02,660)]:
 t=np.arange(round(.65*SR))/SR
 a=np.sin(2*np.pi*freq*t)*np.exp(-t*7)*(1-np.exp(-t*110))
 add(fx,a,at,.017)
env=np.sqrt(uniform_filter1d(np.mean(speech**2,axis=1),size=int(.075*SR))+1e-9)
duck=np.clip(1-env*7,.35,1.)
bed*=duck[:,None];fx*=np.clip(duck+.2,.5,1.)[:,None]
fade=np.ones(n,np.float32);fade[:round(.2*SR)]=np.linspace(0,1,round(.2*SR));fade[-round(.65*SR):]=np.linspace(1,0,round(.65*SR))**1.2
mix=speech+(bed+fx)*fade[:,None]
peak=float(np.max(np.abs(mix)))
if peak>.93:mix*=.93/peak
sf.write(CACHE/'morph-v3-audio.wav',mix,SR,subtype='PCM_24')
shutil.copyfile(ROOT/'edits/voice-agents-9x16/captions.srt',OUT/'captions.srt')
print('Morph v3 audio duration:',len(mix)/SR,'peak dBFS:',round(20*np.log10(np.max(np.abs(mix))+1e-9),2))
print('MORPH_V3_AUDIO_COMPLETE',flush=True)
