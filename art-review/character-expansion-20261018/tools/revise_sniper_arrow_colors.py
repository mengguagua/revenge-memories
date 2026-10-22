#!/usr/bin/env python3
"""Replace only sniper projectile materials, using the existing effect override."""
import argparse, copy, json, subprocess
from types import SimpleNamespace
from PIL import Image, ImageDraw
from build_gallery import ROOT, file_hash, matched_export, relative
from export_gallery import render_frame, font
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts

REV='sniper-arrow-natural-v3-20261023'
OUT=ROOT/REV
SOURCES={'ally':('4af589272de96e','source-input/effects/4af589272de96e.png'),'enemy':('native-aadf144eefab4c','source-input/enemy-motion/effects/native-aadf144eefab4c.png')}
MATERIALS=[(140,107,69),(228,225,200)]

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def build(publish):
    original=Image.open(ROOT/SOURCES['ally'][1]).convert('RGBA');raw=Image.open(OUT/'source/natural-arrow-master.png').convert('RGBA')
    comp=parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]>=128)[0]
    bb=[min(x for x,y in comp),min(y for x,y in comp),max(x for x,y in comp)+1,max(y for x,y in comp)+1]
    bounds=original.getbbox();sample=raw.crop(bb).resize((bounds[2]-bounds[0],bounds[3]-bounds[1]),Image.Resampling.NEAREST)
    arrow=Image.new('RGBA',original.size)
    for y in range(bounds[1],bounds[3]):
        for x in range(bounds[0],bounds[2]):
            alpha=original.getpixel((x,y))[3]
            if not alpha:continue
            color=sample.getpixel((x-bounds[0],y-bounds[1]))[:3]
            material=min(MATERIALS,key=lambda c:sum((a-b)**2 for a,b in zip(c,color)))
            arrow.putpixel((x,y),(*material,alpha))
    assert arrow.getchannel('A').tobytes()==original.getchannel('A').tobytes()
    assert {p[:3]for p in arrow.getdata()if p[3]}==set(MATERIALS)
    # Preserve every original projectile pixel, including its anchors and
    # fletching. Only the new drawing's two materials are transferred.
    arrow.save(OUT/'flying-arrow.png',optimize=True)
    baseline=json.loads((OUT/'baseline.json').read_text());drafts={};source_records=[]
    for side,(key,path)in SOURCES.items():
        im=Image.open(ROOT/path).convert('RGBA');assert im.size==arrow.size and im.getchannel('A').tobytes()==arrow.getchannel('A').tobytes()
        source_records.append({'side':side,'effect_id':key,'path':path,'sha256':file_hash(ROOT/path),'size':list(im.size),'alpha_and_silhouette_unchanged':True})
        m=copy.deepcopy(baseline['mappings'][side]);m.setdefault('effect_overrides',{})[key]='../../../'+REV+'/flying-arrow.png'
        m['projectile_revision']=REV;m['review_note']+=' 飞行箭矢统一木色箭杆、米白箭头与尾羽，摆脱原作阵营色。'
        m['projectile_review']={'revision':REV,'materials':{'shaft':'8c6b45','head_and_fletching':'e4e1c8'},'native_alpha_size_anchors_and_effect_rows_unchanged':True,'applies_to':'class13 attacks only','source_drawing':'source/natural-arrow-master.png'}
        drafts[f'professions/class-13-{side}/battle/frame_mapping.json']=m
        if publish:write(ROOT/f'professions/class-13-{side}/battle/frame_mapping.json',m)
    board=Image.new('RGB',(1120,540),(220,222,216));draw=ImageDraw.Draw(board)
    for row,(side,(key,path))in enumerate(SOURCES.items()):
        for col,im in enumerate([Image.open(ROOT/path).convert('RGBA'),arrow]):
            im=im.crop((24,8,48,16)).resize((432,144),Image.Resampling.NEAREST);x=col*560+64;y=row*250+50;board.paste(im,(x,y),im)
            label=('盟军'if side=='ally'else'敌方')+(' · 原作阵营色'if col==0 else' · 木色箭杆 / 米白箭头与尾羽')
            draw.text((col*560+280,y+174),label,anchor='mm',fill=(23,38,56),font=font(18))
    board.save(OUT/'arrow-colors-light.png',optimize=True)
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'source_materials':'ImageGen recolor; native alpha retained pixel for pixel','generated_source_bounds':bb,'projectile':{'path':relative(OUT/'flying-arrow.png'),'size':[48,16],'bytes':(OUT/'flying-arrow.png').stat().st_size,'sha256':file_hash(OUT/'flying-arrow.png'),'opaque_pixels':sum(bool(p[3])for p in arrow.getdata()),'colors':['8c6b45','e4e1c8']},'original_effects':source_records,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    print(json.dumps({'published':publish,'arrow_bytes':(OUT/'flying-arrow.png').stat().st_size,'shape':'exact native alpha'}),flush=True)

