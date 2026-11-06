#!/usr/bin/env python3
"""Reference-conditioned local SA3 SFX candidates; never writes runtime assets.

This explicitly uses the supplied reference recording as model input, unlike
the first text-only batch. Generated variants must retain that provenance.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source/sfx-20261024/audio-guided'
MODEL=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx')
SR=44100
for name in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[name]='1'

def main():
    import numpy as np
    import soundfile as sf
    from generate_original_sfx import tracks,digest,dump
    parser=argparse.ArgumentParser();parser.add_argument('--id',required=True)
    parser.add_argument('--seed',required=True,type=int);parser.add_argument('--noise',type=float,default=.55)
    parser.add_argument('--cfg',type=float,default=2.)
    parser.add_argument('--fp32',action='store_true')
    args=parser.parse_args()
    t=next(t for t in tracks() if t['id']==args.id)
    old=ROOT/'actual'/t['old_paths'][0].removeprefix('res://')
    a,sr=sf.read(old,dtype='float32',always_2d=True)
    if sr!=SR:raise ValueError('Unexpected reference sample rate')
    out=SOURCE/f'{args.id}_{args.seed}_float.wav';out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    reference=SOURCE/'reference-pcm'/f'{args.id}.wav';reference.parent.mkdir(parents=True,exist_ok=True)
    reference_gain=min(8.,.7/max(float(np.abs(a).max()),1e-9))
    if not reference.exists():sf.write(reference,a*reference_gain,SR,subtype='PCM_16')
    seconds=min(10.,max(1.,len(a)/SR+.2))
    prompt=('TrackType: SFX. A dry monophonic retro 8-bit game sound effect. '
            'Preserve the reference sound\'s electronic pitch contour, immediate attack, '
            'modulation speed and noise-pulse rhythm. A clearly defined pulse-wave or '
            'noise-channel effect, crisp upper-midrange, no muffled low drum or acoustic instrument. '
            'Create a variation in synthetic tone color, retaining the same sound gesture. '
            'No music, no vocal, no real-world ambience, no reverb. ')
    if t.get('manual_stop'):
        prompt+='Continuous electronic modulation until stopped, stable presence from the opening, no musical beat.'
    else:prompt+='One compact event with immediate attack and short release, no additional impacts or repeated sequence.'
    sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
    captured={}
    def save_float(path,audio,sample_rate=SR):
        if not np.isfinite(audio).all():raise ValueError('Nonfinite output')
        captured.update(raw_peak=float(np.abs(audio).max()),raw_rms=float(np.sqrt(np.mean(audio**2))))
        sf.write(path,audio.T,sample_rate,subtype='FLOAT')
    sa3_mlx.save_wav=save_float
    sys.argv=['sa3_mlx.py','--dit','sm-sfx','--decoder','same-s','--seconds',str(seconds),
              '--steps','8','--cfg',str(args.cfg),'--seed',str(args.seed),'--prompt',prompt,
              '--negative-prompt','music, voice, speech, acoustic drum, bass drum, real-world ambience, reverb, muffled impact',
              '--init-audio',str(reference),'--init-noise-level',str(args.noise),'--out',str(out)]
    if args.fp32:sys.argv+=['--dit-dtype','fp32']
    start=time.monotonic();sa3_mlx.main()
    dump(out.with_suffix('.json'),{'id':args.id,'seed':args.seed,'model':'local Stable Audio 3 sm-sfx/same-s',
         'method':'reference-conditioned audio-to-audio variation','reference_path':str(old.relative_to(ROOT)),
         'reference_sha256':digest(old),'reference_pcm_sha256':digest(reference),'init_noise_level':args.noise,
         'reference_input_gain_db':float(20*np.log10(reference_gain)),
         'prompt':prompt,'cfg':args.cfg,'steps':8,'sha256':digest(out),'seconds':seconds,'offline':True,
         'dit_dtype':'fp32' if args.fp32 else 'fp16',
         'generation_wall_seconds':round(time.monotonic()-start,3),**captured})
if __name__=='__main__':main()


def master_candidates():
    """Master outside the game, keeping reference event duration and envelope."""
    import numpy as np
    import soundfile as sf
    import generate_original_sfx as g
    plans={t['id']:t for t in g.tracks()}
    outdir=SOURCE/'candidates';outdir.mkdir(parents=True,exist_ok=True)
    records=[]
    for raw in sorted(SOURCE.glob('*_float.wav')):
        source=json.loads(raw.with_suffix('.json').read_text());t=plans[source['id']]
        old=ROOT/'actual'/t['old_paths'][0].removeprefix('res://')
        original,_=sf.read(old,dtype='float32',always_2d=True)
        a,sr=sf.read(raw,dtype='float32',always_2d=True)
        # The audio-to-audio source already carries the native event gesture.
        # Retain that duration instead of searching for a new transient and
        # accidentally cutting the body or selecting an unrelated later event.
        a=a[:len(original)].copy()
        # Keep the source event's amplitude gesture. This prevents a generated
        # tail, swell or extra pulse from implying an additional hit. New PCM
        # and timbre still come from the audio-conditioned model output.
        ref_env,dt=g.envelope(original);new_env,_=g.envelope(a)
        count=min(len(ref_env),len(new_env))
        smooth=np.ones(5)/5
        reference_shape=np.convolve(ref_env[:count],smooth,mode='same')
        candidate_shape=np.convolve(new_env[:count],smooth,mode='same')
        threshold=max(float(reference_shape.max())*.015,1e-6)
        ratio=np.clip(reference_shape/np.maximum(candidate_shape,1e-6),0,8.)
        ratio[reference_shape<threshold]=0
        axis=np.arange(len(a))/SR
        a*=np.interp(axis,(np.arange(count)+.5)*dt,ratio,left=ratio[0],right=0.)[:,None]
        fade_in=min(44,len(a)//20);fade_out=min(882,len(a)//15)
        a[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
        a[-fade_out:]*=(.5+.5*np.cos(np.linspace(0,np.pi,fade_out)))[:,None]
        env,_=g.envelope(a);active=env[env>max(float(env.max())*.03,10**(-55/20))]
        rms=g.db(np.sqrt(np.mean(active**2)));peak=g.db(np.abs(a).max())
        target,ceiling=g.limits(t)
        shaping={'applied':False}
        if (target-rms)-(ceiling-peak)>2.:
            # The original chip channels have a much denser body than sparse
            # generated spikes. A smooth local knee controls those spikes
            # before gain, rather than making the whole useful sound too quiet.
            local=np.convolve(env,np.ones(5)/5,mode='same')
            local=np.interp(np.arange(len(a))/SR,(np.arange(len(local))+.5)*dt,
                            local,left=local[0],right=local[-1])
            knee=np.maximum(local*2.3,float(local.max())*.02)[:,None]
            a=knee*np.tanh(a/knee)
            env,_=g.envelope(a);active=env[env>max(float(env.max())*.03,10**(-55/20))]
            rms=g.db(np.sqrt(np.mean(active**2)));peak=g.db(np.abs(a).max())
            shaping={'applied':True,'method':'smooth tanh knee at 2.3 times 25ms local RMS',
                     'reason':'generated peak crest would otherwise hide the audible body under the reference peak budget'}
        gain=min(target-rms,ceiling-peak)
        a*=10**(gain/20)
        if t['request']=='53':
            # This wash is heard for only three ticks in arrow-rain. Preserve
            # the reference's actual front level, independently of its 4s body.
            old_front=np.sqrt(np.mean(original[:2205].astype(np.float64)**2))
            new_front=np.sqrt(np.mean(a[:2205].astype(np.float64)**2))
            ratio=min(1.,old_front/max(new_front,1e-12))
            time_axis=np.arange(len(a))/SR
            rise=.5-.5*np.cos(np.pi*np.clip((time_axis-.06)/.24,0,1))
            a*=(ratio+(1-ratio)*rise)[:,None]
        path=outdir/(t['id']+'.ogg')
        with sf.SoundFile(path,mode='w',samplerate=SR,channels=2,format='OGG',subtype='VORBIS',compression_level=.6) as f:
            for i in range(0,len(a),8192):f.write(a[i:i+8192])
        decoded,_=sf.read(path,dtype='float32',always_2d=True)
        metrics=g.measure(path,decoded,SOURCE/'logs'/(t['id']+'_candidate_decoded.log'))
        record={'id':t['id'],'request':t['request'],'path':str(path.relative_to(ROOT)),
                'sha256':g.digest(path),'bytes':path.stat().st_size,'source':source,
                'mastering':{'method':'preserve reference duration and 25ms-smoothed amplitude gesture; rounded edges; constant active-RMS gain',
                              'gain_db':gain,'target_active_rms_dbfs':target,'peak_ceiling_dbfs':ceiling,
                              'transient_shaping':shaping},'metrics':metrics}
        g.dump(path.with_suffix('.json'),record);records.append(record)
    all_records=[json.loads(p.read_text()) for p in sorted(outdir.glob('rm_sfx_*.json'))]
    g.dump(SOURCE/'candidate-manifest.json',{'tracks':all_records,'count':len(all_records)})
    print('Mastered model candidates',len(records),'total with UI synthesis',len(all_records),flush=True)


def render_candidate_scenes():
    """Exact request traces, with a music bed only for genuinely reachable cues."""
    import numpy as np
    import audit_audio_scenes as scene
    import generate_original_sfx as g
    project=ROOT/'actual'
    source=scene.read(project/'data/legacy/full_audio.json')
    records=scene.read(project/'reports/sfx-20261024/generation-report.json')['tracks']
    plans={t['id']:t for t in g.tracks()}
    data={r['request']:scene.load(SOURCE/'candidates'/(r['id']+'.ogg')) for r in records}
    variants=scene.read(project/'data/legacy/full_animation_effects.json')['variants']
    representative={}
    for name,v in variants.items():
        events,end=scene.source_schedule(v)
        for _,_,number,_ in events:
            request=f'{number:02X}'
            if request in data:representative.setdefault(request,(name,events,end))
    outdir=SOURCE/'scene-candidates';outdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    music={name:scene.load(project/'assets/music/20261024'/f'{name}.ogg')
           for name in ['rm_battle_snow','rm_hub_hearth']}
    for r in records:
        req=r['request'];ident=r['id'];path=outdir/(ident+'.mp3')
        if req in representative:
            name,events,end=representative[req]
            a,stats=scene.render_sfx(events,data,source['control_requests'],end+.35)
            a+=scene.bed(music['rm_battle_snow'],len(a),start=3)
            context='native animation trace '+name+' + battle BGM (0.50), SFX (0.65)'
        elif req in ['10','12','13','25']:
            step=.10 if req=='12' else .50
            events=[(.2+i*step,0,int(req,16),'UI repetition') for i in range(6)]
            a,stats=scene.render_sfx(events,data,source['control_requests'],2.)
            a+=scene.bed(music['rm_hub_hearth'],len(a),start=3)
            context='UI repetition + hub BGM (0.50), SFX (0.65)'
        else:
            a=data[req]*scene.SFX_GAIN
            context='compatibility only: no current trigger, no invented scene'
            stats={}
        scene.preview(path,a)
        rows.append({'id':ident,'request':req,'path':str(path.relative_to(ROOT)),
                     'sha256':scene.sha(path),'context':context,
                     'all_sfx_set':'audio-guided candidates','actual_game_gains':True,
                     'peak_dbfs':scene.db(np.abs(a).max()),'timing':stats})
    g.dump(SOURCE/'scene-candidate-manifest.json',{'tracks':rows})
    print('Rendered candidate contexts',len(rows),flush=True)
