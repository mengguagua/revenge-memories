#!/usr/bin/env python3
"""Targeted review checks for centerline, planted gallop, palette and scope."""
from pathlib import Path
from collections import deque
import hashlib
import json
import subprocess
from PIL import Image, ImageChops, ImageDraw
from revise_gold_knight_walk import ROOT, OUT, REVISION, PALETTE, BOB, BODY_CUT, FLOOR, OLD
from export_gallery import font, render_panel


def runs(values):
    return sum(value and (i == 0 or not values[i-1]) for i, value in enumerate(values))


def verify():
    data = json.loads((ROOT/'demos/gallery-data.json').read_text())
    profile = next(p for p in data['profiles'] if p['id'] == 'professions-class-7-ally-maps-tactical-walk')
    actions = [a for a in data['actions'] if a['profile'] == profile['id']]
    assert len(actions) == 8 and profile['revision'] == REVISION
    assert profile['mappingStatus'] == 'review_candidate'
    frames = [Image.open(ROOT/profile['newFrames'][str(i)]).convert('RGBA') for i in range(8)]
    palette = {tuple(bytes.fromhex(c)) for c in PALETTE}
    for i, im in enumerate(frames):
        assert im.size == (128, 96)
        assert set(im.getchannel('A').getdata()) == {0, 255}
        assert {p[:3] for p in im.getdata() if p[3]} <= palette
        assert im.getbbox()[3] <= 96
        if i >= 2:
            old = Image.open(OLD/f'frame-{i:03}.png').convert('RGBA')
            assert im.getchannel('A').tobytes() == old.getchannel('A').point(lambda v: 255 if v >= 128 else 0).tobytes()
    idle = Image.open(ROOT/'gold-knight-idle-v2-20261020/frames/idle-001.png').convert('RGBA')
    assert {p[:3] for p in idle.getdata() if p[3]} == palette
    # Shared body is vertically translated by exactly four output pixels,
    # without any lateral movement or independently redrawn body geometry.
    assert frames[0].crop((0, 0, 128, BODY_CUT)).tobytes() == frames[1].crop((0, BOB, 128, BODY_CUT+BOB)).tobytes()
    for im in frames[:2]:
        assert im.getbbox()[3] == FLOOR+1
        assert im.getchannel('A').crop((0, FLOOR+1, 128, 96)).getbbox() is None
    row0 = [frames[0].getpixel((x, FLOOR))[3] != 0 for x in range(128)]
    row1 = [frames[1].getpixel((x, FLOOR))[3] != 0 for x in range(128)]
    assert runs(row0) == 1 and runs(row1) == 2
    foot0 = [i for i, v in enumerate(row0) if v]
    foot1 = [i for i, v in enumerate(row1) if v]
    assert (min(foot0)+max(foot0))/2 == 64
    assert abs((min(foot1)+max(foot1))/2-64) <= .5
    assert max(foot0)-min(foot0) < max(foot1)-min(foot1)
    # Both registered poses must remain connected through the body/leg join.
    for im in frames[:2]:
        points = {(x,y) for y in range(96) for x in range(128) if im.getpixel((x,y))[3]}
        q = [next(iter(points))]; visited = set(q)
        while q:
            x,y = q.pop()
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    p = (x+dx,y+dy)
                    if p in points and p not in visited: visited.add(p);q.append(p)
        assert visited == points
    shadow = profile['mapShadow']
    assert shadow['size'] == [12,3] and shadow['offset'] == [0,-1]
    assert Image.open(ROOT/shadow['path']).getbbox() == (0,0,11,3)
    assert not profile.get('mapGround')
    reports = []
    for action in actions:
        assert action['ready'] and action['video'] and action['still']
        rows = action['frames']
        assert all(row['offset'] == [0,0] for row in rows)
        if action['key'].startswith('walk-'):
            order = action['neededFrames']
            assert len(rows) == 96
            assert [row['frame'] for row in rows] == [f for _ in range(3) for f in order for _ in range(16)]
        else: assert len(rows) == 32
        probe = json.loads(subprocess.check_output([
            '/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height,nb_frames,duration','-of','json',str(ROOT/action['video'])]))['streams'][0]
        assert int(probe['nb_frames']) == len(rows)
        assert abs(float(probe['duration'])-action['duration']) < .02
        assert [probe['width'],probe['height']] == [584,328]
        heading = profile['actorName']+' · '+action['name']
        d = ImageDraw.Draw(Image.new('RGB',(584,328)))
        assert any(d.textbbox((0,0),heading,font=font(n))[2] <= 536 for n in range(14,23))
        reports.append({'action':action['id'],'frames':len(rows),'video':probe})
    up = next(a for a in actions if a['key'] == 'walk-up')
    for light in [False,True]:
        a = render_panel(data,profile,up,up['frames'][0],True,4,light)
        b = render_panel(data,profile,up,up['frames'][16],True,4,light)
        # Shadow below the floor remains exactly fixed while the body bobs.
        assert a.crop((104,142,152,146)).tobytes() == b.crop((104,142,152,146)).tobytes()
    baseline = json.loads((OUT/'baseline-digests.json').read_text())
    changed = [a['id'] for a in data['actions'] if baseline.get(a['id']) != a['contentDigest']]
    assert set(changed) == {a['id'] for a in actions}
    assert baseline['professions-class-7-ally-maps-tactical-idle--idle-cycle'] == next(a for a in data['actions'] if a['id']=='professions-class-7-ally-maps-tactical-idle--idle-cycle')['contentDigest']
    runtime = json.loads((OUT/'baseline-actual-hashes.json').read_text())
    runtime_changed = [p for p,digest in runtime.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest]
    html = (ROOT/'index.html').read_text()
    assert f'data-default-action="{up["id"]}"' in html
    for name in ['overview.mp4','up-phase-review.png','palette-and-shadow.png']:
        assert (OUT/name).is_file() and f'{REVISION}/{name}' in html
    assets = []
    for path in sorted(OUT.rglob('*.png')):
        with Image.open(path) as im:
            assets.append({'path':path.relative_to(ROOT).as_posix(),'pixels':list(im.size),'bytes':path.stat().st_size,
                           'purpose':'preserved generation/reference source' if path.parent.name=='source' else 'review asset'})
    report = {'status':'passed','runtime_integrated':False,
              'changed_actions':changed,'unchanged_actions':len(data['actions'])-len(changed),
              'centerline_fixed':True,'shared_body_bob_output_pixels':BOB,
              'hoof_floor_output_row':FLOOR,'funnel_hoof_groups':1,'upright_hoof_groups':2,
              'body_leg_join_connected':True,'shadow_fixed_under_both_phases':True,
              'palette_matches_idle':True,'palette_colors':8,'other_directions_alpha_unchanged':True,
              'accepted_idle_unchanged':True,'text_safe_area_metrics':'passed',
              'runtime_files_recorded':len(runtime),'runtime_changes_observed_since_start':runtime_changed,
              'runtime_writes_by_this_task':[],'actions':reports,'assets':assets,
              'visual_review':'Original/new two phases, light/dark palette comparison and decoded video montage checked offline. No game window launched.',
              'browser_review':'Not performed; earlier file URL access restriction respected.'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['assets','actions']},ensure_ascii=False))


if __name__ == '__main__':
    verify()
