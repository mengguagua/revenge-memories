#!/usr/bin/env python3
"""Local scene-led music revisions, using new owned guides for short jingles."""
from __future__ import annotations
import argparse
import json
import os
import shutil
from pathlib import Path
import sys
import time
import generate_original_soundtrack as g

ROOT=g.ROOT;SR=g.SR;SOURCE=ROOT/'source/audio-20261024/content-review'
for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[key]='1'

BATTLE={
 'rm_prologue':'A restrained ceremonial festival march. A bright noble pulse lead above a quietly uneasy bass counterpoint; a joyful surface with an approaching shadow. No jump scare or cinematic drone.',
 'rm_battle_snow':'A determined, urgent escort march for inexperienced volunteers. Clear minor-key pulse melody and steady forward motion.',
 'rm_battle_tide':'A brisk nautical battle march for escorting ships and rescuing captives. Straight driving pulse, never reggae or a relaxed groove.',
 'rm_battle_revenge':'A firm, tense minor-key confrontation march. Anger held under control, decisive rhythmic drive, never relaxed jazz.',
 'rm_battle_refuge':'An urgent defensive minor-key battle theme for protecting an evacuation. Restless forward movement, clear short melodic calls.',
 'rm_battle_two_fronts':'Two short original pulse melodies answer each other in tight counterpoint, expressing coordinated effort and investigation during battle.',
 'rm_battle_sun_tower':'A stern minor-key battle march for a conflicted confrontation with former comrades. Serious and restrained but clearly urgent.',
 'rm_battle_circuit':'An eerie minor-key battle melody for a dangerous ancient facility. Steady urgent pulse, sparse mysterious counterpoint, no dance groove.',
 'rm_battle_ascent':'A purposeful, energetic rescue march. Two original pulse melodies join in determined counterpoint as allies advance together.',
 'rm_battle_final':'A serious, driving final confrontation in a minor mode. Powerful interlocking pulse melodies, spare four-voice texture, no huge drums or cinematic layers.'}

def guide(t):
    """Compose original, resolved utility phrases; no reference melody is used."""
    import numpy as np
    import soundfile as sf
    a=np.zeros((int(4.2*SR),2),np.float32)
    def note(midi,start,length,level=.15,triangle=False,pan=0.):
        n=int(length*SR);x=np.arange(n)/SR;freq=440*2**((midi-69)/12)
        phase=2*np.pi*freq*x
        wave=(np.sin(phase)-np.sin(3*phase)/9+np.sin(5*phase)/25 if triangle else
              np.sin(phase)+.24*np.sin(3*phase)+.07*np.sin(5*phase))
        attack=np.minimum(1.,x/.004);release=np.minimum(1.,np.maximum(0.,length-x)/.09)
        env=attack*release*np.exp(-x/max(length*2,.25))
        v=wave*env*level;at=int(start*SR);count=min(n,len(a)-at)
        if count>0:a[at:at+count]+=v[:count,None]*np.array([1-pan,1+pan])[None]
    role=t['id']
    if role=='rm_jingle_victory':
        melody=[(74,0,.20),(81,.20,.20),(78,.40,.20),(81,.60,.20),(86,.80,.34),(85,1.14,.18),(83,1.32,.18),(81,1.5,.22),(86,1.72,.90)]
        chord=[50,62,66,69];end=2.9
    elif role=='rm_jingle_growth':
        melody=[(79,0,.20),(83,.20,.20),(86,.40,.25),(91,.65,.80)]
        chord=[55,67,71,74];end=2.1
    elif role=='rm_jingle_award':
        melody=[(72,0,.24),(76,.24,.24),(79,.48,.24),(83,.72,.28),(84,1.,.85)]
        chord=[48,60,64,67];end=2.4
    else:
        melody=[(76,0,.28),(72,.28,.28),(74,.56,.28),(72,.84,.28),(69,1.12,.90)]
        chord=[45,57,60,64];end=2.6
    for midi,start,length in melody:note(midi,start,length,.16,False,-.05)
    for i,midi in enumerate(chord):note(midi,.08 if i else 0.,end-.24,.065 if i else .12,True,.03)
    if role!='rm_jingle_wounded':
        for pos in [0.,.4,.8]:note(chord[0]-12,pos,.11,.055,True)
    peak=float(np.abs(a).max());a*=.62/max(peak,1e-9)
    out=SOURCE/'guides'/(role+'.wav');out.parent.mkdir(parents=True,exist_ok=True)
    sf.write(out,a,SR,subtype='PCM_16')
    g.dump(out.with_suffix('.json'),{'id':role,'method':'newly composed additive-synthesis guide',
           'melody_midi_start_duration':melody,'chord_midi':chord,'active_end_seconds':end,
           'reference_audio_used':False,'sha256':g.digest(out)})
    return out,end

