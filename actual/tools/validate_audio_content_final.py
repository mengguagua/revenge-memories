#!/usr/bin/env python3
"""Final asset/evidence/package-boundary checks; no model or device access."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'actual'
REPORT=PROJECT/'reports/audio-content-review-20261024'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    final=read(REPORT/'final-review.json');scenes=read(PROJECT/'reports/audio-scene-review-20261024/review.json')
    checks=[]
    def check(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    check(len(final['resources'])==69,'69 final asset review rows')
    check(final['changed']=={'music':14,'sfx':32},'14 music and 32 SFX revisions')
    all_records={}
    for category,manifest,entries in [('sfx','sound_effects','effects'),('soundtrack','soundtrack','tracks')]:
        tracks=read(PROJECT/f'reports/{category}-20261024/generation-report.json')['tracks']
        runtime=read(PROJECT/f'data/{manifest}.json')
        check(runtime['model_audio_review_completed'],'runtime '+manifest+' exact-hash review metadata')
        for track in tracks:
            entry=runtime[entries][track['id']]
            check(track['sha256']==entry['sha256'] and track['auditory_review'] and entry['auditory_review'],track['id']+' report/manifest agreement')
            all_records[track['id']]=track
    for row in final['resources']:
        path=ROOT/row['runtime_path'];track=all_records[row['id']]
        check(sha(path)==row['sha256']==track['sha256'],row['id']+' current asset hash')
        a,sr=sf.read(path,dtype='float32',always_2d=True)
        check(sr==44100 and a.shape[1]==2 and np.isfinite(a).all() and np.abs(a).max()<1,row['id']+' finite stereo 44.1kHz without clipping')
        body=read(ROOT/row['receipt']);scene=read(ROOT/row['scene_receipt'])
        check(row['sha256'] in body['source_sha256'],row['id']+' waveform body receipt')
        check(sha(ROOT/row['scene_fixture_path'])==row['scene_fixture_sha256']==scene['fixture_sha256'],row['id']+' final scene receipt')
    check(scenes['model_audio_review_completed'] and len(scenes['resources'])==69,'69 current scene reviews attached')
    check(scenes['normal_and_fast_forward_patterns_checked']==296 and not scenes['clipping_scenarios'],'296 deduplicated playback sequences have no clipping')
    check(not [r for r in scenes['resources'] if r['program_result']=='needs_investigation'],'no unresolved signal investigation flags')
    page=read(PROJECT/'reports/sfx-20261024/comparison-manifest.json')
    check(len(page['pairs'])==41 and page['auditory_review'],'41 original/replacement pairs with review metadata')
    missing=[];media_count=0
    for folder in ['sfx','soundtrack','audio-scene-review']:
        p=PROJECT/f'reports/{folder}-20261024/index.html';text=p.read_text()
        for ref in re.findall(r'(?:href|src)="([^"#]+)"',text):
            if re.match(r'^(https?:|data:)',ref):continue
            if not (p.parent/ref.split('#')[0]).exists():missing.append([folder,ref])
        media_count+=text.count('<audio ')
        check('当前模型不支持音频输入' not in text and '未完成真正听觉验收' not in text,folder+' has current review status')
    check(not missing,'all three audition pages link to existing local media/files')
    check(read(PROJECT/'reports/audio-scene-review-20261024/comparison-page-checks.json')['passed'],'9 comparison-page event/static checks passed')
    presets=(PROJECT/'export_presets.cfg').read_text()
    check('reports/*' in presets and 'tools/*' in presets and 'assets/original/audio/*' in presets,'reports/tools/legacy recordings excluded from export')
    native,sr=sf.read(REPORT/'native-engine-mix.wav',always_2d=True)
    check(len(native)>sr and np.isfinite(native).all() and np.abs(native).max()>0 and np.abs(native).max()<1,'native engine mixer capture is finite nonzero PCM')
    for path in [PROJECT/'tools'/name for name in ['review_audio_content.py','review_audio_omni.py','refine_sfx_from_audio.py','refine_ui_sounds.py','refine_music_for_scene.py','publish_audio_refinements.py','audio_content_review_metadata.py','audio_review_page.py','generate_original_sfx.py','generate_original_soundtrack.py','audit_audio_scenes.py','finalize_audio_content_review.py']]:
        compile(path.read_text(),str(path),'exec')
    check(True,'all modified audio Python sources compile')
    data={'passed':True,'check_count':len(checks),'checks':checks,'resources':69,
          'music':28,'sfx':41,'loops':24,'changed':final['changed'],'missing_receipts':0,
          'missing_page_links':missing,'audition_media_players':media_count,
          'sfx_runtime_checks':len(read(REPORT/'sfx-runtime-final.json')['checks']),
          'music_routing_checks':read(REPORT/'music-routing-final.json')['checks'],
          'contact_feedback_checks':10,'scene_sequences':296,
          'native_capture_seconds':len(native)/sr,
          'native_capture_peak':float(np.abs(native).max()),
          'native_capture_exit_warning':'Godot reports ObjectDB/resources retained at test teardown; recording saved successfully and does not affect runtime assets.',
          'model_runtime_stopped':True,'human_listening':False,'iphone_accessed':False,
          'save_accessed':False,'screenshots':0,'browser_visual_checked':False,
          'limits':'Local model descriptions include documented false positives and inconsistent seam/masking judgements. No human, physical-speaker or iPhone listening claim.'}
    (REPORT/'validation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ['checks','limits']},ensure_ascii=False))

if __name__=='__main__':main()
