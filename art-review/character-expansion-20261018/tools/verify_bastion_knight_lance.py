#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted all-class22 weapons, unchanged body anchors/native programs, exports."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from revise_cavalry_map import translate
from revise_bastion_knight_lance import OUT,REV,PALETTE,EPALETTE

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());base=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());profiles={p['id']:p for p in d['profiles']};targets=[a for a in d['actions']if a['profile'].startswith('professions-class-22-')]
    assert len(targets)==40 and all(a['ready']for a in targets);ids={a['id']for a in targets};now={a['id']:a['contentDigest']for a in d['actions']};assert set(now)==set(base['digests']);assert all(now[k]==v for k,v in base['digests'].items()if k not in ids)
    changed=[k for k in now if now[k]!=base['digests'][k]];assert set(changed)==ids
    assert not d['validation']['structuralIssues'];timing=[];checks=[];reports=[]
    native={side:json.loads((ROOT/f'source-input/{"original"if side=="ally"else"enemy"}-motion/full-{"original"if side=="ally"else"enemy"}-motion.json').read_text())for side in['ally','enemy']}
    for a in targets:
        old=base['actions'][a['id']];p=profiles[a['profile']]
        for key in['frames','fps','duration','contactTick','origin']:assert a[key]==old[key],(a['id'],key)
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
        if a['kind']=='attack':
            v=native[p['side']]['variants'][a['key']];assert a['frames']==[pack_frame(r)for r in v['frames']]and a['contactTick']==v['contact_tick']and a['fps']==v['native_fps']and v['contact_count']==1
            if'normal'in a['key']:assert len(a['frames'])==535 and a['contactTick']==245
            timing.append({'action':a['id'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'contact_count':1,'native_rows_equal':True})
    for side in['ally','enemy']:
        palette=set(PALETTE if side=='ally'else EPALETTE);folder=ROOT/f'professions/class-22-{side}';mapping=json.loads((folder/'battle/frame_mapping.json').read_text());old=base['mappings'][side+'/battle'];images={}
        assert mapping['variant_keys']==old['variant_keys']and set(mapping['effect_overrides'])==set(old['effect_overrides'])
        for i,path in mapping['frame_mapping'].items():
            im=Image.open((folder/'battle'/path).resolve()).convert('RGBA');before=Image.open((folder/'battle'/old['frame_mapping'][i]).resolve()).convert('RGBA');images[int(i)]=im
            assert im.size==(320,256)and set(im.getchannel('A').getdata())<={0,255};assert {p[:3]for p in im.getdata()if p[3]}<=palette
            if int(i)<12:
                assert im.crop((190,128,225,162)).tobytes()==before.crop((190,128,225,162)).tobytes(),(side,i,'head changed')
                # The new broad guard can occupy x180..185,y205..209 next to
                # the gauntlet; that area is weapon space, above the actual legs.
                assert im.crop((190,211,320,256)).tobytes()==before.crop((190,211,320,256)).tobytes(),(side,i,'legs changed')
            if int(i)==27:assert im.tobytes()==before.tobytes(),(side,'release hand changed')
            comp=parts((x,y)for y in range(256)for x in range(320)if im.getpixel((x,y))[3]);assert len(comp)==1,(side,i,'fragment',[len(c)for c in comp])
        alias=translate(images[0],[-64,0])if side=='enemy'else images[0]
        for i in[13,24]:assert images[i].tobytes()==alias.tobytes()
        maps=json.loads((folder/'maps/frame_mapping.json').read_text());oldmaps=base['mappings'][side+'/maps']
        for s in maps['scenarios']:
            prev=next(x for x in oldmaps['scenarios']if x['id']==s['id']);assert s['timing']==prev['timing']and s['directions']==prev['directions'];frames={}
            for rec in s['frame_mapping']:
                i=rec['source_index'];im=Image.open((folder/'maps'/rec['path']).resolve()).convert('RGBA');oldrec=next(x for x in prev['frame_mapping']if x['source_index']==i);before=Image.open((folder/'maps'/oldrec['path']).resolve()).convert('RGBA');frames[i]=im
                assert im.size==tuple(s['output_frame_size'])and set(im.getchannel('A').getdata())<={0,255}and {p[:3]for p in im.getdata()if p[3]}<=palette
                box=(34,8,78,32)if s['id']=='tactical-idle'else(49,31,80,49)
                assert im.crop(box).tobytes()==before.crop(box).tobytes(),(side,s['id'],i,'head changed')
                box=(28,68,82,96)if s['id']=='tactical-idle'else(40,82,87,96)
                assert im.crop(box).tobytes()==before.crop(box).tobytes(),(side,s['id'],i,'feet changed')
                comp=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(comp)==1,(side,s['id'],i,'fragment',[len(c)for c in comp])
            if s['id']=='tactical-walk':
                for i in[2,3]:assert frames[i+4].tobytes()==frames[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
            else:
                assert frames[0].tobytes()==frames[4].tobytes()and frames[1].tobytes()==frames[3].tobytes()==frames[5].tobytes()
        effect=next(iter(profiles[f'professions-class-22-{side}-battle']['revisedEffects'].values()));assert effect['frame_size']==[80,16]and effect['anchor']==[40,8]
        projectile=Image.open(ROOT/effect['path']).convert('RGBA');assert projectile.size==(320,64)and set(projectile.getchannel('A').getdata())<={0,255}
        checks.append({'side':side,'native_frames_offsets_fps_and_contact_ticks_unchanged':True,'protected_head_and_leg_pixels_unchanged':True,'left_right_exact_mirrors':True,'empty_release_pose_unchanged':True,'no_detached_body_or_weapon_fragments':True,'projectile_anchor':[40,8],'projectile_logical_size':[80,16]})
    for k,v in meta['placements'].items():
        assert v['clipped_pixels']==0
        if not k.startswith('projectile-'):assert v['visible_pommel_pixels']>0,(k,'pommel disappeared')
        if k.startswith('battle-'):assert v['shared_asset_size']==[104,21]
    for a in targets:
        reports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['kind']=='attack'and('normal'in a['key']or a['key']in['class_22_ally_javelin','class_22_enemy_javelin']):
            reports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)));p=profiles[a['profile']]
            poses=[0,10,11]if'normal'in a['key']else[25,27]
            for i in poses:
                tick=next(n for n,row in enumerate(a['frames'])if row['frame']==i);render_frame(d,p,a,tick,4,False,True).save(OUT/f'{p["side"]}-battle-pose-{i:02}-playback.png',optimize=True)
            if'javelin'in a['key']:
                tick=next(n for n,row in enumerate(a['frames'])if row['effects']);render_frame(d,p,a,tick,4,True,True).save(OUT/f'{p["side"]}-flying-playback.png',optimize=True)
        print('Exported '+a['id'],flush=True)
    videos=[]
    for rec in reports:
        q=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/rec['video'])],capture_output=True,text=True,check=True);s=json.loads(q.stdout)['streams'][0]
        assert int(s['nb_read_frames'])==rec['frames']and abs(float(s['duration'])-rec['frames']/rec['fps'])<1/rec['fps'];videos.append({'path':rec['video'],'decoded':s})
    for a in targets:
        for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','profiles':6,'affected_actions':40,'unrelated_action_digests_unchanged':len(now)-40,'gallery_profiles':len(d['profiles']),'gallery_actions':len(d['actions']),'native_attack_schedules':timing,'native_idle_ticks':[14,8,14,8],'walk_ticks_per_phase':16,'both_factions':checks,'weapon_master_shared':True,'same_battle_weapon_size_all_poses':[104,21],'weapon_clipping':False,'visible_pommel_every_held_weapon_pose':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'Generated source and restoration, dark/light all-pose boards, offline original/redraw playback captures, all40 videos plus4 close videos decoded. No browser workaround or visible Godot window.'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':len(reports),'videos':videos,'exports':reports},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','affected_actions':40,'unrelated_actions_unchanged':len(now)-40,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
