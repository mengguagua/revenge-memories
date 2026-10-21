#!/usr/bin/env python3
"""Targeted, offline class-4 coverage, registration and timing verification."""
import colorsys
import json
from pathlib import Path
import re
from PIL import Image, ImageChops
from build_gallery import ROOT, pack_frame
from revise_cavalry_map import digest, signature

REVISION='knight-complete-v1-20261021'
OUT=ROOT/REVISION

def read(p):return json.loads(p.read_text())
def same(a,b):return a.tobytes()==b.tobytes() and a.size==b.size

def verify():
    baseline=read(OUT/'baseline.json');data=read(ROOT/'demos/gallery-data.json')
    manifest=read(OUT/'asset-manifest.json');lookup={a['id']:a for a in data['actions']}
    for k,v in baseline['digests'].items():
        assert lookup[k]['contentDigest']==v,('Existing visual changed',k)
        assert signature(lookup[k])==baseline['timelines'][k],('Existing timeline changed',k)
    for group in ['mappings','source_files']:
        for p,sha in baseline[group].items():assert digest(ROOT/p)==sha,('Existing source changed',p)
    profiles=[p for p in data['profiles'] if p['classId']=='4']
    actions=[a for a in data['actions'] if a['profile'] in {p['id'] for p in profiles}]
    assert len(profiles)==6 and len(actions)==40 and all(a['ready'] for a in actions)
    assert not any(p['frameErrors'] for p in profiles)
    assert data['summary']=={'profiles':70,'actions':587,'ready':587,'pending':0}
    fixed=[];source_aliases=[];colors=[];assets=[];timelines=[]
    for side in ['ally','enemy']:
        directory=ROOT/f'professions/class-4-{side}'
        mapping=read(directory/'maps/frame_mapping.json')
        for scenario in mapping['scenarios']:
            frames={r['source_index']:Image.open((directory/'maps'/r['output_path']).resolve()).convert('RGBA') for r in scenario['frame_mapping']}
            idle=scenario['id']=='tactical-idle'
            if idle:
                for a,b in [(1,3),(1,5),(0,4)]:assert same(frames[a],frames[b])
                pairs=[(0,1,54),(0,2,54)]
            else:pairs=[(0,1,70),(2,3,70),(4,5,74),(6,7,70)]
            for a,b,y in pairs:
                box=(0,0,frames[a].width,y)
                assert same(frames[a].crop(box),frames[b].crop(box)),('Unstable upper body',side,a,b)
                assert not same(frames[a],frames[b]),('Missing gait phase',side,a,b)
                fixed.append({'side':side,'scenario':scenario['id'],'frames':[a,b],'fixed_box':list(box),'exact_pixel_match':True})
            if not idle:
                # Mirror about x=64; transparent edge is intentionally offset by1.
                for a,b in [(2,6),(3,7)]:
                    mir=Image.new('RGBA',(128,96));mir.alpha_composite(frames[b].transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
                    assert same(frames[a],mir)
            for i,im in frames.items():
                assert set(im.getchannel('A').getdata())<={0,255}
                visible=[p for p in im.getdata() if p[3]]
                assert len({p[:3] for p in visible})<=16
                colors.append({'side':side,'scenario':scenario['id'],'frame':i,'colors':len({p[:3] for p in visible}),
                  'mean_saturation':sum(colorsys.rgb_to_hsv(*[x/255 for x in p[:3]])[1] for p in visible)/len(visible),
                  'white_fraction':sum(min(p[:3])>180 for p in visible)/len(visible)})
        idle=Image.open(ROOT/f'source-input/legacy-assets/assets/original/graphics/map_units/class_4_{side}.png').convert('RGBA')
        walk=Image.open(ROOT/f'source-input/corrected-tactical-walk/class-4-{side}.png').convert('RGBA')
        for i,j in [(0,6),(2,7)]:
            a=idle.crop((i*24,0,i*24+24,24));b=walk.crop((j*32,0,j*32+32,24))
            assert same(a.crop(a.getbbox()),b.crop(b.getbbox()))
            source_aliases.append({'side':side,'idle':i,'walk':j,'tight_RGBA_identical':True})
        battle=read(directory/'battle/frame_mapping.json')
        motion=read(ROOT/f'source-input/{"original-motion/full-original-motion.json" if side=="ally" else "enemy-motion/full-enemy-motion.json"}')
        pid=f'professions-class-4-{side}-battle'
        for key in battle['variant_keys']:
            action=lookup[pid+'--'+key];v=motion['variants'][key]
            assert action['frames']==[pack_frame(row) for row in v['frames']]
            assert action['fps']==v['native_fps'] and action['origin']==v['actor_origin']
            assert action['contactTick']==v['contact_tick']
            assert 'revisedFrames' not in action and 'reviewTailFrames' not in action
            timelines.append({'side':side,'key':key,'ticks':len(action['frames']),'contact_tick':action['contactTick'],'native_timeline_exact':True})
        for f,path in battle['frame_mapping'].items():
            im=Image.open((directory/'battle'/path).resolve()).convert('RGBA')
            assert im.size==(320,256) and len({p[:3] for p in im.getdata() if p[3]})<=16
            assert set(im.getchannel('A').getdata())<={0,255}
        profile=next(p for p in profiles if p['id']==pid)
        for key,meta in profile['revisedEffects'].items():
            native=data['effects'][key];a=Image.open(ROOT/native['path']).convert('RGBA');b=Image.open(ROOT/meta['path']).convert('RGBA')
            assert same(a.getchannel('A'),b.getchannel('A'))
            for field in ['frame_size','anchor','flip_origin_offset']:assert meta[field]==native[field]
    for r in manifest['registration']:
        assert r['visible_clipped_pixels']==0
        assert max(abs(a-b) for a,b in zip(r['target_landmark'],r['registered_landmark']))<=.50001
    for a in manifest['assets']:
        p=ROOT/a['path'];im=Image.open(p);im.load()
        assert list(im.size)==a['size'] and p.stat().st_size==a['bytes'] and digest(p)==a['sha256']
        if '/frame-' in a['path']:assert a['bytes']<50000
        if '-dark.png' in a['path'] or '-light.png' in a['path']:assert a['bytes']<200000
        assets.append({'path':a['path'],'size':a['size'],'bytes':a['bytes']})
    html=(ROOT/'index.html').read_text()
    assert html.count('<details class="revision-history"')==1
    assert not re.search(r'<details[^>]*\bopen\b',html)
    default=re.search(r'data-default-action="([^"]+)"',html).group(1)
    assert default=='professions-class-4-ally-maps-tactical-idle--idle-cycle' and lookup[default]['ready']
    start=html.index('aria-label="本轮双方骑士全动作"');history=html.index('<details class="revision-history"')
    assert start<history<html.index('aria-label="本轮骑兵战斗与投枪配色"')
    for action in re.findall(r'href="\?action=([^"#]+)',html[start:history]):assert action in lookup
    for path in re.findall(r'href="('+REVISION+r'/[^"?#]+)',html):assert (ROOT/path).is_file()
    report={'status':'passed','art_review_status':'pending_user_visual_acceptance','runtime_integrated':False,
      'summary':data['summary'],'new_profiles':6,'new_actions':40,'existing_actions_unchanged':len(baseline['digests']),
      'existing_mappings_and_source_art_unchanged':True,'native_battle_timelines':timelines,
      'source_walk_phase_proof':source_aliases,'stable_upper_regions':fixed,'palette_statistics':colors,
      'registration_error_limit_output_pixels':.5,'all_registration_contours_unclipped':True,
      'lance_alpha_and_metadata_unchanged':True,'asset_checks':assets,
      'html':{'default_action':default,'revision_history_single_closed':True,'current_links_resolve':True},
      'visual_review':'Offline geometry, pixels, timing and assets checked; no browser screenshot or visible Godot run. User visual acceptance remains pending.'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','new_profiles','new_actions','existing_actions_unchanged']},ensure_ascii=False))

if __name__=='__main__':verify()