def battle_guide(t,revision=2):
    """New sixteen-bar four-voice arrangements; no source recording or melody."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter,sosfilt
    themes={
      'rm_prologue':(65,[0,4,2,0,1,2,3,4],'major'),
      'rm_battle_snow':(62,[0,2,4,3,2,0,1,2],'minor'),
      'rm_battle_tide':(64,[4,2,1,0,2,4,5,4],'dorian'),
      'rm_battle_revenge':(67,[0,0,4,3,2,4,2,0],'minor'),
      'rm_battle_refuge':(69,[4,3,2,1,0,2,1,0],'minor'),
      'rm_battle_two_fronts':(65,[0,2,1,3,2,4,3,1],'minor'),
      'rm_battle_sun_tower':(62,[0,4,3,2,1,0,2,1],'minor'),
      'rm_battle_circuit':(61,[0,1,4,3,1,0,5,4],'harmonic_minor'),
      'rm_battle_ascent':(64,[0,2,4,5,4,2,3,4],'minor'),
      'rm_battle_final':(60,[0,4,2,6,5,4,3,1],'harmonic_minor')}
    root,cell,mode=themes[t['id']]
    scale={'major':[0,2,4,5,7,9,11],'minor':[0,2,3,5,7,8,10],
           'dorian':[0,2,3,5,7,9,10],'harmonic_minor':[0,2,3,5,7,8,11]}[mode]
    beat=60/float(t['bpm']);period=16*4*beat;n=round(period*SR)
    a=np.zeros((n,2),np.float32);events=[]
    def pitch(degree,octave=0):return root+scale[degree%7]+12*(degree//7+octave)
    def note(midi,start,length,level,wave='pulse',pan=0.):
        at=round(start*SR);count=min(round(length*SR),n-at)
        if count<=0:return
        x=np.arange(count)/SR;phase=2*np.pi*(440*2**((midi-69)/12))*x
        if wave=='triangle':
            v=np.sin(phase)-np.sin(3*phase)/9+np.sin(5*phase)/25
        elif revision>=2:
            duty=.25 if pan<0 else .5
            v=sum(np.sin(np.pi*h*duty)/(h*np.sin(np.pi*duty))*np.cos(h*(phase-np.pi*duty))
                  for h in range(1,10))
        else:v=np.sin(phase)+.24*np.sin(3*phase)+.07*np.sin(5*phase)
        attack=.001 if revision>=2 else .003
        release=(.008 if wave=='triangle' else .018) if revision>=2 else .035
        env=np.minimum(1.,x/attack)*np.minimum(1.,np.maximum(0.,length-x)/release)
        v=v*env*level
        a[at:at+count]+=v[:,None]*np.array([1-pan,1+pan])[None]
        events.append([midi,round(start,5),round(length,5),wave])
    progression=[0,0,5,5,3,3,4,4,0,5,3,4,3,4,4,4]
    rhythms=[[.5,.5,1,.5,.5,1],[.75,.25,.5,.5,1,1],
             [1,.5,.5,.5,.5,1],[.5,.5,.5,.5,.5,.5,1]]
    rng=np.random.default_rng(2026102900+list(themes).index(t['id']))
    for bar,chord in enumerate(progression):
        rhythm=rhythms[(bar//4+bar%2)%4];position=0.
        for j,duration in enumerate(rhythm):
            degree=chord+cell[(j+(bar%4)*2)%8]
            midi=pitch(degree)
            if revision>=3 and bar==15 and j==len(rhythm)-1:
                # A short leading tone resolves upward into the next tonic,
                # avoiding the previous octave leap at the wrapped boundary.
                midi=root-1
            note(midi, (bar*4+position)*beat,duration*beat*(.94 if revision>=2 else .88),.14,'pulse',-.06)
            position+=duration
        # The answering voice remains below the lead, leaving clean space.
        for j,offset in enumerate([2,4,2,0]):
            note(pitch(chord+offset,-1),(bar*4+j+.10)*beat,(.82 if revision>=2 else .70)*beat,.065,'pulse',.06)
        for j in range(8):
            note(pitch(chord+(4 if j%4==2 else 0),-1),(bar*4+j*.5)*beat,(.49 if revision>=2 else .38)*beat,.115,'triangle')
        for j in range(4):
            count=round(.075*SR);noise=rng.normal(0,1,count)
            band=[450,1400] if j%2==0 else [1600,5800]
            noise=sosfilt(butter(2,band,btype='bandpass',fs=SR,output='sos'),noise)
            drum=(.060 if t['id']=='rm_prologue' else .090) if revision>=2 else (.020 if t['id']=='rm_prologue' else .032)
            noise=np.tanh(noise*1.4)*np.exp(-np.arange(count)/SR/.020)*drum
            at=round((bar*4+j)*beat);count=min(count,n-at)
            a[at:at+count]+=noise[:count,None]
    a*=.62/max(float(np.abs(a).max()),1e-9)
    # Post-roll is the next beginning, so the model sees the planned loop.
    post=min(round(.32*SR),n);extended=np.concatenate([a,a[:post]])
    out=SOURCE/'guides'/(t['id']+(f'_v{revision}' if revision>=2 else '')+'.wav');out.parent.mkdir(parents=True,exist_ok=True)
    sf.write(out,extended,SR,subtype='PCM_16')
    g.dump(out.with_suffix('.json'),{'id':t['id'],'method':'new sixteen-bar four-voice composition',
           'bpm':t['bpm'],'time_signature':'4/4','bars':16,'period_frames':n,'period_seconds':n/SR,'voicing_revision':revision,
           'mode':mode,'root_midi':root,'motif_scale_degrees':cell,'chord_scale_degrees':progression,
           'notes':events,'reference_audio_used':False,'sha256':g.digest(out)})
    return out,n/SR

def worker(ident,seed):
    import numpy as np
    import soundfile as sf
    t=next(t for t in g.tracks() if t['id']==ident)
    SOURCE.mkdir(parents=True,exist_ok=True);(SOURCE/'.gdignore').touch()
    out=SOURCE/'raw'/f'{ident}_{seed}_float.wav';out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    base=('TrackType: Music, VocalType: Instrumental. Original early-console 8-bit fantasy tactics soundtrack. '
          'Strict sparse four-channel chiptune: two warm pulse-wave melody and harmony voices, '
          'one rounded triangle bass voice, and quiet band-limited noise percussion. '
          'Dry direct electronic tone, clear monophonic lines, memorable NEW melody. '
          'Straight rhythm, no swing, no jazz, no reggae. No acoustic instruments, no piano, '
          'no guitar, no flute, no orchestral pad, no realistic drum kit, no voice or choir. ')
    extra=[];guide_info=None
    if t['kind']=='jingle':
        path,end=guide(t);guide_info={'path':str(path.relative_to(ROOT)),'sha256':g.digest(path),'active_end_seconds':end}
        purpose={'rm_jingle_victory':'a clear major-key task-completion fanfare, relief and resolve',
                 'rm_jingle_growth':'a bright rising major arpeggio marking growth',
                 'rm_jingle_award':'a warm rising handover phrase with a resolved final tonic',
                 'rm_jingle_wounded':'a short gentle minor phrase conveying concern for a living wounded companion, never a funeral'}[ident]
        prompt=base+purpose+'. Preserve the supplied new guide melody and its completed final cadence; one phrase followed by a short natural release, then silence.'
        seconds=4.2;extra=['--init-audio',str(path),'--init-noise-level','0.35']
    else:
        prompt=base+f"{t['bpm']} BPM. "+BATTLE.get(ident,'Clear measured forward motion with a restrained original melody for '+t['scene']+'.')
        prompt+=' Repeating complete eight-bar phrases, A A B A form, stable accompaniment, no introduction or fadeout.'
        path,period=battle_guide(t)
        guide_info={'path':str(path.relative_to(ROOT)),'sha256':g.digest(path),'period_seconds':period,'period_frames':round(period*SR)}
        seconds=period+.32;extra=['--init-audio',str(path),'--init-noise-level','0.35']
    sys.path.insert(0,str(g.MODEL/'scripts'));import sa3_mlx
    captured={}
    def save(path,audio,sample_rate=SR):
        if not np.isfinite(audio).all():raise ValueError('Nonfinite generated music')
        captured.update(raw_peak=float(np.abs(audio).max()),raw_rms=float(np.sqrt(np.mean(audio**2))))
        sf.write(path,audio.T,sample_rate,subtype='FLOAT')
    sa3_mlx.save_wav=save
    sys.argv=['sa3_mlx.py','--dit','sm-music','--decoder','same-s','--seconds',str(seconds),
              '--dit-dtype','fp32','--steps','8','--cfg','2.0','--seed',str(seed),'--prompt',prompt,
              '--negative-prompt','vocals, speech, choir, jazz, swing, reggae, piano, acoustic guitar, acoustic drums, flute, orchestral strings, reverb, long introduction',
              '--out',str(out),*extra]
    start=time.monotonic();sa3_mlx.main()
    g.dump(out.with_suffix('.json'),{'track_id':ident,'seed':seed,'model':'local Stable Audio 3 sm-music/same-s',
            'method':'owned-guide audio-conditioned generation' if guide_info else 'new text-to-music composition',
            'guide':guide_info,'prompt':prompt,'seconds':seconds,'cfg':2.,'steps':8,'dit_dtype':'fp32',
            'sha256':g.digest(out),'source_format':'FLOAT WAV','offline':True,
            'generation_wall_seconds':round(time.monotonic()-start,3),**captured})

def master(ident,seed,retimbre=False):
    import numpy as np
    import soundfile as sf
    t=next(t for t in g.tracks() if t['id']==ident)
    raw=SOURCE/'raw'/f'{ident}_{seed}_float.wav';source=json.loads(raw.with_suffix('.json').read_text())
    audio,sr=sf.read(raw,dtype='float32',always_2d=True)
    if t['kind']=='jingle':
        own,_=sf.read(ROOT/source['guide']['path'],dtype='float32',always_2d=True)
        count=min(len(audio),len(own));own=own[:count];audio=audio[:count]
        scale=np.sqrt(np.mean(own**2))/max(float(np.sqrt(np.mean(audio**2))),1e-9)
        audio=own*.65+audio*scale*.35
        end=min(count,int((source['guide']['active_end_seconds']+.18)*SR))
        audio=audio[:end].copy();k=min(int(.18*SR),len(audio)//5)
        audio[-k:]*=(.5+.5*np.cos(np.linspace(0,np.pi,k)))[:,None]
        edit={'method':'65% newly composed guide + 35% model texture; preserve completed cadence and short release',
              'guide_mix':.65,'model_mix':.35,'active_end_seconds':source['guide']['active_end_seconds']}
    else:
        guide_path=ROOT/source['guide']['path']
        if retimbre:
            voicing_revision=2 if retimbre is True else int(retimbre)
            guide_path,_=battle_guide(t,revision=voicing_revision)
            source['post_guide']={'path':str(guide_path.relative_to(ROOT)),'sha256':g.digest(guide_path),
                                  'reason':('leading-tone pickup resolves into loop tonic' if voicing_revision>=3 else
                                            'clearer pulse duties, stronger march percussion and legato bass across phrase boundary')}
        own,_=sf.read(guide_path,dtype='float32',always_2d=True)
        n=int(source['guide']['period_frames']);k=min(round(.20*SR),len(audio)-n)
        if k<2:raise ValueError('Missing generated post-roll')
        w=(.5-.5*np.cos(np.linspace(0,np.pi,k)))[:,None]
        audio[:k]=audio[n:n+k]*(1-w)+audio[:k]*w
        model=audio[:n];own=own[:n]
        scale=np.sqrt(np.mean(own**2))/max(float(np.sqrt(np.mean(model**2))),1e-9)
        audio=own*.85+model*scale*.15
        edit={'method':'new sixteen-bar four-voice composition with local model texture and circular phase wrap',
              'guide_mix':.85,'model_mix':.15,'bars':16,'guide_bpm':t['bpm'],
              'period_frames':n,'period_seconds':n/SR,'loop_offset_seconds':0.,'model_wrap_seconds':k/SR}
    if not t['loop']:audio[:88]*=np.linspace(0,1,88)[:,None]
    master_path=SOURCE/'masters'/(ident+(f'_v{voicing_revision}' if retimbre else '')+'_float.wav');master_path.parent.mkdir(parents=True,exist_ok=True)
    sf.write(master_path,audio,SR,subtype='FLOAT')
    measurement,_=g.loudness(master_path,SOURCE/'logs'/(ident+'_premaster.log'))
    target=-20 if t['loop'] else -19
    gain=min(target-float(measurement['input_i']),-2.-float(measurement['input_tp']))
    audio*=10**(gain/20);sf.write(master_path,audio,SR,subtype='FLOAT')
    out=SOURCE/'candidates'/(ident+'.ogg');out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        history=SOURCE/'history'/g.digest(out);history.mkdir(parents=True,exist_ok=True)
        shutil.copy2(out,history/out.name)
        if out.with_suffix('.json').exists():shutil.copy2(out.with_suffix('.json'),history/out.with_suffix('.json').name)
    with sf.SoundFile(out,mode='w',samplerate=SR,channels=2,format='OGG',subtype='VORBIS',compression_level=.6) as f:
        for i in range(0,len(audio),8192):f.write(audio[i:i+8192])
    decoded,_=sf.read(out,dtype='float32',always_2d=True);metrics=g.analyze_signal(decoded)
    _,levels=g.loudness(out,SOURCE/'logs'/(ident+'_decoded.log'));metrics.update(levels)
    errors=[]
    if metrics['nonfinite_samples'] or metrics['samples_at_or_above_full_scale']:errors.append('invalid_samples')
    if metrics['true_peak_dbtp']>-1:errors.append('peak_headroom')
    if t['loop'] and metrics['seam_delta_over_derivative_p99']>1.5:errors.append('sample_discontinuity')
    g.dump(out.with_suffix('.json'),{'id':ident,'path':str(out.relative_to(ROOT)),'source_path':str(raw.relative_to(ROOT)),
           'master_path':str(master_path.relative_to(ROOT)),'sha256':g.digest(out),'bytes':out.stat().st_size,
           'source':source,'editing':edit,'gain_db':gain,'target_integrated_lufs':target,'metrics':metrics,'errors':errors})
    print(ident,'mastered',metrics['seconds'],'errors',errors,flush=True)
    if errors:raise ValueError(errors)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--seed',required=True,type=int)
    p.add_argument('--master-only',action='store_true');args=p.parse_args()
    if not args.master_only:worker(args.id,args.seed)
    master(args.id,args.seed)
