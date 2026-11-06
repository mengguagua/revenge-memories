#!/usr/bin/env python3
"""Publish selected local candidates while retaining the preceding assets."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import hashlib

ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT/'actual'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):
    p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(p)

def publish(kind,ids):
    category='sfx' if kind=='sfx' else 'soundtrack'
    report=PROJECT/'reports'/(category+'-20261024')
    source=ROOT/('source/sfx-20261024/audio-guided' if kind=='sfx' else 'source/audio-20261024/content-review')
    config_path=PROJECT/'data'/('sound_effects.json' if kind=='sfx' else 'soundtrack.json')
    config=read(config_path);plan=read(report/'plan.json')
    byid={t['id']:t for t in plan['tracks']}
    changes=[]
    for ident in ids:
        candidate=source/'candidates'/(ident+'.ogg');data=read(candidate.with_suffix('.json'))
        if data.get('review_decision')=='rejected':
            raise ValueError('Rejected audio candidate cannot be published: '+ident)
        if sha(candidate)!=data['sha256']:raise ValueError('Candidate hash mismatch: '+ident)
        if data.get('errors'):raise ValueError(data['errors'])
        record_path=report/'tracks'/(ident+'.json');old=read(record_path)
        destination=ROOT/old['runtime_path']
        if sha(destination)==data['sha256']:continue
        history=source/'before-publication'/sha(destination);history.mkdir(parents=True,exist_ok=True)
        shutil.copy2(destination,history/destination.name);shutil.copy2(record_path,history/record_path.name)
        # Freeze the previous file as a model-input snapshot before replacing it.
        frozen=PROJECT/'reports/audio-content-review-20261024/inputs'/(sha(destination)+destination.suffix)
        frozen.parent.mkdir(parents=True,exist_ok=True)
        if not frozen.exists():shutil.copy2(destination,frozen)
        temp=destination.with_suffix('.ogg.tmp');shutil.copy2(candidate,temp);temp.replace(destination)
        row=copy.deepcopy(old);metrics=data['metrics']
        row.update(revision=3,production_method='audio_review_refinement',status='signal_checks_passed',errors=[],
                   bytes=destination.stat().st_size,sha256=sha(destination),duration_seconds=metrics['seconds'],
                   source=data['source'],metrics=metrics,auditory_review=False,
                   auditory_review_note='New candidate reviewed in isolation; final scene-mix review is recorded separately.')
        row.pop('audio_content_review',None)
        if kind=='sfx':
            origin=data['source'];is_synthesis=origin['method'].startswith('reference-analysed')
            raw=(ROOT/origin['source_path'] if origin.get('source_path') else source/f"{ident}_{origin['seed']}_float.wav")
            row['source_path']=str(raw.relative_to(ROOT))
            row['master_path']=data.get('master_path',origin['source_path'] if is_synthesis else str(candidate.relative_to(ROOT)))
            row['master_path_note']='Synthesis FLOAT WAV' if is_synthesis else 'Final encoded candidate; unclipped model FLOAT source retained separately.'
            row['mastering']=data['mastering'];row['editing']={'method':origin['method'],'reference_audio_used':True}
            row['mastering']['active_rms_delta_from_original_db']=metrics['active_rms_dbfs']-row['source_baseline']['active_rms_dbfs']
            row['mastering']['sample_peak_delta_from_original_db']=metrics['sample_peak_dbfs']-row['source_baseline']['peak_dbfs']
            row['mastering']['runtime_gain_unchanged']=True
            entry=config['effects'][ident]
            entry.update(duration=metrics['seconds'],bytes=row['bytes'],sha256=row['sha256'],metrics=metrics,
                         generation_revision=3,generation_seed=origin.get('seed'),auditory_review=False,
                         production_method=origin['method'],asset_ready=True,signal_checks_passed=True)
            # Duration is the verified native envelope, including its original
            # finite stop behavior. It never introduces an infinite SFX loop.
            entry['max_duration']=max(float(entry.get('max_duration',0)),metrics['seconds']+.02)
            byid[ident]['runtime_asset_revision']=3
            byid[ident]['max_duration_seconds']=max(float(byid[ident].get('max_duration_seconds',0)),metrics['seconds']+.02)
            byid[ident]['selected_duration_basis']='native audible envelope and verified request window; finite stop behavior retained'
        else:
            row.update(source_path=data['source_path'],master_path=data['master_path'],editing=data['editing'])
            row['target_integrated_lufs']=data.get('target_integrated_lufs',row.get('target_integrated_lufs'))
            entry=config['tracks'][ident]
            entry.update(duration=metrics['seconds'],bytes=row['bytes'],sha256=row['sha256'],
                         integrated_lufs=metrics['integrated_lufs'],true_peak_dbtp=metrics['true_peak_dbtp'],
                         source_seed=data['source']['seed'],auditory_review=False,
                         production_method=data['source']['method'],asset_ready=True,signal_checks_passed=True)
        entry.pop('audio_content_review',None)
        entry['auditory_review_note']='Waveform changed; final model and scene review pending.'
        dump(record_path,row)
        byid[ident]['selected_production_method']=row['source']['method']
        changes.append({'id':ident,'before_sha256':old['sha256'],'after_sha256':row['sha256'],
                        'before_path':str((history/destination.name).relative_to(ROOT)),
                        'candidate_path':str(candidate.relative_to(ROOT))})
    config['production_revision']=3
    if changes:config['model_audio_review_completed']=False
    dump(config_path,config);dump(report/'plan.json',plan)
    all_records=[read(report/'tracks'/(t['id']+'.json')) for t in plan['tracks']]
    previous=read(report/'generation-report.json');previous.update(tracks=all_records,production_revision=3)
    if changes:previous['auditory_review']=False
    dump(report/'generation-report.json',previous)
    log=source/'publication-changes.json'
    prior=read(log) if log.exists() else []
    dump(log,prior+changes)
    print('Published',kind,len(changes),[c['id'] for c in changes],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sfx',nargs='*');p.add_argument('--music',nargs='*');args=p.parse_args()
    if args.sfx:publish('sfx',args.sfx)
    if args.music:publish('music',args.music)
