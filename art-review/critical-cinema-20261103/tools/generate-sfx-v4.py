"""New offline Stable Audio 3 sound design for the isolated cinema preview."""
import os,sys,json,time,hashlib,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODEL=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx')
RAW=ROOT/'source/revision4/audio';OUT=ROOT/'audio/v4/stems';SR=44100
for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[key]='1'
SPECS={
'step_light':(.32,'One light leather boot planted on dry stone, short sole tap with a little gritty scuff, no march.'),
'step_armor':(.40,'One heavy armored boot stomp onto stone, compact solid footfall and a small metal armor rattle, no explosion.'),
'run_light':(.30,'One quick running leather boot footfall on stone with a little cloth swish, crisp light contact, only one footstep.'),
'run_armor':(.34,'One fast armored running boot contact on stone, tight leather thud with small loose plate jingle, only one footstep.'),
'dash_light':(.65,'One fast body dash past the listener, airy rushing cloth and a short gritty ground skid, agile acceleration, no impact.'),
'dash_heavy':(.80,'One powerful armored forward lunge, broad wind rush and layered moving armor scrape, hard fast acceleration, no impact.'),
'slash_light':(.60,'One agile narrow steel sword cutting through air, sharp swift upper-mid metallic swish, clean short release, no bell.'),
'slash_heavy':(.78,'One broad heavy steel sword slash, dense low-mid air sweep and sharp silver metallic cutting edge, no ringing note.'),
'sword_hit':(.58,'One crisp fantasy sword contact, compact metallic crack mixed with a short gritty hit, immediate dry decay, no blood or voice.'),
'landing':(.44,'One light two-foot landing on stone, close dry leather thud and tiny gravel scrape, compact and restrained.'),
'cloth_turn':(.44,'One quick turn in a thick traveling cloak, short dry cloth rustle and leather creak, no impact or footsteps.'),
'bow_draw':(.80,'One wooden recurve bow slowly drawn taut, tense elastic string friction rising with a quiet wooden limb creak, no release.'),
'bow_release':(.48,'One recurve bowstring snapping forward, tight dry elastic twang and a swift arrow air hiss, one shot only, no gun.'),
'bow_release_heavy':(.62,'One powerful longbow string release, rich tense low elastic snap and strong arrow hiss, one shot, no gun or explosion.'),
'arrow_flight':(.66,'One narrow arrow passing rapidly through air, clean focused high-frequency air whistle and hiss, not a rocket.'),
'arrow_hit':(.38,'One arrow penetrating a hard target, tight dry pointed thunk with a little brittle crack, no gun or sword.'),
'flame_blade':(.90,'One flaming steel sword sweep: a sharp metallic blade swish woven with an energetic fiery whoosh and brief crackle.'),
'flame_burst':(1.00,'One compact fire explosion mixed with a sharp sword impact: bright ignition crack, forceful flame rush then tiny embers. No long rumble.'),
'fire_gather':(1.10,'A compact magical fire orb gathering energy, rising warm flame pressure with soft red-hot crackles, no impact.'),
'fire_flight':(1.20,'A single flying fireball rushing steadily through air, fiery fluttering whoosh and crackling tail, no impact or explosion.'),
'fire_hit':(.90,'One small magical fireball striking a target, quick warm flame ignition puff, round fiery burst and short ember decay.'),
'fire_hit_advanced':(1.10,'One powerful concentrated fire orb impact, dense bright flame pressure blast with sharp crackles and a short clear ember decay.'),
'holy_gather':(1.15,'Tiny magical fireflies gathering, delicate airy shimmering energy with soft high electronic flutter, no melody or bells.'),
'holy_hit':(.95,'One pale green magical light ring opening, soft bright airy scattering sparkle, small glowing motes fading, no music.'),
'holy_hit_advanced':(1.15,'One strong radiant light convergence then scattering, full airy luminous pulse with intricate high sparkling grains, no choir or bells.'),
'thunder_gather':(.95,'A short electrical charge rising, tense blue-white static crackle and restrained low buzzing pressure, no impact.'),
'thunder_hit':(.95,'One lightning bolt striking stone: immediate sharp electric crack, compact ground thud, then branching electric fizz dying away.'),
'thunder_hit_advanced':(1.20,'One powerful lightning ground strike, very sharp electric crack and deep compact pressure hit, branching arcs crackling outward then decay. One bolt only.'),
'wind_gather':(.85,'One magical crescent wind blade forming and rotating in place, rising narrow airy spinning whistle, no impact.'),
'wind_flight':(.90,'One razor thin crescent of wind flying past, focused cutting air hiss with a light rotating flutter, no sword metal.'),
'wind_hit':(.64,'One magical wind blade cutting through a target, crisp airy slicing snap and short spreading wind ribbons, no explosion.'),
'wind_hit_advanced':(.90,'One powerful compressed wind crescent impact, broad sharp airy cutting burst with several brief fine swirling air grains, one hit only.'),
'cutin':(.36,'One short dramatic fantasy game cut-in air sweep, restrained low whoosh with a crisp bright ending, no impact or melody.'),
'shield_rustle':(.40,'One compact movement of a strapped metal shield and arm armor, dry leather strap creak and quiet metal clink, not a block impact.'),
}
NEG='music, song, melody, speech, voice, vocals, singing, choir, crowd, background ambience, gunshot, repeated attacks, multiple impacts, drum beat, long cinematic reverb'
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worker(key):
 import numpy as np,soundfile as sf
 for name in ['t5gemma_f16.npz','dit_sm-sfx_f16.npz','same_s_decoder_f32.npz']:
  if not (MODEL/'models/mlx'/name).is_file():raise FileNotFoundError(name)
 RAW.mkdir(parents=True,exist_ok=True);raw=RAW/(key+'-raw.wav')
 if raw.exists():return
 sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
 def save_float(p,a,sample_rate=SR):
  if not np.isfinite(a).all():raise ValueError('Nonfinite local model output')
  sf.write(p,a.T,sample_rate,subtype='FLOAT')
 sa3_mlx.save_wav=save_float
 seed=20261103400+list(SPECS).index(key);prompt='TrackType: SFX. '+SPECS[key][1]+' Isolated fantasy game sound effect, immediate clear onset, short natural release then silence. No voice or music.'
 sys.argv=['sa3_mlx.py','--dit','sm-sfx','--decoder','same-s','--seconds','2.4','--dit-dtype','fp32','--steps','8','--cfg','2.0','--seed',str(seed),'--prompt',prompt,'--negative-prompt',NEG,'--out',str(raw)]
 start=time.monotonic();sa3_mlx.main();dump(raw.with_suffix('.json'),{'key':key,'model':'local Stable Audio 3 sm-sfx / same-s','offline':True,'weights_reused':str(MODEL),'seed':seed,'steps':8,'cfg':2.,'dit_dtype':'fp32','prompt':prompt,'negative_prompt':NEG,'wall_seconds':round(time.monotonic()-start,3),'sha256':digest(raw)})
