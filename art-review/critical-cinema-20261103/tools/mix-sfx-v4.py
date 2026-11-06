import json,math,hashlib
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[1];SR=44100
manifest=json.loads((ROOT/'source/revision4/audio-manifest.json').read_text());stems={s['key']:sf.read(ROOT/s['path'],dtype='float32',always_2d=True)[0] for s in manifest['stems']}
cases=json.loads((ROOT/'source/revision4/timeline-input.json').read_text());dest=ROOT/'audio/v4/mixes';dest.mkdir(parents=True,exist_ok=True);mixes=[]
for j in cases:
 a=np.zeros((round(j['duration']*SR),2),np.float64);events=[];advanced=j['advanced'];weapon=j['weapon'];hit=j['hit'];metal=advanced and j['hero']=='hunapu'
 def cue(t,key,db=0,pan=0,pitch=1):
  x=stems[key].copy()
  if pitch!=1:x=resample_poly(x,1000,round(1000*pitch),axis=0)
  n=min(len(x),len(a)-round(t*SR))
  if n<=0:return
  x=x[:n];p=np.linspace(pan[0],pan[1],n) if isinstance(pan,tuple) else np.full(n,pan)
  x[:,0]*=np.sqrt(1-p);x[:,1]*=np.sqrt(1+p);a[round(t*SR):round(t*SR)+n]+=x*10**(db/20)
  events.append({'seconds':round(t,4),'stem':key,'gain_db':db,'pan':pan,'pitch_ratio':pitch,'duration':n/SR})
 cue(.63,'cutin',-8,(-.2,.15))
 if weapon=='剑':
  cue(2.18,'step_armor' if metal else 'step_light',-4,-.25);cue(2.30,'shield_rustle' if j['hero']=='hunapu' else 'cloth_turn',-10,-.25)
  start=3.20 if metal else 2.75;cue(start,'dash_heavy' if metal else 'dash_light',-3,(-.3,.05))
  for t in ([3.2,3.43,3.66] if metal else [2.75,3.04]):cue(t,'step_armor' if metal else 'step_light',-7,-.2)
  if j['hero']=='eileen' and not advanced:cue(3.78,'cloth_turn',-10,.0);cue(hit+.06,'landing',-4,.16)
  if j['hero']=='eileen' and advanced:cue(hit-.24,'flame_blade',-1,(-.12,.25));cue(hit,'flame_burst',-1,.25);cue(hit+.015,'sword_hit',-9,.2)
  else:cue(hit-.23,'slash_heavy' if metal else 'slash_light',-1,(-.15,.25),1.11 if j['hero']=='eileen' else 1);cue(hit,'sword_hit',0 if metal else -4,.25)
  cue(5.38,'cloth_turn',-8,.12)
  for n,t in enumerate([5.53,5.894,6.258]):cue(t,'run_armor' if metal else 'run_light',-4,(.12,-.2),1+(n%2)*.035)
  cue(6.63,'step_armor' if metal else 'step_light',-7,-.25)
 elif weapon=='弓':
  if advanced:cue(2.24,'step_armor',-7,-.25);cue(2.58,'landing',-10,-.25)
  cue(2.74 if advanced else 2.18,'bow_draw',-1,-.25)
  release=hit-.65;cue(release,'bow_release_heavy' if advanced else 'bow_release',-1,-.25);cue(release+.06,'arrow_flight',-4,(-.3,.35));cue(hit,'arrow_hit',-1,.28);cue(5.50,'shield_rustle',-12,-.25)
 else:
  kind=j['spell'];gather={'fire':2.15,'holy':2.35,'thunder':2.55,'wind':2.2}[kind];cue(gather,kind+'_gather',-2,-.25)
  if kind=='fire':cue(3.30,'fire_flight',-3,(-.25,.28))
  elif kind=='wind':cue(3.35,'wind_flight',-1,(-.25,.28))
  elif kind=='holy':cue(3.30,'holy_gather',-9,(-.1,.18),1.08 if advanced else 1)
  elif kind=='thunder':cue(hit-.23,'thunder_gather',-8,.25,1.2)
  cue(hit,kind+'_hit'+('_advanced' if advanced else ''),0,.25);cue(5.55,'cloth_turn',-15,-.25)
 a-=a.mean(axis=0);rms=float(np.sqrt(np.mean(a*a)));peak=float(abs(a).max());gain=min(10**(-19/20)/max(rms,1e-9),10**(-1/20)/max(peak,1e-9));a*=gain;a[:220]*=np.linspace(0,1,220)[:,None];a[-440:]*=np.linspace(1,0,440)[:,None]
 out=dest/(j['key']+'.wav');sf.write(out,a,SR,subtype='PCM_16');v,_=sf.read(out,dtype='float32',always_2d=True)
 if not np.isfinite(v).all() or abs(v).max()>=1:raise ValueError(j['key'])
 mixes.append({'key':j['key'],'path':str(out.relative_to(ROOT)),'duration':len(v)/SR,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'peak_dbfs':20*math.log10(max(float(abs(v).max()),1e-9)),'rms_dbfs':20*math.log10(max(float(np.sqrt(np.mean(v*v))),1e-9)),'events':events})
if len({m['sha256'] for m in mixes})!=len(mixes):raise ValueError('Duplicate attack soundtracks')
result={'local_model':'Stable Audio3 sm-sfx/same-s','sample_rate':SR,'model_stems':len(stems),'unique_mixes':len(mixes),'mixes':mixes};(ROOT/'source/revision4/audio-mixes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(ROOT/'audio-data.js').write_text('window.CinemaAudio='+json.dumps({'stems':manifest['stems'],'mixes':[{k:m[k] for k in ['key','path','duration']} for m in mixes]},ensure_ascii=False)+';\n');print('MIXED',len(mixes),'distinct attack soundtracks from',len(stems),'new local model stems')
