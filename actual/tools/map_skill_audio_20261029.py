#!/usr/bin/env python3
"""Offline MAP SFX generation/mastering and waveform-conditioned local review."""
import argparse, hashlib, json, math, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODEL=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx')
SOURCE=ROOT/'source/map-20261029/audio/v2'
OUT=ROOT/'actual/assets/sfx/map-20261029'
REPORT=ROOT/'actual/reports/map-skills-20261029'
SR=44100
SPECS={
 'hunapu_base':(.60,'One compact fantasy steel sword slash: crisp metallic air sweep, dense short upper-mid whoosh and a little gritty armor scrape, forceful but restrained, one gesture, not a long cinematic explosion.'),
 'hunapu_advanced':(.78,'One powerful broad steel blade air slash: layered sharp silver metallic sweep over a strong wind rush and brief coarse armor-breaking crackle. Clearly wider and richer than a small sword slash. Dry, fast decay, no ringing musical note.'),
 'eileen_base':(.72,'One compact magical fire ring bursting outward: a quick bright flame ignition puff, dense fiery rushing body and short crackling decay. One clear burst, no continuous fireplace, no drums, no long rumble.'),
 'eileen_advanced':(.90,'One bright powerful magical fire pillar and outward flame ring explosion: sharply defined fiery ignition, full but controlled low-mid flame pressure, airy radiant shimmer and quick embers dying away. One burst, dry and compact, no bell melody, no sustained rumble.'),
 'hunapu_bow':(.55,'One strong recurve bow string snapping forward and a swift arrow air hiss, tight dry elastic twang with a clean fast projectile whoosh. One shot only, clear and immediate, no sword metal, no gun, no bullet casing, no impact sequence.'),
 'bow_draw':(.28,'One very short restrained recurve bow draw: taut string tension rising and a quiet wooden limb creak, dry elastic friction, brief and clear. No release twang, no gun, no impact, no musical strings.')}
NEGATIVE='music, melody, beat, speech, voice, vocals, crowd, background ambience, multiple attacks, repeated event, long reverb, cinematic trailer, gunshot'
for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[k]='1'
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guide(key):
 import numpy as np
 import soundfile as sf
 seconds=SPECS[key][0];n=round(seconds*SR);t=np.arange(n)/SR
 rng=np.random.default_rng(20261029050+list(SPECS).index(key));noise=rng.normal(0,1,n)
 def band(lo,hi):
  freq=np.fft.rfftfreq(n,1/SR)
  gain=1/np.sqrt(1+(lo/np.maximum(freq,1e-8))**6)/np.sqrt(1+(freq/hi)**6);gain[0]=0
  x=np.fft.irfft(np.fft.rfft(noise)*gain,n)
  return x/max(float(np.std(x)),1e-8)
 # Original short gesture guides. The local generative model provides the
 # texture variation; these guides keep the attack/decay tied to one action.
 if key.startswith('hunapu_') and key!='hunapu_bow':
  env=np.sin(np.pi*np.clip(t/.30,0,1))**1.3*np.exp(-t*3.0)
  body=band(350,6500)*env
  steel=np.sin(2*np.pi*(1900*t-700*t*t))*np.exp(-t*22)*.09
  x=.30*body+steel
  if key.endswith('advanced'):x+=.11*band(100,1600)*np.exp(-t*8)+.07*band(3500,11000)*np.exp(-t*11)
 elif key.startswith('eileen_'):
  env=(1-np.exp(-t*400))*np.exp(-t*(7.0 if key.endswith('base') else 5.0))
  x=.32*band(120,5800)*env+.09*band(4500,13000)*env*(.4+.6*np.abs(np.sin(t*121)))
  if key.endswith('advanced'):x+=.10*np.sin(2*np.pi*(130*t-40*t*t))*np.exp(-t*14)
 elif key=='hunapu_bow':
  # Damped plucked-string body plus one short air gesture, no second shot.
  length=round(SR/280);buffer=rng.uniform(-1,1,length);string=np.empty(n)
  for i in range(n):
   j=i%length;string[i]=buffer[j];buffer[j]=.497*(buffer[j]+buffer[(j+1)%length])
  x=.30*string*np.exp(-t*8)+.13*band(2000,10000)*np.sin(np.pi*np.clip(t/.28,0,1))*np.exp(-t*7)
 else:
  env=np.sin(np.pi*t/seconds)**1.2
  x=.13*band(250,2800)*env*(.45+.55*np.sin(2*np.pi*(90*t+150*t*t))**2)
 x-=x.mean();x=x/max(float(np.abs(x).max()),1e-8)*.65
 stereo=np.column_stack([x,x]);p=SOURCE/(key+'-guide.wav');p.parent.mkdir(parents=True,exist_ok=True)
 sf.write(p,stereo,SR,subtype='PCM_16');return p