def master():
 import numpy as np,soundfile as sf
 OUT.mkdir(parents=True,exist_ok=True);records=[]
 for key,(seconds,description) in SPECS.items():
  raw=RAW/(key+'-raw.wav');a,sr=sf.read(raw,dtype='float32',always_2d=True)
  if sr!=SR or not np.isfinite(a).all():raise ValueError(key)
  a-=a.mean(axis=0);hop=220;env=np.sqrt(np.mean(a[:len(a)//hop*hop].reshape(-1,hop,a.shape[1])**2,axis=(1,2)));active=np.where(env>max(float(env.max())*.13,1e-5))[0]
  if not len(active):raise ValueError('silent '+key)
  start=max(0,int(active[0])*hop-round(.012*SR));n=round(seconds*SR);a=a[start:start+n].copy()
  if len(a)<n:a=np.pad(a,((0,n-len(a)),(0,0)))
  fade=min(round(.04*SR),n//5);a[:88]*=np.linspace(0,1,88)[:,None];a[-fade:]*=np.linspace(1,0,fade)[:,None]
  peak=float(abs(a).max());rms=float(np.sqrt(np.mean(a*a)));gain=min(10**(-19/20)/max(rms,1e-9),10**(-3/20)/max(peak,1e-9));a*=gain
  out=OUT/(key+'.wav');sf.write(out,a,SR,subtype='PCM_16');decoded,_=sf.read(out,dtype='float32',always_2d=True)
  records.append({'key':key,'path':str(out.relative_to(ROOT)),'duration':len(decoded)/SR,'bytes':out.stat().st_size,'sample_rate':SR,'channels':decoded.shape[1],'peak_dbfs':20*math.log10(max(float(abs(decoded).max()),1e-9)),'rms_dbfs':20*math.log10(max(float(np.sqrt(np.mean(decoded**2))),1e-9)),'trimmed_leading_seconds':start/SR,'generated_source':str(raw.relative_to(ROOT)),'sha256':digest(out),'description':description})
 dump(ROOT/'source/revision4/audio-manifest.json',{'model':'local Stable Audio 3 sm-sfx/same-s','all_stems_new_model_generations':True,'no_procedural_substitute':True,'offline':True,'stems':records});print('MASTERED',len(records),'new model stems',flush=True)
def generate():
 RAW.mkdir(parents=True,exist_ok=True)
 for key in SPECS:
  with (RAW/(key+'.log')).open('w') as log:r=subprocess.run([sys.executable,'-B',__file__,'worker',key],stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError((RAW/(key+'.log')).read_text()[-4000:])
  print('GENERATED',key,flush=True)
 master()
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='worker':worker(sys.argv[2])
 elif len(sys.argv)>1 and sys.argv[1]=='master':master()
 else:generate()
