#!/usr/bin/env python3
"""Offline waveform-conditioned Qwen2-Audio review, with resumable hash receipts.

Run with StableAudio3SmallSFX/audio-reviewer/.venv/bin/python (Metal required).
No loudspeaker playback, device, save, network inference or game window access.
Model judgments are evidence for an editor, never human-listening certificates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import types

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'actual'
REPORT = PROJECT / 'reports/audio-content-review-20261024'
MODEL = Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/audio-reviewer/Qwen2-Audio-7B-Instruct-4bit')
MODEL_REV = 'c65570002626f41b4dc08b7b54f42f99f3e82e7f'
ADAPTER_REV = 1
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

def read(p): return json.loads(Path(p).read_text())
def dump(p, x):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix(p.suffix + '.tmp')
    temp.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temp.replace(p)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resource(p): return PROJECT / p.removeprefix('res://')

def waveform(path, start=0, end=None, repeat_short=False):
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    a, sr = sf.read(path, dtype='float32', always_2d=True)
    a = a[int(start*sr):int(end*sr) if end is not None else None].mean(axis=1)
    if sr != 16000:
        gcd = math.gcd(sr, 16000)
        a = resample_poly(a, 16000//gcd, sr//gcd).astype(np.float32)
    if repeat_short and len(a) < 8000:
        # Explicitly disclosed to the model; no time stretching or normalization.
        gap = np.zeros(2400, np.float32)
        a = np.concatenate([np.concatenate([a, gap]) for _ in range(4)])
    if not 0 < len(a) <= 480000: raise ValueError(f'Outside model window: {path}: {len(a)}')
    return a

def load_reviewer():
    import mlx.core as mx
    import mlx.nn as nn
    import numpy as np
    from mlx_audio.stt.utils import load_model
    from transformers import WhisperFeatureExtractor
    model = load_model(MODEL, strict=True)
    extractor = WhisperFeatureExtractor.from_pretrained(MODEL, local_files_only=True)

    def embeddings(self, audio, prompt=None, verbose=False):
        audio_list = self._load_audio(audio)
        projected = []; lengths = []
        for wave in audio_list:
            # Official Slaney log-mel, 3000 frames, and real unpadded length.
            f = extractor(np.array(wave), sampling_rate=16000,
                          return_attention_mask=True, return_tensors='np')
            n_mel = int(f['attention_mask'][0].sum())
            conv_length = (n_mel-1)//2+1
            output_length = (conv_length-2)//2+1
            if output_length < 1: raise ValueError('Audio too short for the encoder')
            enc = self.audio_tower
            x = mx.array(f['input_features'], dtype=enc.conv1.weight.dtype).transpose(0,2,1)
            x = nn.gelu(enc.conv1(x)); x = nn.gelu(enc.conv2(x))
            # In the reference model padded keys are masked. Dropping those
            # positions after convolution is equivalent for valid query outputs.
            x = x[:, :conv_length] + enc.embed_positions[:conv_length]
            for layer in enc.layers: x = layer(x)
            n = x.shape[1]//2
            x = x[:, :n*2].reshape(1,n,2,x.shape[-1]).mean(axis=2)
            x = enc.layer_norm(x)
            # Do not cast features to QuantizedEmbedding.weight's uint32 dtype.
            x = self.multi_modal_projector(x)[:, :output_length]
            projected.append(x); lengths.append(output_length)
        ids = self._build_prompt(lengths, prompt)
        is_audio = ids == self.audio_token_id
        text = self.language_model.model.embed_tokens(mx.where(is_audio, 0, ids)[None])
        features = mx.concatenate(projected, axis=1).astype(text.dtype)
        indices = mx.clip(mx.cumsum(is_audio.astype(mx.int32))-1, 0, features.shape[1]-1)
        embedded = mx.where(is_audio[None,:,None], features[:,indices,:], text)
        mx.eval(embedded)
        return ids, embedded, len(ids)

    model.get_input_embeddings = types.MethodType(embeddings, model)
    return model

BLIND = ('Describe only the audible sound in this audio. State sound type, timbre, '
         'pitch movement, rhythm and whether speech or music is audible. '
         'Do not infer a story or visual source. Be specific and concise, under 60 words. '
         'If silent say silent. Very short one-shot clips may be repeated four times with silence for analysis.')
PAIR = ('Compare the two audio inputs as game sound effects. Audio 1 is the reference; '
        'Audio 2 is the replacement. Describe each actual sound, then the most obvious '
        'difference in timbre, attack, pitch movement, density and decay. Do not assume '
        'the replacement is good. Avoid invented visual events. Under 100 words. '
        'Very short one-shots may be repeated four times with silent gaps for analysis.')
MUSIC = ('Describe this instrumental game-music passage using only what is audible: '
         'dominant instruments/timbres, pulse, energy and mood; any voice, noise or '
         'abrupt musical change. Is it sparse retro synthesized music or acoustic/full-band music? '
         'Do not guess a game, story, composer or title. Under 75 words.')
SEAM = ('This clip crosses the repeat boundary of a looping game soundtrack at its midpoint. '
        'Describe the audible music and whether rhythm, harmony, instruments or loudness '
        'change abruptly at the middle. Report uncertainty. Under 60 words.')

def task_key(t):
    raw = json.dumps({**t, 'adapter':ADAPTER_REV, 'model':MODEL_REV}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]

def tasks():
    import soundfile as sf
    music = read(PROJECT/'reports/soundtrack-20261024/generation-report.json')['tracks']
    sfx = read(PROJECT/'reports/sfx-20261024/generation-report.json')['tracks']
    plans = {t['id']:t for t in read(PROJECT/'reports/sfx-20261024/plan.json')['tracks']}
    out = []
    for t in sfx:
        new = ROOT/t['runtime_path']; old = resource(plans[t['id']]['old_paths'][0])
        out.append({'id':t['id'], 'kind':'sfx_pair', 'paths':[str(old),str(new)],
                    'hashes':[sha(old),sha(new)], 'prompt':PAIR, 'max_tokens':165,
                    'repeat_short':True})
    for t in music:
        p = ROOT/t['runtime_path']; duration = sf.info(p).duration
        start = 0.; segment = 0
        while start < duration-.005:
            end = min(duration,start+28.)
            out.append({'id':t['id'], 'kind':'music_full_coverage', 'segment':segment,
                        'paths':[str(p)], 'hashes':[sha(p)], 'start':round(start,5),
                        'end':round(end,5), 'prompt':MUSIC, 'max_tokens':120})
            if end>=duration-.005:break
            start=end-1.;segment+=1
        if t['loop']:
            out.append({'id':t['id'], 'kind':'loop_boundary', 'paths':[str(p)],
                        'hashes':[sha(p)], 'boundary_seconds':6., 'prompt':SEAM,'max_tokens':100})
    for request,t in read(PROJECT/'data/legacy/full_audio.json')['music_by_request'].items():
        p=resource(t['path'])
        out.append({'id':'original_music_'+request, 'kind':'original_music_reference',
                    'paths':[str(p)], 'hashes':[sha(p)],'start':0.,'end':min(25.,sf.info(p).duration),
                    'prompt':MUSIC,'max_tokens':100})
    scene_review=read(PROJECT/'reports/audio-scene-review-20261024/review.json')
    scene_rows=scene_review['resources']
    for t in scene_rows:
        suffix='_scene.mp3' if t['type']=='music' else '_new_context.mp3'
        p=PROJECT/'reports/audio-scene-review-20261024/audition'/(t['id']+suffix)
        if not p.exists():continue
        duration=sf.info(p).duration
        prompt=('This is an offline mix using game playback gains and event timing. '
                'Describe the sounds actually audible and any masking, harshness, excessively long tail '
                'or distracting effect. Intended scene: '+t.get('scene','')+'. '
                'Do not infer unheard elements from this description. Under 70 words.')
        out.append({'id':t['id'],'kind':'scene_mix','paths':[str(p)],'hashes':[sha(p)],
                    'start':0.,'end':min(28.,duration),'prompt':prompt,'max_tokens':110})
    return out

def run(ts, limit=None):
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    model = None; done=[]
    for t in ts[:limit] if limit else ts:
        key=task_key(t); output=REPORT/'receipts'/f'{t["id"]}_{t["kind"]}_{key}.json'
        if output.exists():
            done.append(read(output));continue
        if model is None:
            start=time.monotonic();model=load_reviewer()
            print(f'Loaded reviewer in {time.monotonic()-start:.1f}s',flush=True)
        audios=[]
        for p in t['paths']:
            if 'boundary_seconds' in t:
                seconds=t['boundary_seconds']; duration=sf.info(p).duration
                a=np.concatenate([waveform(p,max(0.,duration-seconds)),waveform(p,0,min(seconds,duration))])
            else:a=waveform(p,t.get('start',0),t.get('end'),t.get('repeat_short',False))
            audios.append(a)
        start=time.monotonic()
        result=model.generate(audios, prompt=t['prompt'], max_tokens=t['max_tokens'], temperature=0.)
        receipt={**t,'key':key,'model':str(MODEL),'model_revision':MODEL_REV,
                 'adapter_revision':ADAPTER_REV,'audio_input_samples':[len(a) for a in audios],
                 'audio_input_sample_rate':16000,'response':result.text,
                 'generation_tokens':result.generation_tokens,'generation_tps':result.generation_tps,
                 'wall_seconds':round(time.monotonic()-start,3),
                 'peak_memory_bytes':mx.get_peak_memory(),'review_type':'local_audio_model',
                 'human_listening':False}
        dump(output,receipt);done.append(receipt)
        print(json.dumps({'id':t['id'],'kind':t['kind'],'segment':t.get('segment'),
                          'seconds':receipt['wall_seconds'],'response':result.text},ensure_ascii=False),flush=True)
        mx.clear_cache()
    return done

def calibration():
    import numpy as np
    import soundfile as sf
    d=REPORT/'calibration';d.mkdir(parents=True,exist_ok=True)
    sr=16000;time_axis=np.arange(sr*2)/sr
    for name,a in [('silence',np.zeros(sr*2)),('sine_440',.12*np.sin(2*np.pi*440*time_axis)),
                   ('noise',np.random.default_rng(69).normal(0,.045,sr*2))]:
        p=d/(name+'.wav')
        if not p.exists():sf.write(p,a,sr,subtype='FLOAT')
    names=['silence','sine_440','noise']
    ts=[{'id':'calibration_'+n,'kind':'calibration','paths':[str(d/(n+'.wav'))],
         'hashes':[sha(d/(n+'.wav'))],'prompt':BLIND,'max_tokens':95} for n in names]
    ts += [t for t in tasks() if t['id'] in ['rm_sfx_12','rm_sfx_03','rm_title'] and t['kind']!='loop_boundary'][:3]
    dump(REPORT/'calibration.json',run(ts))

def main():
    a=argparse.ArgumentParser();a.add_argument('--calibrate',action='store_true')
    a.add_argument('--kind',nargs='+');a.add_argument('--ids',nargs='+');a.add_argument('--limit',type=int)
    args=a.parse_args();REPORT.mkdir(parents=True,exist_ok=True)
    if args.calibrate:calibration();return
    ts=tasks()
    if args.kind:ts=[t for t in ts if t['kind'] in args.kind]
    if args.ids:ts=[t for t in ts if t['id'] in args.ids]
    dump(REPORT/'task-plan.json',ts)
    rows=run(ts,args.limit)
    dump(REPORT/'latest-run.json',{'tasks':len(rows),'receipts':rows})
if __name__=='__main__':main()
