#!/usr/bin/env python3
"""Qwen3-Omni audio-input review through a loopback-only local llama.cpp server."""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import shutil
from pathlib import Path
import time
import urllib.request
from review_audio_content import ROOT,PROJECT,REPORT,read,dump,sha,waveform,resource

MODEL_ID='ggml-org/Qwen3-Omni-30B-A3B-Instruct-GGUF'
MODEL_REV='6e35a28f4a19b18730f8949b0c579c6429649ab8'
ENDPOINT='http://127.0.0.1:18769/v1/chat/completions'
PROMPT_REV=1

def part(audio):
    import soundfile as sf
    buf=io.BytesIO();sf.write(buf,audio,16000,format='WAV',subtype='PCM_16')
    return {'type':'input_audio','input_audio':{'data':base64.b64encode(buf.getvalue()).decode(),'format':'wav'}}

def load_slice(spec):
    import numpy as np
    import soundfile as sf
    p=Path(spec['path']);duration=sf.info(p).duration
    # The newer model supports long input. The helper intentionally caps each
    # decode call at 30 seconds, so concatenate all unchanged chunks here.
    if spec.get('seam'):
        seconds=min(6.,duration)
        return np.concatenate([waveform(p,duration-seconds),waveform(p,0,seconds)])
    end=min(spec.get('end',duration),duration);start=spec.get('start',0.)
    chunks=[]
    while start<end-.00001:
        stop=min(start+28.,end);chunks.append(waveform(p,start,stop,spec.get('repeat_short',False)))
        start=stop
    return np.concatenate(chunks)

def plans():
    old=read(PROJECT/'data/legacy/full_audio.json')
    route=read(PROJECT/'data/soundtrack.json')['routing']['legacy_music_requests']
    music=read(PROJECT/'reports/soundtrack-20261024/generation-report.json')['tracks']
    sfx=read(PROJECT/'reports/sfx-20261024/generation-report.json')['tracks']
    sp={t['id']:t for t in read(PROJECT/'reports/sfx-20261024/plan.json')['tracks']}
    mp={t['id']:t for t in read(PROJECT/'reports/soundtrack-20261024/plan.json')['tracks']}
    ts=[]
    for t in sfx:
        p=sp[t['id']];scene=PROJECT/'reports/audio-scene-review-20261024/audition'/(t['id']+'_new_context.mp3')
        if scene.with_suffix('.wav').exists():scene=scene.with_suffix('.wav')
        audios=[{'path':str(resource(p['old_paths'][0])),'repeat_short':True},
                {'path':str(ROOT/t['runtime_path']),'repeat_short':True}, {'path':str(scene),'end':28.}]
        prompt=('Listen to all three audio inputs. Audio 1 is a reference game sound effect. '
                'Audio 2 is the replacement, with the actual playback level retained. Very short '
                'one-shots in inputs 1 and 2 are repeated four times with gaps for analysis. '
                'Audio 3 is a game-gain offline scene mix using audio 2 and the current event timing. '
                'First describe the audible timbre and gesture of 1 and 2 separately. Then assess '
                'whether 2 loses an important attack, pitch sweep, electronic modulation or clarity, '
                'contains unwanted music/speech, or becomes dull/boomy/harsh. Finally describe '
                'audibility/masking and tail timing in 3. Be critical and grounded in the audio. '
                'Do not invent mechanics, identify a specific game, or give generic praise. '
                'Report uncertainty. Under 180 words. Function for editorial context: '+p['role'])
        ts.append({'id':t['id'],'kind':'sfx_full_and_scene','audios':audios,'prompt':prompt,'max_tokens':320})
    for t in music:
        reference=next((req for req,ident in route.items() if ident==t['id']),
                       '76' if t['id'].startswith('rm_battle') else '93')
        audios=[{'path':str(ROOT/t['runtime_path'])},
                {'path':str(resource(old['music_by_request'][reference]['path'])),'end':15.}]
        if t['loop']:audios.append({'path':str(ROOT/t['runtime_path']),'seam':True})
        scene=PROJECT/'reports/audio-scene-review-20261024/audition'/(t['id']+'_scene.mp3')
        if scene.with_suffix('.wav').exists():scene=scene.with_suffix('.wav')
        audios.append({'path':str(scene),'end':28.})
        prompt=('Listen to every audio input. Audio 1 is the ENTIRE new game soundtrack cue; '
                'describe its actual timbres, energy, mood, melodic development and any unwanted '
                'speech, vocals, defects or sections inappropriate for the scene. Audio 2 is a '
                'short reference for the original game\'s clear, sparse retro texture; do not '
                'require copying its melody. ')
        prompt+=('Audio 3 is tail 6 seconds then head 6 seconds, with the loop join at 6 seconds; '
                 'assess rhythmic/harmonic continuity and distracting loudness changes there. '
                 'Audio 4 is the current game-gain offline mix with interface or combat effects. '
                 if t['loop'] else 'Audio 3 is the current game-gain offline mix, including the background pause and resume. ')
        prompt+=('Discuss whether effects mask music or music masks essential feedback. '
                 'Report uncertainty, avoid invented precise keys/BPM/timestamps and generic praise. '
                 'Under 190 words. Intended scene: '+mp[t['id']]['scene']+'; desired mood: '+mp[t['id']]['mood'])
        ts.append({'id':t['id'],'kind':'music_entire_loop_and_scene','audios':audios,'prompt':prompt,'max_tokens':340})
    return ts