def worker(key):
 import numpy as np
 import soundfile as sf
 for f in ['t5gemma_f16.npz','dit_sm-sfx_f16.npz','same_s_decoder_f32.npz']:
  if not (MODEL/'models/mlx'/f).is_file():raise FileNotFoundError(f)
 sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
 raw=SOURCE/(key+'-raw.wav');raw.parent.mkdir(parents=True,exist_ok=True)
 if raw.exists():return
 def save_float(path,a,sample_rate=SR):
  if not np.isfinite(a).all():raise ValueError('nonfinite generation')
  sf.write(path,a.T,sample_rate,subtype='FLOAT')
 sa3_mlx.save_wav=save_float
 seed=20261029030+list(SPECS).index(key)
 prompt='TrackType: SFX. '+SPECS[key][1]+' Single isolated game sound effect, immediate onset then quick clean decay. No voices or music.'
 reference=guide(key)
 sys.argv=['sa3_mlx.py','--dit','sm-sfx','--decoder','same-s','--seconds','2.5','--dit-dtype','fp32','--steps','8','--cfg','2.0','--seed',str(seed),'--prompt',prompt,'--negative-prompt',NEGATIVE+', monotonous static buzz, pure sine tone','--init-audio',str(reference),'--init-noise-level','.42','--out',str(raw)]
 start=time.monotonic();sa3_mlx.main()
 dump(raw.with_suffix('.json'),{'model':'local Stable Audio 3 sm-sfx/same-s','dit_dtype':'fp32','method':'original gesture guide conditioned generation','guide':str(reference.relative_to(ROOT)),'guide_sha256':sha(reference),'init_noise_level':.42,'seed':seed,'steps':8,'cfg':2.,'prompt':prompt,'negative_prompt':NEGATIVE,'offline':True,'wall_seconds':round(time.monotonic()-start,2),'sha256':sha(raw)})
def master():
 import numpy as np
 import soundfile as sf
 records=[];OUT.mkdir(parents=True,exist_ok=True)
 for key,(seconds,_) in SPECS.items():
  raw=SOURCE/(key+'-raw.wav');a,sr=sf.read(raw,dtype='float32',always_2d=True);assert sr==SR
  # Validate generated content, retaining the guide's immediate single onset.
  env=np.sqrt(np.mean(a[:len(a)//220*220].reshape(-1,220,2)**2,axis=(1,2)))
  active=np.where(env>max(float(env.max())*.08,1e-5))[0]
  if not len(active):raise ValueError('silent '+key)
  start=0;a=a[:round(seconds*sr)].copy()
  if len(a)<round(seconds*sr):a=np.pad(a,((0,round(seconds*sr)-len(a)),(0,0)))
  original,_=sf.read(SOURCE/(key+'-guide.wav'),dtype='float32',always_2d=True)
  # Preserve the deliberately authored single-gesture timing and blend the
  # generated timbral variation, rather than letting a model add extra hits.
  a-=a.mean(axis=0)
  a*=max(1e-8,float(np.sqrt(np.mean(original**2))))/max(1e-8,float(np.sqrt(np.mean(a*a))))
  a=.28*a+.72*original
  a[:88]*=np.linspace(0,1,88)[:,None];fade=min(round(.065*sr),len(a)//4)
  a[-fade:]*=(.5+.5*np.cos(np.linspace(0,np.pi,fade)))[:,None]
  rms=float(np.sqrt(np.mean(a*a)));peak=float(np.abs(a).max())
  gain=min(10**(-20/20)/max(rms,1e-8),10**(-5/20)/max(peak,1e-8));a*=gain
  target=OUT/('rm_map_'+key+'.ogg');sf.write(target,a,sr,format='OGG',subtype='VORBIS')
  decoded,_=sf.read(target,dtype='float32',always_2d=True)
  assert np.isfinite(decoded).all() and float(np.abs(decoded).max())<1
  records.append({'key':'map_'+key,'id':'rm_map_'+key,'path':'res://'+str(target.relative_to(ROOT/'actual')),'duration':len(decoded)/sr,'sample_rate':sr,'channels':2,'bytes':target.stat().st_size,'sha256':sha(target),'peak_dbfs':20*math.log10(max(1e-9,float(np.abs(decoded).max()))),'rms_dbfs':20*math.log10(max(1e-9,float(np.sqrt(np.mean(decoded**2))))),'trimmed_leading_seconds':start/sr,'source':str(raw.relative_to(ROOT)),'mix':{'guide_fraction':.72,'generated_texture_fraction':.28,'one_attack_only':True},'source_metadata':json.loads(raw.with_suffix('.json').read_text())})
 dump(REPORT/'audio.json',{'generation':'local Stable Audio 3','offline':True,'human_listening':False,'tracks':records})
 print(json.dumps({'mastered':len(records),'seconds':[r['duration']for r in records]}),flush=True)
def generate():
 SOURCE.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 for key in SPECS:
  log=SOURCE/(key+'-generation.log')
  with log.open('w') as f:
   result=subprocess.run([sys.executable,'-B',__file__,'worker',key],stdout=f,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError(log.read_text()[-3500:])
  print('GENERATED '+key,flush=True)
 master()
def review():
 import review_audio_content as r
 r.REPORT=REPORT/'audio-review'
 tracks=json.loads((REPORT/'audio.json').read_text())['tracks']
 tasks=[{'id':t['id'],'kind':'map_sfx','paths':[str(ROOT/'actual'/t['path'].removeprefix('res://'))],'hashes':[t['sha256']],'prompt':r.BLIND,'max_tokens':120,'repeat_short':True}for t in tracks]
 receipts=r.run(tasks);dump(REPORT/'audio-model-review.json',receipts)
def omni():
 import review_audio_omni as r
 r.REPORT=REPORT/'audio-omni'
 tracks=json.loads((REPORT/'audio.json').read_text())['tracks']
 tasks=[{'id':t['id'],'kind':'map_sfx_blind','audios':[{'path':str(ROOT/'actual'/t['path'].removeprefix('res://')),'repeat_short':True}],
  'prompt':'Describe only the sound actually audible in this short audio input. State its timbre and gesture and whether speech, musical melody, intrusive clicks or distortion are audible. Do not infer a visual event or invent a duration. Be critical and report uncertainty. Short inputs below half a second may be repeated with silence for analysis. Under 90 words.','max_tokens':180}for t in tracks]
 r.run(tasks)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['worker','generate','master','review','omni']);a.add_argument('key',nargs='?');args=a.parse_args()
 if args.mode=='worker':worker(args.key)
 else:globals()[args.mode]()
