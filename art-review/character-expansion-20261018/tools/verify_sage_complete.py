#!/usr/bin/env python3
"""Targeted scholar source schedules, fixed map core, assets and video checks."""
import ast,json,re,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,pack_frame,relative,matched_export,SPELL_NAMES
from export_gallery import render_frame
from export_knight_complete import export_one
from import_sage_complete import REV,OUT,C,helper
from prepare_sage_complete import write

def verify(export=False):
    b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text())
    pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']}
    actions=[a for a in now.values() if a['profile'].startswith('professions-class-19-ally-')]
    assert len(actions)==97 and len(now)==872 and len(pp)==100 and all(a['ready'] for a in actions)
    assert not d['validation']['structuralIssues'] and set(now)-set(before)=={a['id'] for a in actions}
    for k,a in before.items():assert a['contentDigest']==now[k]['contentDigest'],('unrelated action',k)
    assert d['effects']==b['gallery']['effects']
    schedules=[]
    for a in actions:
        p=pp[a['profile']];assert p['classId']=='19' and p['className']=='博学术师' and p['revision']==REV
        assert not a.get('revisedFrames') and not a.get('reviewTailFrames')
        if a['kind']=='attack':
            v=b['variants'][a['key']]
            assert a['frames']==[pack_frame(f) for f in v['frames']]
            assert a['fps']==v['native_fps'] and a['origin']==v['actor_origin'] and a['contactTick']==v['contact_tick']
            item=int(re.search(r'_item_(\d+)',a['key']).group(1))
            schedules.append({'actor_id':'class-19-ally','class':'博学术师','class_sample_action':SPELL_NAMES[item],'hero_card_binding':None,'source_action':a['key'],'source_item_id':item,'source_program':v['source_program_address'],'ticks':len(a['frames']),'release_or_contact_tick':a['contactTick'],'source_contact_count':v['contact_count'],'effect_events_exact':True,'note':'职业动作库；实际可用法术依个人法术表与已解锁槽位。未授予所有展示法术、未新增伤害/恢复或阶段特性。'})
        elif a['key']=='idle-cycle':
            expected=[i for _ in range(2) for i,n in zip([0,1,2,1],[14,8,14,8]) for _ in range(n)]
            assert [f['frame'] for f in a['frames']]==expected
        elif a['kind']=='map_walk':
            start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']]
            assert [f['frame'] for f in a['frames']]==[i for _ in range(3) for i in [start,start+1] for _ in range(16)]
            assert all(f['offset']==[0,0] and not f['flip'] for f in a['frames'])
    assert len(schedules)==84
    source=json.loads((OUT/'native-reference-audit.json').read_text())
    for row in source['assets']:assert file_hash(ROOT/row['path'])==row['sha256']
    images={};checks=[]
    for kind,count,size in [('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96)),('battle',22,(320,256))]:
        paths=sorted((OUT/'ally'/kind).glob('frame-*.png'));assert len(paths)==count
        for path in paths:
            i=int(path.stem.split('-')[-1]);im=Image.open(path).convert('RGBA');images[kind,i]=im
            assert im.size==size and set(im.getchannel('A').getdata())=={0,255}
            assert {p[:3] for p in im.getdata() if p[3]}<=set(C)
            assert path.stat().st_size<50000
            parts=helper.parts((x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3])
            assert len(parts)==1,(kind,i,'detached pixels or body part')
            checks.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'connected_components':list(map(len,parts)),'colors':len({p[:3] for p in im.getdata() if p[3]})})
    for i,j in enumerate([0,1,2,1,0,1]):assert images['tactical-idle',i].tobytes()==images['tactical-idle',j].tobytes()
    for box in [[34,13,58,43],[34,43,55,57],[29,73,66,81]]:
        assert all(images['tactical-idle',i].crop(box).tobytes()==images['tactical-idle',0].crop(box).tobytes() for i in [1,2])
    for ids,y in [([0,1],43),([2,3],47),([4,5],47)]:
        box=[50,y-20,79,y+20];assert images['tactical-walk',ids[0]].crop(box).tobytes()==images['tactical-walk',ids[1]].crop(box).tobytes()
    for i,j in [(6,2),(7,3)]:assert images['tactical-walk',i].tobytes()==images['tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
    for i in range(16,37):
        for box in [[165,146,206,230],[150,230,222,256],[209,79,267,256]]:
            assert images['battle',i].crop(box).tobytes()==images['battle',0].crop(box).tobytes(),(i,box,'battle body or staff drift')
    reg=json.loads((OUT/'registration.json').read_text())
    assert all(row['clipped_opaque_pixels']==0 for row in reg['registrations'])
    for row in json.loads((OUT/'asset-manifest.json').read_text())['assets']:
        assert file_hash(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
    for name in ['prepare_sage_complete.py','import_sage_complete.py','verify_sage_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
    write(OUT/'action-effect-mapping.json',{'source_rules':['docs2/完整游戏设定.md:98','docs2/完整游戏设定.md:355','actual/core/combat_rules.gd:31','actual/core/item_rules.gd:27'],'no_runtime_rule_changes':True,'actor_id':'class-19-ally','actions':schedules})
    report={'status':'assets_passed','revision':REV,'new_profiles':3,'new_actions':97,'native_spell_variants':84,'existing_actions_unchanged':775,'native_frames_effect_events_fps_origins_contacts_exact':True,'all_prior_effect_assets_and_metadata_unchanged':True,'map_head_neck_torso_fixed':True,'map_idle_planted_boots_fixed':True,'mirrored_left_direction_exact':True,'battle_staff_body_waist_and_boots_fixed':True,'original_source_assets_unchanged':True,'registrations_clipped_pixels':0,'palette':C,'asset_checks':checks,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','new':97,'unchanged':775}),flush=True)
    if not export:return
    exports=[];captures=[]
    for a in actions:
        canonical=a['kind']!='attack' or not any(s in a['key'] for s in ['vs_heavy','far_'])
        if not canonical:continue
        p=pp[a['profile']]
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key'] in ['class_19_ally_item_23','class_19_ally_item_40','class_19_ally_item_42']:
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        if a['kind']=='map_walk' or a['key']=='idle-cycle':
            for tick in ([0,16] if a['kind']=='map_walk' else [0,14,22]):
                path=OUT/f'{a["key"]}-{tick:03}-light.png';render_frame(d,p,a,tick,8,True).save(path,optimize=True);captures.append(relative(path))
        if a['key'] in ['class_19_ally_item_23','class_19_ally_item_40','class_19_ally_item_42']:
            ticks=[0,a['contactTick']]
            for pose in ([21,23,26,29,30,31] if a['key'].endswith('_23') else [32,34,36] if a['key'].endswith('_42') else [24]):
                match=next((i for i,f in enumerate(a['frames']) if f['frame']==pose),None)
                if match is not None:ticks.append(match)
            for tick in sorted(set(ticks)):
                for light in [False,True]:
                    path=OUT/f'{a["key"]}-{tick:03}-{"light" if light else "dark"}.png';render_frame(d,p,a,tick,5,light,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['key'],flush=True)
    decoded=[]
    for e in exports:
        info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(info['nb_read_frames'])==e['frames'] and abs(float(info['duration'])-e['expected_duration'])<1/e['fps']
        decoded.append({'path':e['video'],**info})
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path) if matched_export(path,a['contentDigest']) else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures)
    write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded})
    print(json.dumps({'status':'passed','new':97,'unchanged':775,'decoded_videos':len(decoded)}),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
