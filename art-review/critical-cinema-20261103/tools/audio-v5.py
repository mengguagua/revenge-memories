"""Offline bespoke weapon transients, lightning and two original hero music cues."""
import os,sys,json,subprocess,hashlib,math
from pathlib import Path
import numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1];MODEL=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx');SRC=ROOT/'source/revision5/audio';SRC.mkdir(parents=True,exist_ok=True);SR=44100
for x in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[x]='1'
SPECS={
'slash_light':(.23,'A single razor-sharp steel sword slash. Extremely quick bright shing, cutting air snap, dry metallic edge, immediate stop. Not a thud, no long wind swell or musical ringing.'),
'slash_heavy':(.29,'A single decisive broad steel blade cut. Very fast sharp ching and dense brief air rip, dry hard bright attack, short clipped metallic decay. No large explosion, no sustained note.'),
'sword_hit':(.19,'One clean crisp steel blade striking, sharp bright metallic crack with a compact hard impact, immediate attack and very short decay. Dry close recording, no low muffled thud.'),
'bow_draw':(.18,'One very quick recurve bow draw, short taut dry string friction and tiny wood creak, clipped tension zip, no release and no long stretch.'),
'bow_release':(.12,'One ultra-short tight recurve bowstring release, dry bright tzip snap and brief elastic string slap, crisply stopped, no long boing or guitar note.'),
'bow_release_heavy':(.15,'One strong short longbow release, hard tight elastic snap, bright dry tchak with a little wooden body, no long ringing twang.'),
'arrow_flight':(.17,'One very short fast arrow passing close to the microphone, razor thin fast fssip air cut, sharp start and quick tail, no rocket and no long whistle.'),
'arrow_hit':(.23,'One arrowhead forcefully piercing a soft fleshy target through cloth, clear close dry puncture snap followed by a compact moist dense thwuck and brief shaft quiver. No metal clang, no wood knock, no voice.'),
'flame_blade':(.38,'One crisp sharp steel sword cut with a thin flame layer. Bright dry metallic shing at front, brief fiery air rip, tiny ember tail. Sword edge stays clear, not a muffled fire puff.'),
'flame_burst':(.72,'One bright fire burst with a sharp clean blade impact at the front. Immediate hard ignition crack, compact warm body then fast embers, short controlled decay.'),
'lightning_crack':(.16,'One close lightning crack: extremely sharp violent dry electrical air-tearing snap, a single high-energy transient, no phone beep or synth note.'),
'lightning_body':(.44,'One compact thunderclap body, powerful dense low-mid air pressure boom with crackling high-mid edge, rapid attack, tight decay, not a gunshot or musical drum.'),
'lightning_tail':(.78,'Short natural rolling thunder tail after a nearby lightning strike, irregular low rumble fading quickly, subtle scattered electric fizz, no constant static buzz and no beep.'),
}
MUSIC={
'hunapu':('胡纳普 · 破阵疾锋',176,'TrackType: Music. Original high energy tactical fantasy RPG battle instrumental, 176 BPM, D minor. Driving double-time rock drums, punchy kick and crisp snare, palm-muted distorted rhythm electric guitars and agile melodic lead guitar, powerful bass, short heroic brass accents. A memorable determined four-note motif, relentless forward motion, urgent bold masculine sword-and-bow hero. Start immediately with the full fast rhythm and hook, no slow introduction. Tight professional game soundtrack mix, dry clear percussion, controlled low end, melody leaves room for weapon hits. Instrumental only, absolutely no singing or speech. Entirely original composition.'),
'eileen':('艾琳 · 赤焰疾舞',188,'TrackType: Music. Original intense fast melodic fantasy battle instrumental, 188 BPM, E minor. Rapid staccato strings and agile high violin lead over energetic rock drums, tight electric bass, rhythmic electric guitar, bright celesta-like magical accents used sparingly. A recognizable fiery rising motif, fierce and nimble red-haired sword-and-magic heroine, tense elegant momentum. Start immediately with full fast rhythm and melody, no slow introduction. Clear exciting game soundtrack production, crisp short percussion, light controlled bass, room for magic and sword transients. Instrumental only, no voice or choir. Entirely original composition distinct from a heavy guitar-led male theme.')}
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guide(key):
 sec=SPECS[key][0];n=round(sec*SR);t=np.arange(n)/SR;u=t/sec;r=np.random.default_rng(202611035000+list(SPECS).index(key));z=r.normal(0,1,n)
 def band(lo,hi):
  f=np.fft.rfftfreq(n,1/SR);g=(1+(lo/np.maximum(f,1e-6))**8)**-.5*(1+(f/hi)**8)**-.5;g[0]=0;x=np.fft.irfft(np.fft.rfft(z)*g,n);return x/max(np.std(x),1e-8)
 def decay(tau):return (1-np.exp(-t*2500))*np.exp(-t/tau)
 if key.startswith('slash') or key=='flame_blade':
  env=np.sin(np.pi*np.minimum(t/.085,1))**1.1*np.exp(-t*14);x=.28*band(2200,13500)*env
  for f,a in [(2350,.13),(3680,.07),(6190,.035)]:x+=a*np.sin(2*np.pi*(f*t-1100*t*t))*decay(.028)
  if key=='flame_blade':x+=.10*band(220,8000)*decay(.11)*(1+.2*np.sin(t*283))
 elif key=='sword_hit':
  x=.35*band(1800,14000)*decay(.018)+.16*band(350,1500)*decay(.027)
  for f in [2237,3671,5977]:x+=.075*np.sin(2*np.pi*f*t)*decay(.027)
 elif key=='bow_draw':x=.17*band(500,4500)*np.sin(np.pi*u)**1.3*(.3+.7*np.sin(2*np.pi*(130*t+140*t*t))**2)
 elif key.startswith('bow_release'):
  delay=round(SR/470);b=r.uniform(-1,1,delay);string=np.zeros(n)
  for i in range(n):j=i%delay;string[i]=b[j];b[j]=.485*(b[j]+b[(j+1)%delay])
  x=.27*string*np.exp(-t*70)+.25*band(2500,12500)*decay(.012)
 elif key=='arrow_flight':x=.3*band(4000,15000)*np.sin(np.pi*u)**2*(.8+.2*np.sin(t*800))
 elif key=='arrow_hit':
  x=.36*band(90,1700)*decay(.034)+.22*band(1600,8500)*decay(.009);x+=.12*band(220,3400)*np.exp(-((t-.030)/.019)**2)*(1+.3*np.sin(t*700));x+=.08*np.sin(2*np.pi*(185*t-160*t*t))*decay(.04)
 elif key=='lightning_crack':x=.44*band(1300,16000)*decay(.014)+.2*band(140,2300)*decay(.028)
 elif key=='lightning_body':x=.34*band(50,2200)*decay(.11)+.11*band(2400,12000)*decay(.065)
 elif key=='lightning_tail':x=.23*band(35,850)*decay(.25)*(.65+.35*np.sin(36*t+7*np.sin(t*13)))+.045*band(2100,11000)*decay(.13)
 else:x=.29*band(100,7200)*decay(.14)+.1*band(6000,14500)*decay(.07)
 x-=x.mean();x=x/max(abs(x).max(),1e-8)*.65;p=SRC/(key+'-guide.wav');sf.write(p,np.column_stack([x,x]),SR,subtype='PCM_16');return p

