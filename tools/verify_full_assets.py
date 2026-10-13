#!/usr/bin/env python3
"""Validate complete source graphics/animation/audio resources without a window."""
import hashlib,json,subprocess
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    graphics=json.loads((ROOT/'data/graphics.json').read_text());effects=json.loads((ROOT/'data/full_animation_effects.json').read_text());audio=json.loads((ROOT/'data/full_audio.json').read_text())
    failures=[];images=[];checks=0
    def check(ok,what):
        nonlocal checks
        checks+=1
        if not ok:failures.append(what)
    for asset in graphics['assets']:
        if not asset.get('kind','').startswith('full_'):continue
        path=ROOT/asset['path'].removeprefix('res://');im=Image.open(path);im.load()
        check(im.size==(asset['width'],asset['height']),asset['path']+'dimensions')
        check(im.mode=='RGBA',asset['path']+'alpha mode')
        check(im.width<=16384 and im.height<=16384,asset['path']+'GPU texture extent')
        check(set(im.getchannel('A').getdata())<={0,255},asset['path']+'unfiltered source alpha')
        images.append({'path':asset['path'],'usage':asset['kind'],'pixels':list(im.size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for cls in range(1,23):
        for side in ['ally','enemy']:
            key=f'class_{cls}_{side}';check(key in graphics['battle'] and key in graphics['map_units'],key+'class coverage')
    check(len(graphics['village_sprites'])==66,'all66 source personal map ids')
    total_frames=0;sound_requests=set()
    for key,variant in effects['variants'].items():
        sprite=graphics['battle'][f'class_{variant["source_class_id"]}_{variant["source_side"]}'];frames=variant['frames'];total_frames+=len(frames)
        check(variant['contact_count']==1 and 0<=variant['contact_tick']<len(frames),key+'single valid contact')
        check(all(0<=f['frame']<sprite['frames'] for f in frames),key+'body frame bounds')
        check(all(e['sprite'] in effects['sprites'] for f in frames for e in f['effects']),key+'effect resource references')
        for f in frames:sound_requests.update(f.get('sound_requests',[]))
    for q in sound_requests:check(f'{q:02X}' in audio['sfx_by_request'] or f'{q:02X}' in audio['control_requests'],f'source sound request{q:02X}')
    check(not effects['failures'],'all selected source animation routines finish')
    check(not audio['failures'],'all mapped music/sfx extracted')
    check(len(audio['routing']['hub_music_index_by_map'])==120,'hub music table ends before unrelated records')
    check(audio['routing']['hub_music_lookup_limit_exclusive']==111 and audio['routing']['hub_music_default_index']==4,'high map ids use source fallback')
    check(audio['routing']['enemy_by_route']==[0x70,0x77],'source actual enemy-phase music')
    audio_report=[];seen=set()
    for group in ['music_by_request','sfx_by_request']:
        for key,entry in audio[group].items():
            if entry['path'] in seen:continue
            seen.add(entry['path']);path=ROOT/entry['path'].removeprefix('res://')
            result=subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(path),'-f','f32le','-acodec','pcm_f32le','-'],capture_output=True,check=True)
            samples=np.frombuffer(result.stdout,dtype='<f4');peak=float(np.abs(samples).max(initial=0));clipped=int(np.count_nonzero(np.abs(samples)>=1.0))
            check(len(samples)>0 and peak>0,entry['path']+'decoded non-silent')
            check(clipped==0,entry['path']+'decoded clipping')
            duration=len(samples)/44100/2;check(abs(duration-float(entry['duration']))<.03,entry['path']+'duration')
            if entry.get('loop'):check(0<=entry['loop_offset']<duration,entry['path']+'loop point')
            audio_report.append({'request':key,'path':entry['path'],'duration':round(duration,6),'decoded_peak':round(peak,6),'clipped_samples':clipped,'bytes':path.stat().st_size})
    report={'source_revision':graphics['source_revision'],'checks':checks,'failures':failures,'new_graphics_count':len(images),'image_reference_limit_exceeded':[i for i in images if i['bytes']>=50000],'graphics':images,'class_side_coverage':44,'personal_sprite_coverage':66,'animation_variant_count':len(effects['variants']),'animation_frame_count':total_frames,'effect_sprite_count':len(effects['sprites']),'sound_requests':sorted(sound_requests),'audio':audio_report,'music_count':len(audio['music_by_request']),'sfx_count':len(audio['sfx_by_request']),'source_music_empty_slots':audio['ignored_requests'],'visual_review':'Original standing class contact sheet and Fire/Thunder/Seraphim/Sagittae frame composites inspected. Native runtime UI/camera/actor interaction screenshots belong to integration verification.','limitations':['Original PPU mid-scanline behavior is not emulated by the native renderer.','Contact pause is supplied by the native HP/damage event.','Enemy projectile palettes use each class standard palette; special palette variants affect the body sheets.']}
    (ROOT/'reports/full-assets-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['graphics','audio','source_music_empty_slots']},ensure_ascii=False))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
