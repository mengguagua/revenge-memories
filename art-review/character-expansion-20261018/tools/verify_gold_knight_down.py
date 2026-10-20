#!/usr/bin/env python3
"""Targeted pixel, layering, timing, video and review-scope checks; no images emitted."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image, ImageChops, ImageDraw
from revise_gold_knight_down import ROOT, OUT, REVISION, AXIS, FLOOR, BODY_BOB, PALETTE
from export_gallery import font, render_panel


def groups(row):
    return sum(value and (i == 0 or not row[i-1]) for i, value in enumerate(row))


def verify():
    data = json.loads((ROOT/'demos/gallery-data.json').read_text())
    profile = next(p for p in data['profiles'] if p['id']=='professions-class-7-ally-maps-tactical-walk')
    target = profile['id']+'--walk-down'
    expected_actions = {target, profile['id']+'--idle-down'}
    frames = [Image.open(ROOT/profile['newFrames'][str(i)]).convert('RGBA') for i in [4,5]]
    colors = {tuple(bytes.fromhex(c)) for c in PALETTE}
    for im in frames:
        assert im.size == (128,96)
        assert set(im.getchannel('A').getdata()) == {0,255}
        assert {p[:3] for p in im.getdata() if p[3]} == colors
        x0,y0,x1,y1 = im.getbbox()
        assert min(x0,y0,128-x1,96-y1)>=3
        pixels = {(x,y) for y in range(96) for x in range(128) if im.getpixel((x,y))[3]}
        stack = [next(iter(pixels))];seen=set(stack)
        while stack:
            x,y=stack.pop()
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    p=(x+dx,y+dy)
                    if p in pixels and p not in seen:seen.add(p);stack.append(p)
        assert seen == pixels, 'Detached limb pixels'
    air,land=frames
    # Upper body is one plate, shifted vertically by four output pixels only.
    assert air.crop((0,0,128,64)).tobytes()==land.crop((0,BODY_BOB,128,64+BODY_BOB)).tobytes()
    assert air.getbbox()[3]==83 and land.getbbox()[3]==FLOOR+1
    assert air.getchannel('A').crop((0,83,128,96)).getbbox() is None
    hoof_row=[land.getpixel((x,FLOOR))[3]!=0 for x in range(128)]
    assert groups(hoof_row)==2
    xs=[i for i,v in enumerate(hoof_row) if v]
    assert (min(xs)+max(xs))/2==AXIS
    assert land.getchannel('A').crop((0,FLOOR+1,128,96)).getbbox() is None
    # Verify all four airborne limbs remain represented after nearer limbs
    # occlude the farther ones; each far hoof retains visible contour pixels.
    names=['hind-left','hind-right','fore-left','fore-right']
    layers=[Image.open(OUT/f'source/air-{name}.png').convert('RGBA').getchannel('A') for name in names]
    visible_hoof_pixels={}
    for i,(name,layer) in enumerate(zip(names,layers)):
        bb=layer.getbbox(); assert bb and bb[3] < FLOOR
        foot=Image.new('L',(128,96));foot.paste(layer.crop((0,bb[3]-3,128,bb[3])),(0,bb[3]-3))
        for later in layers[i+1:]:foot=ImageChops.multiply(foot,ImageChops.invert(later))
        visible=sum(v!=0 for v in foot.getdata());assert visible>=4,(name,visible)
        visible_hoof_pixels[name]=visible
    baseline=json.loads((OUT/'baseline-digests.json').read_text())
    changed=[a['id'] for a in data['actions'] if baseline.get(a['id'])!=a['contentDigest']]
    assert set(changed)==expected_actions
    for p in data['profiles']:
        if p['id']==profile['id']:
            for i in [0,1,2,3,6,7]:
                assert (ROOT/p['newFrames'][str(i)]).read_bytes()==(ROOT/f'gold-knight-walk-v3-20261020/frames/frame-{i:03}.png').read_bytes()
    reports=[]
    draw=ImageDraw.Draw(Image.new('RGB',(584,328)))
    for action in data['actions']:
        if action['id'] not in expected_actions:continue
        assert action['ready'] and action['video'] and action['still']
        assert all(row['offset']==[0,0] and not row['flip'] for row in action['frames'])
        if action['id']==target:
            assert [row['frame'] for row in action['frames']]==[f for _ in range(3) for f in [4,5] for _ in range(16)]
        else:assert len(action['frames'])==32 and all(row['frame']==4 for row in action['frames'])
        probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0',
             '-show_entries','stream=width,height,nb_frames,duration','-of','json',str(ROOT/action['video'])]))['streams'][0]
        assert int(probe['nb_frames'])==len(action['frames'])
        assert abs(float(probe['duration'])-action['duration'])<.02
        assert [probe['width'],probe['height']]==[584,328]
        heading=profile['actorName']+' · '+action['name']
        assert any(draw.textbbox((0,0),heading,font=font(n))[2]<=536 for n in range(14,23))
        reports.append({'action':action['id'],'video':probe})
    up=next(a for a in data['actions'] if a['id']==target)
    assert profile['mapShadow']['path']=='gold-knight-walk-v3-20261020/ground-shadow.png'
    assert profile['mapShadow']['offset']==[0,-1]
    for light in [False,True]:
        a=render_panel(data,profile,up,up['frames'][0],True,4,light)
        b=render_panel(data,profile,up,up['frames'][16],True,4,light)
        assert a.crop((104,142,152,146)).tobytes()==b.crop((104,142,152,146)).tobytes()
    runtime=json.loads((OUT/'baseline-actual-hashes.json').read_text())
    runtime_changed=[p for p,h in runtime.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    html=(ROOT/'index.html').read_text()
    assert f'data-default-action="{target}"' in html
    for name in ['overview.mp4','down-phase-review.png']:
        assert (OUT/name).is_file() and f'{REVISION}/{name}' in html
    assets=[]
    for p in sorted(OUT.rglob('*.png')):
        with Image.open(p) as im:
            assets.append({'path':p.relative_to(ROOT).as_posix(),'pixels':list(im.size),'bytes':p.stat().st_size,
                           'purpose':'layer/reference source' if p.parent.name=='source' else 'review asset'})
    report={'status':'passed','runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
            'changed_actions':changed,'unchanged_actions':len(data['actions'])-len(changed),
            'centerline_fixed':True,'shared_body_bob_output_pixels':BODY_BOB,
            'airborne_bottom_row':82,'grounded_hoof_row':FLOOR,'airborne_clearance_pixels':10,
            'airborne_visible_hoof_pixels':visible_hoof_pixels,'grounded_visible_hoof_groups':2,
            'limbs_connected':True,'shadow_fixed':True,'palette_colors':8,'other_directions_unchanged':True,
            'text_safe_area_metrics':'passed','runtime_files_recorded':len(runtime),
            'runtime_changes_observed_since_start':runtime_changed,'runtime_writes_by_this_task':[],
            'actions':reports,'assets':assets,
            'review_method':'Existing source screenshot, native pixel maps, layer occlusion/registration checks and offline composition. Saved review images for user acceptance; no images returned to chat and no game window launched.'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['actions','assets']},ensure_ascii=False))


if __name__ == '__main__':
    verify()
