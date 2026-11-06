"""Local model refinements conditioned on original action envelopes; no downloaded audio."""
import os,sys,json,subprocess,hashlib
from pathlib import Path
import numpy as np,soundfile as sf
from generate_sfx_v4 import SPECS,MODEL,ROOT,SR,NEG,dump,digest
RAW=ROOT/'source/revision4/audio-guided';RAW.mkdir(exist_ok=True)
def guide(key):
 sec=SPECS[key][0];n=round(sec*SR);t=np.arange(n)/SR;u=t/sec;r=np.random.default_rng(7100+list(SPECS).index(key));z=r.normal(0,1,n)
 def band(lo,hi):
  f=np.fft.rfftfreq(n,1/SR);g=(1+(lo/np.maximum(f,1e-6))**6)**-.5*(1+(f/hi)**6)**-.5;g[0]=0;x=np.fft.irfft(np.fft.rfft(z)*g,n);return x/max(np.std(x),1e-9)
 attack=(1-np.exp(-t*500));dec=attack*np.exp(-u*8);swell=np.sin(np.pi*u)**1.3
 if 'step' in key or key in ['run_light','run_armor','landing','arrow_hit','sword_hit']:
  x=.35*band(90,1800)*dec+.12*band(2000,9000)*np.exp(-u*21);x+=.10*np.sin(2*np.pi*95*t)*dec
 elif 'bow_release' in key:
  delay=round(SR/(135 if 'heavy' in key else 215));b=r.uniform(-1,1,delay);x=np.empty(n)
  for i in range(n):j=i%delay;x[i]=b[j];b[j]=.496*(b[j]+b[(j+1)%delay])
  x=x*np.exp(-u*9)*.48+.16*band(1800,10000)*np.sin(np.pi*np.minimum(u*2.3,1))*np.exp(-u*7)
 elif key=='bow_draw':x=.17*band(140,1800)*swell*(.3+.7*np.sin(2*np.pi*(60*t+110*t*t))**2)
 elif 'thunder' in key:
  x=band(800,13000)*(.15*swell if 'gather' in key else .34*dec)*(.25+.75*np.sin(733*t)**8)
  if 'hit' in key:x+=.20*band(45,420)*attack*np.exp(-u*6)
 elif key.startswith('fire') or key.startswith('flame'):
  e=swell if 'gather' in key or 'flight' in key else attack*np.exp(-u*5)
  x=.28*band(90,5200)*e+.13*band(3500,13500)*e*(.25+.75*np.abs(np.sin(210*t)))
 elif key.startswith('holy'):
  e=swell if 'gather' in key else attack*np.exp(-u*5);x=.13*band(2600,13500)*e
  for i,f in enumerate([1177,1643,2411,3329]):x+=.035*np.sin(2*np.pi*(f*t+17*t*t))*e*(.5+.5*np.sin((23+i*7)*t))
 elif 'cloth' in key or 'shield' in key:x=.17*band(300,6000)*swell*(.35+.65*np.sin(56*t)**2)
 else:
  e=swell if 'gather' in key or 'flight' in key else np.sin(np.pi*np.minimum(u*1.4,1))**1.2*np.exp(-u*2)
  lo,hi=(100,3700) if 'heavy' in key else (700,11000)
  if key.startswith('wind'):lo,hi=1700,12500
  x=.28*band(lo,hi)*e
  if 'slash' in key:x+=.035*np.sin(2*np.pi*(2600*t-1900*t*t))*e
 x-=x.mean();x=x/max(abs(x).max(),1e-8)*.65;p=RAW/(key+'-guide.wav');sf.write(p,np.column_stack([x,x]),SR,subtype='PCM_16');return p

def worker(key):
 sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
 raw=RAW/(key+'-raw.wav');g=guide(key)
 if raw.exists():return
 def save(p,a,sample_rate=SR):sf.write(p,a.T,sample_rate,subtype='FLOAT')
 sa3_mlx.save_wav=save
 prompt='TrackType: SFX. '+SPECS[key][1]+' One isolated gesture, physical texture, immediate onset. No music or electronic notification.'
 sys.argv=['sa3_mlx.py','--dit','sm-sfx','--decoder','same-s','--seconds','2.4','--dit-dtype','fp32','--steps','8','--cfg','2.0','--seed',str(8200+list(SPECS).index(key)),'--prompt',prompt,'--negative-prompt',NEG+', ringtone, notification, beep, melody, pure tone','--init-audio',str(g),'--init-noise-level','.35','--out',str(raw)];sa3_mlx.main()
 dump(raw.with_suffix('.json'),{'method':'local model conditioned on original action envelope','guide':str(g.relative_to(ROOT)),'guide_sha256':digest(g),'init_noise_level':.35,'model':'Stable Audio 3 sm-sfx/same-s','steps':8,'offline':True,'prompt':prompt,'sha256':digest(raw)})
def master():
 records=[]
 for key,(sec,description) in SPECS.items():
  a,sr=sf.read(RAW/(key+'-raw.wav'),always_2d=True);g,_=sf.read(RAW/(key+'-guide.wav'),always_2d=True);a=a[:len(g)];a-=a.mean(0);a*=np.sqrt(np.mean(g*g))/max(np.sqrt(np.mean(a*a)),1e-8)
  # Generated texture is the majority; authored guide preserves the single action envelope.
  a=.7*a+.3*g;a[:88]*=np.linspace(0,1,88)[:,None];fade=min(round(.055*SR),len(a)//5);a[-fade:]*=np.linspace(1,0,fade)[:,None]
  a*=min(10**(-19/20)/max(np.sqrt(np.mean(a*a)),1e-9),10**(-3/20)/max(abs(a).max(),1e-9));p=ROOT/'audio/v4/stems'/(key+'.wav');sf.write(p,a,SR,subtype='PCM_16')
  records.append({'key':key,'path':str(p.relative_to(ROOT)),'duration':len(a)/SR,'bytes':p.stat().st_size,'channels':2,'sample_rate':SR,'peak_dbfs':float(20*np.log10(max(abs(a).max(),1e-9))),'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(a*a)),1e-9))),'sha256':digest(p),'description':description,'source':str((RAW/(key+'-raw.wav')).relative_to(ROOT)),'generated_fraction':.7,'original_envelope_fraction':.3})
 dump(ROOT/'source/revision4/audio-manifest.json',{'model':'local Stable Audio 3 sm-sfx/same-s','method':'New audio-conditioned local model generations, 70% generated texture / 30% original physical gesture guide','offline':True,'human_listening':False,'stems':records});print('MASTERED',len(records),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1:worker(sys.argv[1])
 else:
  for key in SPECS:
   with (RAW/(key+'.log')).open('w') as f:r=subprocess.run([sys.executable,'-B',__file__,key],stdout=f,stderr=subprocess.STDOUT)
   if r.returncode:raise RuntimeError((RAW/(key+'.log')).read_text()[-1200:])
   print('REFINED',key,flush=True)
  master()
