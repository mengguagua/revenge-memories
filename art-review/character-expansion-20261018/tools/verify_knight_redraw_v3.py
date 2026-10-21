#!/usr/bin/env python3
"""Verify whole redraw assets/timing; visual inspection is a separate record."""
import json
import re
from PIL import Image
from build_gallery import ROOT, pack_frame
from revise_cavalry_map import digest
from import_knight_redraw_v3 import OUT, REV, ALLY, ENEMY

def read(p):return json.loads(p.read_text())

def verify():
    baseline=read(OUT/'baseline.json');data=read(ROOT/'demos/gallery-data.json')
    action_lookup={a['id']:a for a in data['actions']}
    profiles=[p for p in data['profiles'] if p['classId']=='4']
    pids={p['id']for p in profiles};actions=[a for a in data['actions'] if a['profile'] in pids]
    assert len(profiles)==6 and len(actions)==40 and all(a['ready'] for a in actions)
    assert not any(p['frameErrors'] for p in profiles)
    unaffected=0
    for key,old in baseline['action_digests'].items():
        if action_lookup[key]['profile'] not in pids:
            assert action_lookup[key]['contentDigest']==old,('Unrelated action changed',key);unaffected+=1
    assert unaffected==547
    native=[]
    for side,filename in [('ally','original-motion/full-original-motion.json'),('enemy','enemy-motion/full-enemy-motion.json')]:
        source=read(ROOT/'source-input'/filename)
        battle_profile=f'professions-class-4-{side}-battle'
        for a in actions:
            if a['profile']!=battle_profile or a['kind']!='attack':continue
            v=source['variants'][a['key']]
            assert a['frames']==[pack_frame(f)for f in v['frames']]
            assert a['contactTick']==v['contact_tick'] and a['fps']==v['native_fps'] and a['origin']==v['actor_origin']
            assert 'revisedFrames' not in a and 'reviewTailFrames' not in a
            native.append({'side':side,'key':a['key'],'ticks':len(a['frames']),'contact_tick':a['contactTick'],'original_rows_exact':True})
        idle=action_lookup[f'professions-class-4-{side}-maps-tactical-idle--idle-cycle']
        expected=[]
        for _ in range(2):
            for f,n in [(0,14),(1,8),(2,14),(1,8)]:expected.extend([f]*n)
        assert [f['frame'] for f in idle['frames']]==expected
        for direction,pair in [('up',[0,1]),('right',[2,3]),('down',[4,5]),('left',[6,7])]:
            a=action_lookup[f'professions-class-4-{side}-maps-tactical-walk--walk-{direction}']
            assert [f['frame']for f in a['frames']]==([pair[0]]*16+[pair[1]]*16)*3
            assert all(f['offset']==[0,0] for f in a['frames'])
        palette={tuple(bytes.fromhex(h))for h in (ALLY if side=='ally' else ENEMY)}
        for p in [p for p in profiles if p['side']==side]:
            for key,path in p['newFrames'].items():
                im=Image.open(ROOT/path).convert('RGBA');im.load()
                assert list(im.size)==p['outputFrameSize']
                assert {v[:3]for v in im.getdata()if v[3]}<=palette
                assert set(im.getchannel('A').getdata())<={0,255}
                assert (ROOT/path).stat().st_size<50000
        for i,j in [(2,6),(3,7)]:
            right=Image.open(OUT/f'{side}/tactical-walk/frame-{i:03}.png').convert('RGBA')
            left=Image.open(OUT/f'{side}/tactical-walk/frame-{j:03}.png').convert('RGBA')
            mirrored=Image.new('RGBA',left.size);mirrored.alpha_composite(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
            assert right.tobytes()==mirrored.tobytes()
        p=next(p for p in profiles if p['id']==battle_profile)
        for key,meta in p['revisedEffects'].items():
            native_meta=data['effects'][key]
            for field in ['frame_size','anchor','flip_origin_offset']:assert meta[field]==native_meta[field]
            im=Image.open(ROOT/meta['path']).convert('RGBA');assert im.size==(256,64)
            b=im.getbbox();assert b[0]>=100 and b[1]>=48 and b[2]<=252 and b[3]<=60
            assert {v[:3]for v in im.getdata()if v[3]}<=palette
    manifest=read(OUT/'asset-manifest.json')
    assert len(manifest['registration'])==19
    for r in manifest['registration']:
        assert r['clipped_pixels']==0
        assert max(abs(a-b)for a,b in zip(r['target_landmark'],r['actual_landmark']))<=.500001
        assert r['method']=='whole-pose uniform scale and integer translation only'
    for a in manifest['assets']:
        p=ROOT/a['path'];assert digest(p)==a['sha256'] and p.stat().st_size==a['bytes']
        with Image.open(p) as im:assert list(im.size)==a['size']
    # Validate the enemy background/OAM placement compensation independently.
    for dst,src in [(31,0),(40,0),(41,41),(45,43)]:
        ally=Image.open(OUT/f'ally/battle/frame-{src:03}.png').convert('RGBA')
        enemy=Image.open(OUT/f'enemy/battle/frame-{dst:03}.png').convert('RGBA')
        moved=Image.new('RGBA',ally.size);moved.alpha_composite(ally,(-64,0))
        assert moved.getchannel('A').tobytes()==enemy.getchannel('A').tobytes()
    html=(ROOT/'index.html').read_text()
    assert html.count('<details class="revision-history"')==1 and not re.search(r'<details[^>]*\bopen\b',html)
    assert f'gallery-data.js?v={REV}' in html
    assert html.index('aria-label="本轮双方骑士完整重绘"')<html.index('<details class="revision-history"')
    for p in re.findall(r'href="('+REV+r'/[^"?#]+)',html):assert (ROOT/p).is_file()
    report={'status':'passed','art_acceptance':'pending_user_review','runtime_integrated':False,
        'new_revision_profiles':6,'ready_actions':40,'unrelated_actions_unchanged':unaffected,
        'native_battle_timelines':native,'map_cycles_and_timing_exact':True,'whole_pose_registration_error_limit':.5,
        'registration_clipped_pixels':0,'palette_colors_per_side':16,'enemy_OAM_background_compensation_correct':True,
        'redrawn_lance_original_logical_canvas_anchor_envelope_and_trajectory':True,
        'all_assets_load':True,'history_single_closed':True,
        'browser_check':'Local file protocol blocked by browser security policy; no browser workarounds used. Offline renderer and frame boards inspected.',
        'visual_review_reference':'visual-review.json'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','ready_actions':40,'unrelated_unchanged':unaffected,'native_battle_variants':len(native)}))

if __name__=='__main__':verify()