def run(ts):
    results=[]
    for t in ts:
        hashes=[sha(a['path']) for a in t['audios']]
        archived=[]
        for spec,digest in zip(t['audios'],hashes):
            p=Path(spec['path']);snapshot=REPORT/'inputs'/(digest+p.suffix)
            snapshot.parent.mkdir(parents=True,exist_ok=True)
            if not snapshot.exists():shutil.copy2(p,snapshot)
            archived.append(str(snapshot.relative_to(ROOT)))
        key=hashlib.sha256(json.dumps({'task':t,'hashes':hashes,'model':MODEL_REV,'prompt_revision':PROMPT_REV},sort_keys=True).encode()).hexdigest()[:24]
        output=REPORT/'omni-receipts'/f'{t["id"]}_{key}.json'
        if output.exists():results.append(read(output));continue
        # Decode the frozen copies, so concurrent report refreshes cannot
        # change the waveform between hashing and model input preparation.
        waves=[load_slice({**a,'path':str(ROOT/frozen)})
               for a,frozen in zip(t['audios'],archived)]
        content=[]
        for i,w in enumerate(waves,1):content.extend([{'type':'text','text':f'Audio {i}:'},part(w)])
        content.append({'type':'text','text':t['prompt']})
        body={'messages':[{'role':'system','content':'You are a careful audio analyst. Describe only audible evidence; admit uncertainty.'},
                          {'role':'user','content':content}], 'max_tokens':t['max_tokens'], 'temperature':0.,'stream':False}
        request=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        start=time.monotonic()
        with urllib.request.urlopen(request,timeout=600) as response:result=json.load(response)
        message=result['choices'][0]['message'];text=message.get('content','')
        receipt={**t,'key':key,'source_sha256':hashes,'model':MODEL_ID,'model_revision':MODEL_REV,
                 'archived_input_paths':archived,
                 'audio_input_samples':[len(w) for w in waves],'input_sample_rate':16000,
                 'input_pcm_sha256':[hashlib.sha256(w.tobytes()).hexdigest() for w in waves],
                 'response':text,'reasoning':message.get('reasoning_content'),
                 'usage':result.get('usage'),'timings':result.get('timings'),
                 'finish_reason':result['choices'][0].get('finish_reason'),
                 'wall_seconds':round(time.monotonic()-start,3),'human_listening':False,
                 'review_type':'local_waveform_conditioned_model'}
        if not text.strip():raise RuntimeError(f'Empty audio response: {t["id"]}: {message}')
        dump(output,receipt);results.append(receipt)
        print(json.dumps({'id':t['id'],'seconds':receipt['wall_seconds'],'response':text},ensure_ascii=False),flush=True)
    dump(REPORT/'omni-latest-run.json',results)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ids',nargs='+');parser.add_argument('--calibrate',action='store_true')
    parser.add_argument('--candidates',action='store_true');parser.add_argument('--music-only',action='store_true')
    parser.add_argument('--blind',action='store_true')
    parser.add_argument('--final-scenes',action='store_true')
    args=parser.parse_args()
    if args.calibrate:
        import numpy as np
        import soundfile as sf
        long_path=REPORT/'calibration/long_tail.wav'
        if not long_path.exists():
            a=np.zeros(16000*36,np.float32)
            a[:32000]=np.random.default_rng(70).normal(0,.045,32000)
            a[-32000:]=.12*np.sin(2*np.pi*440*np.arange(32000)/16000)
            sf.write(long_path,a,16000,subtype='FLOAT')
        ts=[{'id':'omni_control_'+name,'kind':'control','audios':[{'path':str(REPORT/'calibration'/(name+'.wav'))}],
             'prompt':'Describe only the sound actually audible. If silent, say silent. Under 50 words.','max_tokens':100}
            for name in ['silence','sine_440','noise','long_tail']]
        run(ts);return
    ts=plans()
    if args.final_scenes:
        fixtures=read(PROJECT/'reports/audio-scene-review-20261024/review.json')
        ts=[]
        for row in fixtures['resources']:
            context=row.get('scene_context',row.get('scene',''))
            prompt=('This is a final offline scene mix using the actual game gains and native event sequence. '
                    'Describe only audible evidence. Check whether essential feedback attacks are clear, '
                    'any intrusive click/distortion or excessive rumbling tail, and whether music continuity '
                    'is distracted by the effects. Effects need not be as loud as music; a naturally masked '
                    'quiet tail is not a failure. Report uncertainty and avoid inventing instruments/events. '
                    'Under 90 words. Fixture context: '+context)
            if row['id']=='rm_sfx_53':prompt+=' The arrow-rain prelude is deliberately quiet and lasts only three native ticks (about 50ms) before contact replaces it; do not expect the full four-second isolated texture.'
            ts.append({'id':row['id'],'kind':'final_scene_mix','audios':[{'path':str(ROOT/row['scene_fixture_path'])}],
                       'asset_sha256':fixtures['asset_sha256_by_id'][row['id']],
                       'fixture_sha256':row['scene_fixture_sha256'],'prompt':prompt,'max_tokens':170})
    if args.music_only:ts=[t for t in ts if t['kind'].startswith('music')]
    if args.candidates:
        selected=[]
        for t in ts:
            if not t['kind'].startswith('sfx'):continue
            candidate=ROOT/'source/sfx-20261024/audio-guided/candidates'/(t['id']+'.ogg')
            if not candidate.exists():continue
            mix=ROOT/'source/sfx-20261024/audio-guided/scene-candidates'/(t['id']+'.mp3')
            t['audios']=t['audios'][:2]+[{'path':str(candidate),'repeat_short':True}]
            if mix.exists():t['audios'].append({'path':str(mix),'end':28.})
            t['kind']='sfx_candidate_and_scene'
            t['prompt']=('Compare the actual audio inputs. Audio 1 is the reference sound effect; '
                         'Audio 2 is the current replacement; Audio 3 is a newly remade candidate. '
                         'Short one-shots may be repeated four times with gaps for analysis. '
                         'Audio 4, if supplied, is the candidate in a game-gain offline scene mix. '
                         'Describe the actual timbre, attack, pitch/modulation gesture and decay '
                         'of 1, 2 and 3. Which replacement better preserves clear, distinctive '
                         'retro electronic feedback without dull thuds, unwanted music/voice or '
                         'unrelated sounds? Assess candidate clarity/masking/tail in audio 4. '
                         'Give a final preference: 2, 3, neither, or uncertain, with a concrete '
                         'audible reason. Do not invent visuals or mechanics. Under 180 words. '
                         'Function context: '+next(p['role'] for p in read(PROJECT/'reports/sfx-20261024/plan.json')['tracks'] if p['id']==t['id']))
            t['max_tokens']=320;selected.append(t)
            if args.blind:
                candidate_input=3
                if int(t['id'].split('_')[-1],16)%2:
                    t['audios'][1],t['audios'][2]=t['audios'][2],t['audios'][1]
                    candidate_input=2
                t['candidate_input']=candidate_input
                t['prompt']=('Audio 1 is a reference sound effect. Audio 2 and Audio 3 are anonymous '
                             'replacement sounds in randomized order. Short one-shots may be repeated '
                             'four times with gaps for analysis. Audio 4, if present, is one replacement '
                             'in the actual game-gain offline scene mix; assess that mix separately, '
                             'never compare it as an isolated replacement. Describe audible timbre, '
                             'attack, pitch/modulation gesture and decay of 1, 2 and 3. Which replacement '
                             'better preserves distinctive clear retro electronic feedback? Identify '
                             'any dull thud, unwanted music/voice or unrelated sound. If 2 and 3 sound '
                             'the same, say so. For 4, check whether the essential attack is audible; '
                             'a tail under music alone is not a failure. Give final isolated preference '
                             '2, 3, neither or uncertain, with concrete audible evidence. Do not infer '
                             'quality from ordering. Under 180 words. Function context: '+next(p['role'] for p in read(PROJECT/'reports/sfx-20261024/plan.json')['tracks'] if p['id']==t['id']))
        ts=selected
    if args.ids:ts=[t for t in ts if t['id'] in args.ids]
    dump(REPORT/'omni-task-plan.json',ts);run(ts)
if __name__=='__main__':main()