def verify_export():
    baseline=json.loads((OUT/'baseline.json').read_text());data=json.loads((ROOT/'demos/gallery-data.json').read_text());profiles={p['id']:p for p in data['profiles']}
    changed=[a for a in data['actions']if a['contentDigest']!=baseline['actions'][a['id']]['contentDigest']]
    assert len(data['actions'])==len(baseline['actions'])==731 and not data['validation']['structuralIssues']
    assert len(changed)==26 and all(a['profile'].startswith('professions-class-13-')and a['context']=='battle'for a in changed)
    attacks=[a for a in changed if a['kind']=='attack'];assert len(attacks)==18
    for side in SOURCES:
        m=json.loads((ROOT/f'professions/class-13-{side}/battle/frame_mapping.json').read_text());old=baseline['mappings'][side]
        for key in old:
            if key!='review_note':assert m[key]==old[key],('body or source mapping changed',side,key)
        p=profiles[f'professions-class-13-{side}-battle'];key,path=SOURCES[side]
        assert p['revisedEffects'][key]['path']==REV+'/flying-arrow.png'
        for k,v in p['revisedEffects'][key].items():
            if k!='path':assert v==data['effects'][key][k]
    exports=[];captures=[];unchanged_reactions=[]
    for a in changed:
        old=baseline['actions'][a['id']]
        for key in ['frames','fps','duration','origin','viewport','neededFrames','contactTick']:assert a.get(key)==old.get(key),(a['id'],key)
        p=profiles[a['profile']]
        if a['kind']!='attack':
            # The existing cache signature adds an empty effect-override
            # dictionary to reactions too. Their rendered pixels are identical.
            oldp=baseline['profiles'][a['profile']]
            for tick in range(len(a['frames'])):
                assert render_frame(data,p,a,tick,4).tobytes()==render_frame(data,oldp,old,tick,4).tobytes()
            unchanged_reactions.append(a['id'])
        exports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in ['class_13_ally_bow','class_13_ally_silver_bow','class_13_enemy_bow']:
            exports.append(export_one(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        if a['key']in ['class_13_ally_bow','class_13_ally_silver_bow','class_13_enemy_bow','class_13_ally_bow_far_enemy','class_13_ally_silver_bow_far_enemy','class_13_enemy_bow_far_ally']:
            key=SOURCES[p['side']][0];ticks=[i for i,row in enumerate(a['frames'])if any(e['sprite']==key for e in row.get('effects',[]))];assert ticks
            tick=ticks[len(ticks)//2]
            for light in [False,True]:
                target=OUT/(a['key']+('-light.png'if light else'-dark.png'));render_frame(data,p,a,tick,6,light).save(target,optimize=True);captures.append({'path':relative(target),'tick':tick})
        print('Refreshed '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        s=json.loads(probe.stdout)['streams'][0];assert int(s['nb_read_frames'])==e['frames']and abs(float(s['duration'])-e['frames']/e['fps'])<1/e['fps'];decoded.append({'video':e['video'],'stream':s})
    for a in changed:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    write(OUT/'verification.json',{'status':'passed','physical_attack_changes':18,'unchanged_reactions_cache_refreshed':unchanged_reactions,'unrelated_action_digests_unchanged':705,'all_original_timelines_positions_and_contact_ticks_unchanged':True,'body_frames_and_poses_unchanged':True,'native_alpha_unchanged':True,'exports':exports,'decoded_videos':decoded,'captures':captures,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_scope':'Offline synchronized projectile-flight captures in both factions, near/far, light/dark; browser not rendered.'})
    print(json.dumps({'status':'passed','attack_actions':18,'reaction_pixels_unchanged':8,'videos':len(decoded),'unrelated_unchanged':705}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--verify-export',action='store_true');a=p.parse_args();verify_export()if a.verify_export else build(a.publish)
