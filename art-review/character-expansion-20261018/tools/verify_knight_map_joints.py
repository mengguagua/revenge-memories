#!/usr/bin/env python3
"""Focused checks for complete clothing, attached legs and unchanged timings."""
import json
import re
from PIL import Image
from build_gallery import ROOT
from revise_cavalry_map import digest, signature
from revise_knight_map_joints import OUT, PREVIOUS, REVISION, components

def read(p):return json.loads(p.read_text())

def verify():
    baseline=read(OUT/'baseline.json');data=read(ROOT/'demos/gallery-data.json')
    actions={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']}
    changed_profiles={f'professions-class-4-{s}-maps-{k}' for s in ['ally','enemy'] for k in ['tactical-idle','tactical-walk']}
    assert data['summary']=={'profiles':70,'actions':587,'ready':587,'pending':0}
    unaffected=0
    for key,old_digest in baseline['digests'].items():
        a=actions[key];assert signature(a)==baseline['timelines'][key],('Changed timing',key)
        if a['profile'] not in changed_profiles:
            assert a['contentDigest']==old_digest,('Unrelated action changed',key);unaffected+=1
    changed_mappings=set(baseline['mappings'])
    for p,sha in baseline['all_mapping_hashes'].items():
        if p not in changed_mappings:assert digest(ROOT/p)==sha,('Unrelated mapping changed',p)
    for record in read(PREVIOUS/'asset-manifest.json')['assets']:
        assert digest(ROOT/record['path'])==record['sha256'],'Previous art must remain intact'
    checks=[]
    for side in ['ally','enemy']:
        base=Image.open(PREVIOUS/f'{side}/tactical-idle/frame-000.png').convert('RGBA')
        frames={i:Image.open(OUT/f'{side}/tactical-idle/frame-{i:03}.png').convert('RGBA') for i in range(6)}
        palette={p[:3] for p in base.getdata() if p[3]}
        for i,im in frames.items():
            assert im.crop((0,0,96,66)).tobytes()==base.crop((0,0,96,66)).tobytes(),'Body, clothes or leg roots changed'
            assert len(components(im))==1,'Detached leg/cloth fragment'
            assert len(components(im,64))==5,'Expected four separate lower legs and original tail tip'
            assert {p[:3] for p in im.getdata() if p[3]}<=palette
            assert set(im.getchannel('A').getdata())<={0,255}
        for a,b in [(1,3),(1,5),(0,4)]:assert frames[a].tobytes()==frames[b].tobytes()
        for phase in [1,2]:assert frames[phase].tobytes()!=frames[0].tobytes()
        for i,phase in [(6,0),(7,2)]:
            left=Image.open(OUT/f'{side}/tactical-walk/frame-{i:03}.png').convert('RGBA')
            assert left.crop((16,16,112,112)).crop((0,0,96,80)).tobytes()==frames[phase].crop((0,0,96,80)).tobytes()
            right=Image.open(OUT/f'{side}/tactical-walk/frame-{i-4:03}.png').convert('RGBA')
            mirrored=Image.new('RGBA',left.size);mirrored.alpha_composite(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
            assert right.tobytes()==mirrored.tobytes(),'Mirror geometry or color differs'
        mp=ROOT/f'professions/class-4-{side}/maps/frame_mapping.json';current=read(mp)
        old=baseline['mappings'][str(mp.relative_to(ROOT))]
        old_walk=next(s for s in old['scenarios'] if s['id']=='tactical-walk')
        walk=next(s for s in current['scenarios'] if s['id']=='tactical-walk')
        for i in [0,1,4,5]:
            a=next(r for r in walk['frame_mapping'] if r['source_index']==i)
            b=next(r for r in old_walk['frame_mapping'] if r['source_index']==i)
            assert a==b,'Up/down frame record changed'
        for s in current['scenarios']:
            prior=next(p for p in old['scenarios'] if p['id']==s['id']);assert s['timing']==prior['timing']
            for r in s['frame_mapping']:
                p=(mp.parent/r['output_path']).resolve();im=Image.open(p);im.load()
                assert digest(p)==r['sha256'] and list(im.size)==s['output_frame_size']
        checks.append({'side':side,'complete_body_and_clothing_pixel_identical':True,'root_rows_64_65_pixel_identical':True,
          'full_sprite_connected':True,'four_separate_lower_legs_plus_fixed_tail':True,'center_and_mirror_match':True,
          'up_down_frames_unchanged':True,'palette_unchanged':True})
    manifest=read(OUT/'asset-manifest.json')
    for a in manifest['assets']:
        p=ROOT/a['path'];assert digest(p)==a['sha256'] and p.stat().st_size==a['bytes']
        assert a['bytes']<(200000 if 'board' in a['purpose'] else 50000)
    html=(ROOT/'index.html').read_text();assert html.count('<details class="revision-history"')==1 and not re.search(r'<details[^>]*\bopen\b',html)
    assert html.index('aria-label="本轮骑士腿根与服饰衔接"')<html.index('<details class="revision-history"')
    assert f'gallery-data.js?v={REVISION}' in html
    report={'status':'passed','art_review_status':'pending_user_visual_acceptance','runtime_integrated':False,
      'checks':checks,'unchanged_action_timelines':len(actions),'unaffected_action_digests':unaffected,
      'all_battle_and_other_class_mappings_unchanged':True,'previous_revision_images_intact':True,
      'history_single_default_closed':True,'no_browser_or_godot_launch':True,
      'scope':'Offline pixel, connected-component, path and timing checks. User visual acceptance remains pending.'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','sides':2,'timelines_unchanged':len(actions),'unaffected_actions':unaffected}))

if __name__=='__main__':verify()
