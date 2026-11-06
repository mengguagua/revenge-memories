#!/usr/bin/env python3
"""Small owned movement cue; preserve all legacy request aliases and assets."""
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/iphone16-feedback-20261024'
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sr=44100;t=np.arange(round(.085*sr))/sr
    rng=np.random.default_rng(2026102420)
    noise=sosfilt(butter(2,[250,1800],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,len(t)))
    phase=2*np.pi*(150*t-260*t*t)
    body=.36*np.sin(phase)*np.exp(-t/.017)
    a=(noise*.9+body)*np.minimum(1,t/.0025)*np.exp(-t/.020)
    a[-220:]*=np.linspace(1,0,220)
    a*=10**(-30.5/20)/np.sqrt(np.mean(a*a))
    path=ROOT/'actual/assets/sfx/20261024/rm_map_step.ogg'
    stereo=np.stack([a,a],axis=1).astype(np.float32)
    with sf.SoundFile(path,'w',samplerate=sr,channels=2,format='OGG',subtype='VORBIS') as f:f.write(stereo)
    decoded,_=sf.read(path,always_2d=True)
    assert np.isfinite(decoded).all() and np.abs(decoded).max()<1
    sf.write(OUT/'map-step.wav',decoded,sr,subtype='PCM_16')
    recipe={'method':'new deterministic filtered-noise and damped-tone synthesis; no source recording',
            'seed':2026102420,'duration_seconds':len(decoded)/sr,'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(decoded**2)))),
            'sample_peak_dbfs':float(20*np.log10(np.abs(decoded).max())),
            'path':'res://assets/sfx/20261024/rm_map_step.ogg','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'human_listening':False}
    dump(OUT/'map-step.json',recipe)
    p=ROOT/'actual/data/sound_effects.json';data=json.loads(p.read_text())
    data.setdefault('gameplay_effects',{})['map_step']={**recipe,'default_enabled':True,'loop':False,'manual_stop':False}
    dump(p,data)
    p=ROOT/'actual/data/soundtrack.json';score=json.loads(p.read_text());base=score['tracks']['rm_battle_final']
    score.setdefault('additional_tracks',{})['rm_duel_urgent']={
        'title':'交锋 · 疾进','kind':'bgm','path':base['path'],'loop':True,'loop_offset':0.0,
        'playback_pitch_scale':1.12,'source_asset_id':'rm_battle_final','source_sha256':base['sha256'],
        'arrangement':'Reuse the owned final-battle cue at 1.12x playback rate (~164 BPM); not a new recording or extra original-game request.'}
    score['routing']['duel_attack']='rm_duel_urgent'
    dump(p,score)
    print(json.dumps(recipe))

if __name__=='__main__':main()
