#!/usr/bin/env python3
"""Reference-analysed additive/noise SFX synthesis (no copied PCM)."""
import argparse
from pathlib import Path
import json
import shutil
import numpy as np
import soundfile as sf
from scipy.signal import stft,medfilt,butter,sosfilt
import generate_original_sfx as g

ROOT=g.ROOT;SOURCE=ROOT/'source/sfx-20261024/audio-guided'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ids',nargs='+')
    args=parser.parse_args()
    outdir=SOURCE/'candidates';outdir.mkdir(parents=True,exist_ok=True)
    for t in g.tracks():
        if args.ids:
            if t['id'] not in args.ids and t['request'] not in args.ids:continue
        elif t['request'] not in {'10','11','12','13','25','54'}:continue
        old=ROOT/'actual'/t['old_paths'][0].removeprefix('res://')
        original,sr=sf.read(old,dtype='float32',always_2d=True)
        mono=original.mean(axis=1)
        f,times,z=stft(mono,sr,nperseg=1024,noverlap=804,boundary='zeros')
        band=(f>=400)&(f<=4000);power=np.abs(z[band]);freq=f[band][power.argmax(axis=0)]
        energy=np.sqrt((np.abs(z)**2).sum(axis=0))
        active=energy>energy.max()*.08
        freq=medfilt(freq,3)
        freq=np.interp(times,times[active],freq[active])
        env,dt=g.envelope(original)
        last=int(np.flatnonzero(env>max(float(env.max())*.025,10**(-60/20)))[-1])
        duration=min(len(original)/sr,(last+1)*dt+.018)
        n=int(duration*sr);axis=np.arange(n)/sr
        pitch=np.interp(axis,times,freq)
        phase=np.cumsum(2*np.pi*pitch/sr)
        # A new rounded pulse colour with deliberately restrained upper harmonics.
        tone=np.sin(phase)+.16*np.sin(3*phase)+.035*np.sin(5*phase)
        noise_weight=0.
        if t['request'] not in {'10','11','12','13','25','54'}:
            spectrum=(np.abs(z[:,active])**2).mean(axis=1)
            usable=(f>400)&(f<7500)
            flatness=float(np.exp(np.log(np.maximum(spectrum[usable],1e-15)).mean())/max(float(spectrum[usable].mean()),1e-15))
            noise_weight=float(np.clip(flatness*2,.08,.7))
            noise=np.random.default_rng(2026102800+int(t['request'],16)).normal(0,1,n)
            noise=sosfilt(butter(3,[600,7000],btype='bandpass',fs=sr,output='sos'),noise)
            noise/=max(float(np.sqrt(np.mean(noise**2))),1e-9)
            noise=np.tanh(noise/1.2)
            noise/=max(float(np.sqrt(np.mean(noise**2))),1e-9)
            tone=tone*(1-noise_weight)+noise*noise_weight
        contour=np.interp(axis,(np.arange(len(env))+.5)*dt,env,left=env[0],right=0.)
        smooth=np.convolve(contour,np.ones(89)/89,mode='same')
        a=tone*smooth
        a[:44]*=np.linspace(0,1,44)
        a[-441:]*=.5+.5*np.cos(np.linspace(0,np.pi,441))
        a=np.repeat(a[:,None],2,axis=1).astype(np.float32)
        ev,_=g.envelope(a);selected=ev[ev>max(float(ev.max())*.03,10**(-55/20))]
        rms=g.db(np.sqrt(np.mean(selected**2)));peak=g.db(np.abs(a).max());target,ceiling=g.limits(t)
        shaping=False
        if (target-rms)-(ceiling-peak)>2 and t['request'] not in {'10','11','12','13','25','54'}:
            local=np.interp(axis,(np.arange(len(ev))+.5)*dt,np.convolve(ev,np.ones(5)/5,mode='same'))
            knee=np.maximum(local*2.3,float(local.max())*.02)[:,None]
            a=knee*np.tanh(a/knee);ev,_=g.envelope(a)
            selected=ev[ev>max(float(ev.max())*.03,10**(-55/20))]
            rms=g.db(np.sqrt(np.mean(selected**2)));peak=g.db(np.abs(a).max());shaping=True
        gain=min(target-rms,ceiling-peak);a*=10**(gain/20)
        master=SOURCE/'ui-synthesis'/(t['id']+'_float.wav');master.parent.mkdir(parents=True,exist_ok=True)
        sf.write(master,a,sr,subtype='FLOAT')
        path=outdir/(t['id']+'.ogg')
        if path.exists():
            history=SOURCE/'history'/g.digest(path);history.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,history/path.name)
            if path.with_suffix('.json').exists():shutil.copy2(path.with_suffix('.json'),history/path.with_suffix('.json').name)
        with sf.SoundFile(path,mode='w',samplerate=sr,channels=2,format='OGG',subtype='VORBIS',compression_level=.6) as file:
            for start in range(0,len(a),8192):file.write(a[start:start+8192])
        decoded,_=sf.read(path,dtype='float32',always_2d=True)
        metrics=g.measure(path,decoded,SOURCE/'logs'/(t['id']+'_candidate_decoded.log'))
        record={'id':t['id'],'request':t['request'],'path':str(path.relative_to(ROOT)),
                'sha256':g.digest(path),'bytes':path.stat().st_size,
                'source':{'method':'reference-analysed pitch/envelope with new additive and band-limited noise synthesis',
                          'reference_path':str(old.relative_to(ROOT)),'reference_sha256':g.digest(old),
                          'source_path':str(master.relative_to(ROOT)),'copied_pcm':False,
                          'oscillator':'sin(f) + 0.16 sin(3f) + 0.035 sin(5f)',
                          'noise_weight':noise_weight,
                          'frequency_range_hz':[float(pitch.min()),float(pitch.max())]},
                'mastering':{'gain_db':gain,'target_active_rms_dbfs':target,'peak_ceiling_dbfs':ceiling,
                             'smooth_local_crest_control':shaping},'metrics':metrics}
        g.dump(path.with_suffix('.json'),record)
        print(t['id'],duration,metrics['active_rms_dbfs'],flush=True)
if __name__=='__main__':main()
