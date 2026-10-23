#!/usr/bin/env python3
"""Targeted checks and offline exports for the six Falcon Knight javelins."""
import ast, json, subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT, file_hash, relative, matched_export
from export_gallery import render_frame
from export_knight_complete import export_one

REV = 'falcon-flying-lance-v2-20261023'
OUT = ROOT / REV

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def verify(export=False):
    baseline = json.loads((OUT / 'baseline.json').read_text())
    data = json.loads((ROOT / 'demos/gallery-data.json').read_text())
    before = {a['id']: a for a in baseline['gallery']['actions']}
    now = {a['id']: a for a in data['actions']}
    profiles = {p['id']: p for p in data['profiles']}
    profile = profiles['professions-class-5-ally-battle']
    actions = [a for a in now.values() if a['profile'] == profile['id'] and 'javelin' in a['key']]
    changed = {k for k, a in now.items() if a['contentDigest'] != before[k]['contentDigest']}
    assert len(now) == len(before) == 775 and len(data['profiles']) == 97
    assert len(actions) == 6 and changed == {a['id'] for a in actions}
    assert all(a['ready'] for a in actions) and not data['validation']['structuralIssues']
    for k, a in now.items():
        for field in ['frames', 'fps', 'origin', 'contactTick', 'duration']:
            assert a.get(field) == before[k].get(field), (k, field)
    mapping = json.loads((ROOT / 'professions/class-5-ally/battle/frame_mapping.json').read_text())
    assert mapping['frame_mapping'] == baseline['battle']['frame_mapping']
    original_assets = json.loads((ROOT / 'falcon-knight-complete-v1-20261023/asset-manifest.json').read_text())['assets']
    held_frames = [row for row in original_assets if '/ally/battle/frame-' in row['path']]
    assert len(held_frames) == 12
    for row in held_frames:
        assert file_hash(ROOT / row['path']) == row['sha256']
    old_profile = next(p for p in baseline['gallery']['profiles'] if p['id'] == profile['id'])
    assert profile['newFrames'] == old_profile['newFrames']
    effect = profile['revisedEffects']['1ecba259419456']
    old_effect = old_profile['revisedEffects']['1ecba259419456']
    assert {k:v for k,v in effect.items() if k != 'path'} == {k:v for k,v in old_effect.items() if k != 'path'}
    reg = json.loads((OUT / 'registration.json').read_text())
    source = ROOT / reg['source_weapon']
    assert file_hash(source) == reg['source_sha256']
    master = Image.open(source).convert('RGBA')
    im = Image.open(ROOT / effect['path']).convert('RGBA')
    expected = Image.new('RGBA', (256,64))
    expected.alpha_composite(master.resize(tuple(reg['uniform_weapon_resample']), Image.Resampling.NEAREST), tuple(reg['composition_offset']))
    assert expected.tobytes() == im.tobytes() and im.size == (256,64)
    assert set(im.getchannel('A').getdata()) == {0,255}
    assert {p[:3] for p in im.getdata() if p[3]} <= {p[:3] for p in master.getdata() if p[3]}
    assert reg['visible_length_ratio'] > 1.7
    assets = json.loads((OUT / 'asset-manifest.json').read_text())['assets']
    for row in assets:
        assert file_hash(ROOT / row['path']) == row['sha256'] and (ROOT / row['path']).stat().st_size == row['bytes']
    for name in ['patch_falcon_flying_lance.py', 'verify_falcon_flying_lance.py']:
        ast.parse((ROOT / 'tools' / name).read_text())
    captures = []
    near = next(a for a in actions if a['key'] == 'class_5_ally_javelin')
    for tick in [21,31,51]:
        for light in [False,True]:
            path = OUT / f'near-{tick:03}-{"light" if light else "dark"}.png'
            render_frame(data,profile,near,tick,6,light,True).save(path,optimize=True)
            captures.append(relative(path))
    report = {'status':'assets_passed','revision':REV,'changed_actions':sorted(changed),'unrelated_actions_unchanged':len(now)-len(changed),'native_frames_fps_origins_contacts_unchanged':True,'held_weapon_frames_unchanged':True,'effect_metadata_and_trajectory_unchanged':True,'same_approved_weapon_master':True,'exact_master_resample_verified':True,'binary_alpha':True,'palette_colors':len({p[:3] for p in im.getdata() if p[3]}),'old_visible_length':30,'new_visible_length':53.75,'visible_length_ratio':reg['visible_length_ratio'],'offline_captures':captures,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    report['unchanged_held_body_png_hashes_verified'] = len(held_frames)
    write(OUT / 'verification.json',report)
    print(json.dumps({'status':'assets_passed','changed':6,'unchanged':769}),flush=True)
    if not export:
        return
    exports = []
    for a in actions:
        exports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a is near:
            exports.append(export_one(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        print('Exported ' + a['key'],flush=True)
    decoded = []
    for row in exports:
        info = json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT / row['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(info['nb_read_frames']) == row['frames']
        assert abs(float(info['duration'])-row['expected_duration']) < 1/row['fps']
        decoded.append({'path':row['video'],**info})
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path = ROOT / f'demos/{kind}/{a["id"]}{suffix}.{ext}'
            a[field] = relative(path) if matched_export(path,a['contentDigest']) else None
        assert a['video'] and a['still']
    assert near['closeVideo']
    (ROOT / 'gallery-data.js').write_text('window.GALLERY_DATA = ' + json.dumps(data,ensure_ascii=False,separators=(',',':')) + ';\n')
    (ROOT / 'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')) + '\n')
    report.update(status='passed',decoded_videos=len(decoded))
    write(OUT / 'verification.json',report)
    write(OUT / 'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded})
    print(json.dumps({'status':'passed','changed':6,'unchanged':769,'decoded_videos':len(decoded)}),flush=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--export',action='store_true')
    verify(parser.parse_args().export)
