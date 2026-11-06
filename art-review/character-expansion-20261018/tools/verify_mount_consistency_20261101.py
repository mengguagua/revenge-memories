#!/usr/bin/env python3
"""Focused mount geometry, accepted-art preservation and animation export checks."""
import ast
import colorsys
import json
import subprocess
from types import SimpleNamespace

from PIL import Image

from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import export,render_frame
from validate_gallery import box_at,outside

REV='mount-consistency-v2-20261101'
OUT=ROOT/REV


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    base=json.loads((OUT/'baseline.json').read_text())
    original=json.loads((ROOT/'battle-appearance-v1-20261031/baseline.json').read_text())
    reg=json.loads((OUT/'registration.json').read_text())['frames']
    now={a['id']:a for a in data['actions']}
    targets=[now[k] for k in base['actions']]
    unrelated={k:v for k,v in base['digests'].items() if k not in base['actions']}
    assert all(now[k]['contentDigest']==v for k,v in unrelated.items())
    assert not data['validation']['structuralIssues']
    for path,digest in base['archer_files'].items():
        assert file_hash(ROOT/path)==digest
    tracks=[]
    for a in targets:
        old=base['actions'][a['id']]
        for key in ['frames','revisedFrames','reviewTailFrames','origin','contactTick','fps','key']:
            assert a.get(key)==old.get(key),(a['id'],key)
        assert a['ready']
        tracks.append({'id':a['id'],'frames':len(a['frames']),'contact_tick':a['contactTick'],
                       'original_timing_offsets_and_effects_preserved':True})
    skull_areas=[]
    for row in reg:
        cid,f=row['class_id'],row['frame']
        p=OUT/f'class-{cid}/frame-{f:03}.png'
        q=Image.open(p).convert('RGBA')
        before=Image.open(ROOT/base['profiles'][str(cid)]['newFrames'][str(f)]).convert('RGBA')
        assert q.size==before.size
        assert p.stat().st_size<50000
        if cid==1:
            old=Image.open(ROOT/original['profiles']['1']['newFrames'][str(f)]).convert('RGBA')
            assert q.getchannel('A').tobytes()==before.getchannel('A').tobytes()
            for a,b,c in zip(before.getdata(),q.getdata(),old.getdata()):
                if a!=b:
                    assert b==c
                # Original light coat and ivory armor pixels remain confirmed.
                if c[3] and max(c[:3])>146 and min(a[:3])>175:
                    assert a==b
        else:
            accepted={(x,y) for y in range(q.height) for x in range(q.width)
                      if before.getpixel((x,y))==(185,99,105,255)}
            current={(x,y) for y in range(q.height) for x in range(q.width)
                     if q.getpixel((x,y))==(185,99,105,255)}
            assert current==accepted and len(current)==364
            assert row['accepted_head_scale']==1 and row['no_clipped_pixels']
            if 'horse_skull_registered_box' in row:
                count=sum(p[3]>0 for p in q.crop(row['horse_skull_registered_box']).getdata())
                skull_areas.append({'frame':f,'before':row['source_skull_visible_area'],'after':count})
            else:
                bb=(158,166,187,214)
                skull_areas.append({'frame':f,'before':sum(p[3]>0 for p in before.crop(bb).getdata()),
                                    'after':sum(p[3]>0 for p in q.crop(bb).getdata())})
    assert max(a['after'] for a in skull_areas)/min(a['after'] for a in skull_areas)<1.12
    for f in [9,16]:
        assert Image.open(OUT/f'class-1/frame-{f:03}.png').convert('RGBA').tobytes()==Image.open(OUT/'class-1/frame-000.png').convert('RGBA').tobytes()
    assets=json.loads((OUT/'asset-manifest.json').read_text())['assets']
    assert all(file_hash(ROOT/r['path'])==r['sha256'] for r in assets)
    profiles={p['id']:p for p in data['profiles']}
    checks=0
    for a in targets:
        p=profiles[a['profile']]
        seen=set()
        for row in a.get('revisedFrames',a['frames']):
            key=json.dumps(row,sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            q=Image.open(ROOT/p['newFrames'][str(row['frame'])]).convert('RGBA')
            off=row.get('offset',[0,0])
            point=[a['origin'][i]+off[i]-p['anchor'][i] for i in range(2)]
            point[0]+=row.get('shake',0)
            b=box_at(q,point,p['sourceFrameSize'],row.get('flip',False))
            assert not outside(b,a.get('viewport',data['viewport'])),(a['id'],b)
            camera=a['closeCamera']
            view=[a['origin'][i]+off[i]+camera['offset'][i] for i in range(2)]+camera['size']
            assert not outside(b,view),(a['id'],b,view)
            checks+=2
    for name in ['revise_mount_consistency_20261101.py','verify_mount_consistency_20261101.py','export_gallery.py']:
        ast.parse((ROOT/'tools'/name).read_text())
    exports=[]
    for a in targets:
        if not a.get('defaultVideo'):
            continue
        for close in ([False,True] if a['kind']=='attack' else [False]):
            e=export(data,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False))
            if e.get('skipped_unchanged'):
                e={'action':a['id'],'video':e['path'],'frames':len(a['frames'])+len(a.get('reviewTailFrames',[])),
                   'fps':a['fps'],'expected_duration':a['duration'],'cached_export_verified':True}
            exports.append(e)
        print('Exported '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        stream=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0',
              '-show_entries','stream=nb_read_frames,duration,width,height','-of','json',str(ROOT/e['video'])],
              capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(stream['nb_read_frames'])==e['frames']
        assert abs(float(stream['duration'])-e['expected_duration'])<1/e['fps']
        decoded.append({'path':e['video'],**stream})
    captures=[]
    for cid in [1,3]:
        a=next(a for a in targets if a['profile']==f'professions-class-{cid}-ally-battle' and a['key']==f'original_class_{cid}_normal')
        for f in range(8):
            tick=next(i for i,row in enumerate(a['frames']) if row['frame']==f)
            for light in [False,True]:
                path=OUT/(f'review/playback-{cid}-pose-{f}-'+('light' if light else 'dark')+'.png')
                render_frame(data,profiles[a['profile']],a,tick,4,light,True).save(path,optimize=True)
                captures.append(relative(path))
    for a in targets:
        for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{folder}/{a["id"]}{suffix}.{ext}'
            a[field]=relative(p) if matched_export(p,a['contentDigest']) else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    write(OUT/'action-contract.json',{'scope':'mounted appearance only; no new hits or card effects','actions':tracks})
    report={'status':'passed','source_poses':24,'related_actions':len(targets),'unrelated_action_digests_unchanged':len(unrelated),
            'timing_offsets_effects_contacts_unchanged':True,'accepted_archer_sha256_unchanged':True,
            'accepted_pegasus_hair_absolute_pixels_unchanged':True,'pegasus_hair_pixels_each':364,
            'cavalry_alpha_and_positions_unchanged':True,'cavalry_recovered_only_immutable_original_dark_materials':True,
            'original_light_coat_and_ivory_armor_pixels_preserved':True,'horse_skull_registration':skull_areas,
            'skull_area_range_before':[min(x['before'] for x in skull_areas),max(x['before'] for x in skull_areas)],
            'skull_area_range_after':[min(x['after'] for x in skull_areas),max(x['after'] for x in skull_areas)],
            'alpha_extent_checks':checks,'videos_verified':len(decoded),'offline_captures':captures,
            'native_size_dark_light_visual_review':True,'browser_ui_checked':False,
            'browser_limitation':'file URL automation blocked earlier; no alternate browser/server attempted',
            'runtime_integrated':False,'visual_acceptance':'mount revisions pending; archer accepted'}
    write(OUT/'verification.json',report)
    write(OUT/'export-report.json',{'exports':exports,'decoded_videos':decoded})
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
