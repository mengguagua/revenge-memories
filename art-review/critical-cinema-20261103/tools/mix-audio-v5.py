import json,math,hashlib
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[1];SR=44100
manifest=json.loads((ROOT/'source/revision5/audio-manifest.json').read_text());stems={s['key']:sf.read(ROOT/s['path'],dtype='float32',always_2d=True)[0] for s in manifest['stems']}
cases=json.loads((ROOT/'source/revision4/timeline-input.json').read_text());dest=ROOT/'audio/v5/sfx-mixes';dest.mkdir(parents=True,exist_ok=True);mixes=[]
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
  if j['hero']=='eileen' and advanced:cue(hit-.14,'flame_blade',-1,(-.12,.25));cue(hit,'flame_burst',-1,.25);cue(hit+.015,'sword_hit',-9,.2)
  else:cue(hit-.11,'slash_heavy' if metal else 'slash_light',-1,(-.15,.25),1.11 if j['hero']=='eileen' else 1);cue(hit,'sword_hit',0 if metal else -4,.25)
  cue(5.38,'cloth_turn',-8,.12)
  for n,t in enumerate([5.53,5.894,6.258]):cue(t,'run_armor' if metal else 'run_light',-4,(.12,-.2),1+(n%2)*.035)
  cue(6.63,'step_armor' if metal else 'step_light',-7,-.25)
 elif weapon=='弓':
  if advanced:cue(2.24,'step_armor',-7,-.25);cue(2.58,'landing',-10,-.25)
  cue(3.03 if advanced else 2.65,'bow_draw',-1,-.25)
  release=hit-.65;cue(release,'bow_release_heavy' if advanced else 'bow_release',-1,-.25);cue(hit-.18,'arrow_flight',-2,(-.3,.35));cue(hit,'arrow_hit',2,.28);cue(5.50,'shield_rustle',-12,-.25)
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
 mixes.append({'hero':j['hero'],'hit':j['hit'],'key':j['key'],'path':str(out.relative_to(ROOT)),'duration':len(v)/SR,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'peak_dbfs':20*math.log10(max(float(abs(v).max()),1e-9)),'rms_dbfs':20*math.log10(max(float(np.sqrt(np.mean(v*v))),1e-9)),'events':events})
if len({m['sha256'] for m in mixes})!=len(mixes):raise ValueError('Duplicate attack soundtracks')
music=json.loads((ROOT/'source/revision5/music.json').read_text())['tracks'];themes={m['hero']:sf.read(ROOT/m['path'],dtype='float32',always_2d=True)[0]for m in music}
for m in mixes:
 fx,_=sf.read(ROOT/m['path'],dtype='float32',always_2d=True);n=len(fx);t=np.arange(n)/SR;bed=themes[m['hero']][:n].copy();hit=m['hit']
 # Keep the first beat recognizable, then duck the transient band at cut-in / release / contact.
 gain=np.full(n,10**(-8/20));gain*=np.minimum(1,t/.06)*np.minimum(1,(m['duration']-t)/.28)
 duck_envelope=np.ones(n)
 for e in m['events']:
  if any(x in e['stem']for x in ['slash','sword_hit','bow_release','arrow_hit','thunder_hit','flame_burst']):
   at=e['seconds'];u=(t-at);duck=1-.68*np.exp(-np.maximum(u,0)/.18);duck_envelope=np.minimum(duck_envelope,np.where((u>=-.012)&(u<.65),duck,1))
 gain*=duck_envelope;bed*=gain[:,None];bp=ROOT/'audio/v5/beds'/(m['key']+'.wav');bp.parent.mkdir(exist_ok=True);sf.write(bp,bed,SR,subtype='PCM_16')
 final=fx+bed;peak=float(abs(final).max());master=min(1,10**(-1/20)/max(peak,1e-9));final*=master;fp=ROOT/'audio/v5/mixes'/(m['key']+'.wav');sf.write(fp,final,SR,subtype='PCM_16')
 m['sfx_path']=m['path'];m['path']=str(fp.relative_to(ROOT));m['bed_path']=str(bp.relative_to(ROOT));m['bgm_hero']=m['hero'];m['ducking']='up to 9.9 dB reduction on short weapon/contact transients; music bed nominal -8 dB';m['peak_dbfs']=20*math.log10(max(float(abs(final).max()),1e-9));m['sha256']=hashlib.sha256(fp.read_bytes()).hexdigest();m['master_gain']=master
result={'local_model':'Stable Audio3 sm-sfx / sm-music / same-s','sample_rate':SR,'model_stems':len(stems),'unique_mixes':len(mixes),'music':music,'mixes':mixes};(ROOT/'source/revision5/audio-mixes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(ROOT/'audio-data.js').write_text('window.CinemaAudio='+json.dumps({'stems':manifest['stems'],'music':music,'mixes':[{k:m[k] for k in ['key','path','sfx_path','bed_path','duration','master_gain']}for m in mixes]},ensure_ascii=False)+';\n');print('MIXED',len(mixes),'unique SFX + ducked character theme soundtracks')