def worker(key):
 sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
 music=key.startswith('music-');hero=key[6:] if music else None;raw=SRC/(key+'-raw.wav')
 if raw.exists():return
 def save(p,a,sample_rate=SR):
  if not np.isfinite(a).all():raise ValueError('nonfinite '+key)
  sf.write(p,a.T,sample_rate,subtype='FLOAT')
 sa3_mlx.save_wav=save
 prompt=MUSIC[hero][2] if music else 'TrackType: SFX. '+SPECS[key][1]+' Isolated single action, close dry foley, silence after the gesture.'
 args=['sa3_mlx.py','--dit','sm-music'if music else'sm-sfx','--decoder','same-s','--seconds','24'if music else'2.0','--dit-dtype','fp32','--steps','12','--cfg','2.5','--seed',str(202611035100+(list(MUSIC).index(hero)if music else list(SPECS).index(key))),'--prompt',prompt,'--negative-prompt','speech, singing, vocals, choir, telephone ringtone, clipping, distortion artifacts'+(''if music else', music, melody, sustained tone, multiple attacks, long reverb'),'--out',str(raw)]
 g=None
 if not music:g=guide(key);args+=['--init-audio',str(g),'--init-noise-level','.24']
 sys.argv=args;sa3_mlx.main();dump(raw.with_suffix('.json'),{'model':'local Stable Audio3 '+('sm-music'if music else'sm-sfx')+'/same-s','offline':True,'steps':12,'cfg':2.5,'prompt':prompt,'guide':str(g.relative_to(ROOT))if g else None,'init_noise_level':.24 if g else None,'sha256':sha(raw)})

