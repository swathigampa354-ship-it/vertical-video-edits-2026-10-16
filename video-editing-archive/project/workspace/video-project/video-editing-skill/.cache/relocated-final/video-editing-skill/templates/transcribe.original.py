from pathlib import Path
import json, time
import imageio_ffmpeg, subprocess
from faster_whisper import WhisperModel
ROOT=Path(__file__).resolve().parents[1]
audio=ROOT/'analysis/raw-audio.wav'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-hide_banner','-loglevel','error','-i',str(ROOT/'assets/raw.mp4'),'-vn','-ac','1','-ar','16000',str(audio)],check=True)
print('Loading English speech model...',flush=True)
model=WhisperModel('base.en',device='cpu',compute_type='int8',cpu_threads=2,num_workers=1)
import soundfile as sf
samples, rate=sf.read(audio,dtype='float32')
assert rate==16000
segments, info=model.transcribe(samples,language='en',beam_size=5,word_timestamps=True,vad_filter=False,condition_on_previous_text=True)
result={'language':info.language,'duration':info.duration,'segments':[]}
for s in segments:
 item={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word.strip(),'probability':w.probability} for w in (s.words or [])]}
 result['segments'].append(item)
 print(f"{s.start:.2f}–{s.end:.2f}: {s.text}",flush=True)
(ROOT/'analysis/transcript.json').write_text(json.dumps(result,indent=2))
print('TRANSCRIPTION_COMPLETE',flush=True)
