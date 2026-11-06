#!/usr/bin/env python3
"""Focused review verification and exports for three allied appearance changes."""
import ast
import json
import subprocess
from types import SimpleNamespace

from PIL import Image

from build_gallery import ROOT, file_hash, relative, matched_export
from export_gallery import export, render_frame
from validate_gallery import box_at, outside

REV = 'battle-appearance-v1-20261031'
OUT = ROOT/REV


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    data = json.loads((ROOT/'demos/gallery-data.json').read_text())
    base = json.loads((OUT/'baseline.json').read_text())
    reg = json.loads((OUT/'registration.json').read_text())['frames']
    unaffected = json.loads((OUT/'unaffected-digests.json').read_text())
    now = {a['id']: a for a in data['actions']}
    assert all(now[k]['contentDigest'] == v for k, v in unaffected.items())
    assert not data['validation']['structuralIssues']
    targets = [now[k] for k in base['actions']]
    tracks = []
    for action in targets:
        old = base['actions'][action['id']]
        for key in ['frames', 'revisedFrames', 'reviewTailFrames', 'origin', 'contactTick', 'fps', 'key']:
            assert old.get(key) == action.get(key), (action['id'], key)
        assert action['ready']
        tracks.append({'id': action['id'], 'frames': len(action['frames']), 'contact_tick': action['contactTick'],
                       'timing_offsets_effects_unchanged': True})
    assets = json.loads((OUT/'asset-manifest.json').read_text())['assets']
    for record in assets:
        assert file_hash(ROOT/record['path']) == record['sha256']
    hair_sets = []
    for record in reg:
        cid, frame = record['class_id'], record['frame']
        path = OUT/f'class-{cid}/frame-{frame:03}.png'
        im = Image.open(path).convert('RGBA')
        assert im.size == ((320,384) if cid == 3 else (320,256))
        assert path.stat().st_size < 50000
        old = Image.open(ROOT/base['profiles'][str(cid)]['newFrames'][str(frame)]).convert('RGBA')
        if cid == 1:
            assert im.getchannel('A').tobytes() == old.getchannel('A').tobytes()
        if cid == 3:
            dx, dy = record['translation']
            hair_sets.append({(x-dx, y-dy) for y in range(im.height) for x in range(im.width)
                              if im.getpixel((x,y)) == (185,99,105,255)})
            b = record['modified_region']
            for y in range(im.height):
                for x in range(im.width):
                    if not (b[0] <= x < b[2] and b[1] <= y < b[3]):
                        assert im.getpixel((x,y)) == old.getpixel((x,y))
        if cid == 12:
            assert len({p for p in im.getdata() if p[3]}) == 5
            assert set(im.getchannel('A').getdata()) <= {0,255}
            assert im.getbbox()[3] == 256
    assert all(s == hair_sets[0] for s in hair_sets)
    profiles = {p['id']: p for p in data['profiles']}
    # Check actual alpha extents through every unique native placement.
    extent_checks = 0
    for action in targets:
        p = profiles[action['profile']]
        seen = set()
        for row in action.get('revisedFrames',action['frames']):
            state = json.dumps(row,sort_keys=True)
            if state in seen:
                continue
            seen.add(state)
            im = Image.open(ROOT/p['newFrames'][str(row['frame'])]).convert('RGBA')
            offset = row.get('offset',[0,0])
            point = [action['origin'][i]+offset[i]-p['anchor'][i] for i in range(2)]
            point[0] += row.get('shake',0)
            box = box_at(im, point, p['sourceFrameSize'], row.get('flip',False))
            assert not outside(box, action.get('viewport',data['viewport'])), (action['id'], box)
            camera = action['closeCamera']
            view = [action['origin'][i]+offset[i]+camera['offset'][i] for i in range(2)]+camera['size']
            assert not outside(box,view), (action['id'],box,view)
            extent_checks += 2
    for name in ['revise_battle_appearance_20261031.py','verify_battle_appearance_20261031.py','export_gallery.py']:
        ast.parse((ROOT/'tools'/name).read_text())
    export_targets = [a for a in targets if a.get('defaultVideo')]
    exports = []
    for a in export_targets:
        modes = [False,True] if a['kind'] == 'attack' else [False]
        for close in modes:
            result = export(data,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False))
            if result.get('skipped_unchanged'):
                result = {'action':a['id'], 'video':result['path'], 'frames':len(a['frames'])+len(a.get('reviewTailFrames',[])),
                          'fps':a['fps'], 'expected_duration':a['duration'], 'cached_export_verified':True}
            exports.append(result)
        print('Exported '+a['id'],flush=True)
    decoded = []
    for result in exports:
        if 'video' not in result:
            continue
        path = ROOT/result['video']
        stream = json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames',
                   '-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration',
                   '-of','json',str(path)],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(stream['nb_read_frames']) == result['frames']
        assert abs(float(stream['duration'])-result['expected_duration']) < 1/result['fps']
        decoded.append({'path': result['video'], **stream})
    for a in targets:
        for field,folder,suffix,extension in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path = ROOT/f'demos/{folder}/{a["id"]}{suffix}.{extension}'
            a[field] = relative(path) if matched_export(path,a['contentDigest']) else None
    captures = []
    for cid,key,ticks in [(3,'original_class_3_normal',[11,19,27,108]),
                         (1,'original_class_1_normal',[12,101]),(12,'class_12_ally_bow',[0,53,54])]:
        a = next(a for a in targets if a['profile']==f'professions-class-{cid}-ally-battle' and a['key']==key)
        p = profiles[a['profile']]
        for tick in ticks:
            for light in [False,True]:
                path = OUT/(f'review/playback-{cid}-{tick:03}-'+('light' if light else 'dark'))
                path = path.with_suffix('.png')
                render_frame(data,p,a,tick,4,light,True).save(path,optimize=True)
                captures.append(relative(path))
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    write(OUT/'action-contract.json', {'actors': [{'actor_id':base['profiles'][str(cid)]['actor'],
          'class_id':cid,'actions':[(a['key'],a['contactTick']) for a in targets if a['profile']==base['profiles'][str(cid)]['id']],
          'change':'appearance only; existing lance/javelin/bow actions and one original settlement retained'} for cid in [1,3,12]], 'tracks':tracks})
    report = {'status':'passed','source_poses':27,'changed_actions':len(targets),
              'unrelated_actions_unchanged':len(unaffected),'native_timing_offsets_effects_contacts_unchanged':True,
              'cavalry_original_alpha_geometry_preserved':True,'pegasus_hair_shape_and_pixel_count_identical':True,
              'pegasus_hair_pixels_each':len(hair_sets[0]),'archer_five_materials_binary_alpha':True,
              'alpha_extent_checks':extent_checks,'individual_sprite_png_bytes':
              {'min':min(a['bytes'] for a in assets if '/frame-' in a['path']),
               'max':max(a['bytes'] for a in assets if '/frame-' in a['path'])},
              'native_size_dark_light_art_checked':True,'offline_animation_captures':captures,
              'browser_ui_checked':False,'browser_limitation':'file protocol blocked; no alternate browser/server attempted',
              'caption_safe_area':'existing measured title/label renderer applied to this revision',
              'runtime_integrated':False,'visual_acceptance':'pending_user_review'}
    write(OUT/'verification.json',report)
    write(OUT/'export-report.json',{'exports':exports,'decoded_videos':decoded})
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