def master():
 before=json.loads((ROOT/'source/revision5/audio-before.json').read_text());records=[];out=ROOT/'audio/v5/stems';out.mkdir(exist_ok=True)
 for old in before['stems']:
  key=old['key']
  if key in SPECS:
   a,sr=sf.read(SRC/(key+'-raw.wav'),always_2d=True);g,_=sf.read(SRC/(key+'-guide.wav'),always_2d=True);a=a[:len(g)];a-=a.mean(0);a*=np.sqrt(np.mean(g*g))/max(np.sqrt(np.mean(a*a)),1e-9);a=.55*a+.45*g
  elif key.startswith('thunder_hit'):
   sec=1.12 if key.endswith('advanced')else .90;a=np.zeros((round(sec*SR),2))
   for name,at,db in [('lightning_crack',0,0),('lightning_body',.012,-2),('lightning_tail',.10,-7)]:
    q,_=sf.read(ROOT/'audio/v5/stems'/(name+'.wav'),always_2d=True);n=min(len(q),len(a)-round(at*SR));a[round(at*SR):round(at*SR)+n]+=q[:n]*10**(db/20)
  else:
   a,sr=sf.read(ROOT/old['path'],always_2d=True)
  a-=a.mean(0);fade=min(round(.012*SR),len(a)//5);a[:44]*=np.linspace(0,1,44)[:,None];a[-fade:]*=np.linspace(1,0,fade)[:,None];a*=min(10**(-19/20)/max(np.sqrt(np.mean(a*a)),1e-9),10**(-3/20)/max(abs(a).max(),1e-9));p=out/(key+'.wav');sf.write(p,a,SR,subtype='PCM_16');records.append(dict(key=key,path=str(p.relative_to(ROOT)),duration=len(a)/SR,bytes=p.stat().st_size,sha256=sha(p),sample_rate=SR,channels=2,peak_dbfs=float(20*np.log10(max(abs(a).max(),1e-9))),rms_dbfs=float(20*np.log10(max(np.sqrt(np.mean(a*a)),1e-9))),revision=5 if key in SPECS or key.startswith('thunder_hit')else 4))
 dump(ROOT/'source/revision5/audio-manifest.json',{'model':'local Stable Audio3 sm-sfx/same-s','method':'13 new audio-conditioned physical gesture sources; 55% generated texture / 45% original transient guide; new lightning is layered crack/body/tail','stems':records,'offline':True,'human_listening':False})
 bgm=[]
 for hero,(name,bpm,prompt) in MUSIC.items():
  a,sr=sf.read(SRC/('music-'+hero+'-raw.wav'),always_2d=True);a-=a.mean(0);a*=min(10**(-17/20)/max(np.sqrt(np.mean(a*a)),1e-9),10**(-2/20)/max(abs(a).max(),1e-9));a[:220]*=np.linspace(0,1,220)[:,None];a[-22050:]*=np.linspace(1,0,22050)[:,None];p=ROOT/'audio/v5/bgm'/(hero+'.wav');sf.write(p,a,SR,subtype='PCM_16');bgm.append(dict(hero=hero,name=name,path=str(p.relative_to(ROOT)),requested_bpm=bpm,duration=len(a)/SR,sha256=sha(p),prompt=prompt,model='local Stable Audio3 sm-music/same-s',instrumental=True))
 dump(ROOT/'source/revision5/music.json',{'original':True,'instrumental':True,'human_listening':False,'tracks':bgm});print('MASTERED',len(records),'stems and',len(bgm),'original character themes',flush=True)

def lightning_layers():
 out=ROOT/'audio/v5/stems'
 for key in ['lightning_crack','lightning_body','lightning_tail']:
  a,_=sf.read(SRC/(key+'-raw.wav'),always_2d=True);g,_=sf.read(SRC/(key+'-guide.wav'),always_2d=True);a=a[:len(g)];a-=a.mean(0);a*=np.sqrt(np.mean(g*g))/max(np.sqrt(np.mean(a*a)),1e-9);a=.55*a+.45*g;a*=min(.18/max(np.sqrt(np.mean(a*a)),1e-9),.70/max(abs(a).max(),1e-9));sf.write(out/(key+'.wav'),a,SR,subtype='PCM_16')
if __name__=='__main__':
 if len(sys.argv)>1:worker(sys.argv[1])
 else:
  for key in list(SPECS)+['music-hunapu','music-eileen']:
   with (SRC/(key+'.log')).open('w')as f:r=subprocess.run([sys.executable,'-B',__file__,key],stdout=f,stderr=subprocess.STDOUT)
   if r.returncode:raise RuntimeError((SRC/(key+'.log')).read_text()[-1800:])
   print('GENERATED',key,flush=True)
  lightning_layers();master()
