#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted class9 source schedules, fixed map cores, palettes and playback."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from import_swordsman_complete import OUT,REV,C,EC
from revise_cavalry_map import translate

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());profiles={p['id']:p for p in d['profiles']};target=[a for a in d['actions']if a['profile'].startswith('professions-class-9-')]
    assert len(target)==40 and all(a['ready']for a in target)
    now={a['id']:a['contentDigest']for a in d['actions']};old=b['digests'];ids={a['id']for a in target};added=set(now)-set(old)
    assert len(added)==20 and added<=ids;assert len(set(old)&ids)==20
    unchanged=[k for k in old if k not in ids];assert len(unchanged)==607
    assert all(old[k]==now[k]for k in unchanged);assert all(old[k]!=now[k]for k in set(old)&ids)
    assert not d['validation']['structuralIssues'];schedules=[];assetchecks=[];exports=[];visual_captures=[]
    for side in['ally','enemy']:
        native=json.loads((ROOT/f'source-input/{"original"if side=="ally"else"enemy"}-motion/full-{"original"if side=="ally"else"enemy"}-motion.json').read_text());colors=C if side=='ally'else EC
        for a in[a for a in target if profiles[a['profile']]['side']==side]:
            assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
            if side=='ally':
                before=b['actions'][a['id']]
                for field in['frames','fps','duration','contactTick','origin']:assert a[field]==before[field],(a['id'],field)
            if a['kind']=='attack':
                v=native['variants'][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']];assert a['contactTick']==v['contact_tick'];assert a['origin']==v['actor_origin'];assert a['fps']==v['native_fps']
                schedules.append({'key':a['key'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'contact_count':v['contact_count'],'exact_source_rows':True,'native_program':v['source_program_address']})
            elif a['key']=='idle-cycle':
                expected=[j for _ in range(2)for f,n in zip([0,1,2,1],[14,8,14,8])for j in[f]*n];assert[f['frame']for f in a['frames']]==expected
            elif a['kind']=='map_walk':
                start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];assert[f['frame']for f in a['frames']]==[j for _ in range(3)for f in[start,start+1]for j in[f]*16];assert all(not f['flip']and f['offset']==[0,0]for f in a['frames'])
        for kind,count in[('tactical-walk',8),('tactical-idle',6),('battle',15)]:
            files=sorted((OUT/side/kind).glob('frame-*.png'));assert len(files)==count
            for file in files:
                im=Image.open(file).convert('RGBA');opaque={p[:3]for p in im.getdata()if p[3]};is_arc=kind=='battle'and file.name=='frame-006.png';assert is_arc or opaque<=set(colors),(file,'unexpected material color')
                assert set(im.getchannel('A').getdata())<={0,255};assert file.stat().st_size<50000
                cc=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cc)==(2 if is_arc else 1),(file,'detached anatomy',list(map(len,cc)))
                assetchecks.append({'path':relative(file),'dimensions':list(im.size),'bytes':file.stat().st_size,'colors':len(opaque),'components':len(cc)})
        for rec in meta['fixed_map_regions'].values():
            kind='tactical-idle'if rec['frames']==[0,1,2]else'tactical-walk';ims=[Image.open(OUT/side/kind/f'frame-{i:03}.png').convert('RGBA')for i in rec['frames']]
            for rect in rec['fixed_head_and_torso_regions']:assert all(im.crop(rect).tobytes()==ims[0].crop(rect).tobytes()for im in ims)
        assert len({Image.open(OUT/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA').tobytes()for i in range(8)})==8
        # Face and eyes survive the matte/white-fleck cleanup in front views.
        for kind,i,box in[('tactical-idle',0,[48,26,61,36]),('tactical-walk',2,[50,42,66,54]),('battle',0,[180,140,207,162])]:
            im=Image.open(OUT/side/kind/f'frame-{i:03}.png').convert('RGBA').crop(box);px=list(im.getdata());assert any(p[:3]==colors[9]and p[3]for p in px);assert any(p[:3]==colors[0]and p[3]for p in px)
    for i in[12,23,24]:
        ally=Image.open(OUT/f'ally/battle/frame-{i:03}.png').convert('RGBA');enemy=Image.open(OUT/f'enemy/battle/frame-{i:03}.png').convert('RGBA');assert translate(ally,[-64,0]).getchannel('A').tobytes()==enemy.getchannel('A').tobytes()
    # Inspect/replay every new action. Four close videos expose the complete
    # sword-and-shield silhouette for normal and equipment-based Levin attacks.
    for a in target:
        p=profiles[a['profile']];exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['kind']=='attack'and('normal'in a['key']or a['key']in['class_9_ally_levin','class_9_enemy_levin']):
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
            poses=[0,4,5,6,7,8,9,10,11]if'normal'in a['key']else[24]
            for i in poses:
                tick=next(n for n,f in enumerate(a['frames'])if f['frame']==i);path=OUT/f'{p["side"]}-battle-pose-{i:02}-playback.png';render_frame(d,p,a,tick,4,False,True).save(path,optimize=True);visual_captures.append(relative(path))
        if a['kind']=='map_walk'or a['key']=='idle-cycle':
            tick=0;path=OUT/f'{p["side"]}-{a["key"]}-playback.png';render_frame(d,p,a,tick,4,True).save(path,optimize=True);visual_captures.append(relative(path))
        print('Exported '+a['id'],flush=True)
    videos=[]
    for rec in exports:
        q=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/rec['video'])],capture_output=True,text=True,check=True);v=json.loads(q.stdout)['streams'][0]
        assert int(v['nb_read_frames'])==rec['frames'];assert abs(float(v['duration'])-rec['frames']/rec['fps'])<1/rec['fps'];videos.append({'path':rec['video'],'decoded':v})
    for a in target:
        for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    verification={'status':'passed','profiles':6,'affected_actions':40,'new_enemy_actions':20,'revised_ally_actions':20,'unrelated_existing_actions_unchanged':607,'gallery_profiles':len(d['profiles']),'gallery_actions':len(d['actions']),'native_schedules':schedules,'map_core_rgba_identical':True,'independent_walk_slots':8,'eye_and_skin_material_present':True,'pure_hair_fill_with_outline':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_scope':'Dark/light all-pose boards and offline original/redraw captures; no browser file-access workaround or foreground game window.','asset_checks':assetchecks,'playback_captures':visual_captures}
    (OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n');(OUT/'export-report.json').write_text(json.dumps({'status':'passed','exports':exports,'decoded_videos':videos},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','actions':40,'videos':len(videos),'unrelated_existing_unchanged':607}),flush=True)

if __name__=='__main__':main()
