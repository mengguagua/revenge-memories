#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted checks for alternating up-walk boots and an immutable upper body."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageChops
from build_gallery import ROOT,relative,matched_export
from export_gallery import render_panel,render_frame
from export_knight_complete import export_one
from revise_heavy_up_step import OUT,REV,LEG_BOX,leg_boxes

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());base=json.loads((OUT/'baseline.json').read_text());profiles={p['id']:p for p in d['profiles']}
    targets=[a for a in d['actions']if a['profile'].startswith('professions-class-2-')and a['key']in['walk-up','idle-up']];assert len(targets)==4 and all(a['ready']for a in targets)
    ids={a['id']for a in targets};now={a['id']:a['contentDigest']for a in d['actions']};assert set(now)==set(base['digests']);assert all(now[k]==v for k,v in base['digests'].items()if k not in ids)
    checked=[];exports=[];videos=[]
    for side in['ally','enemy']:
        mapping=json.loads((ROOT/f'professions/class-2-{side}/maps/frame_mapping.json').read_text());old=base['mappings'][side];original=next(s for s in old['scenarios']if s['id']=='tactical-walk');walk=next(s for s in mapping['scenarios']if s['id']=='tactical-walk')
        assert walk['timing']==original['timing']and walk['directions']==original['directions']
        assert next(s for s in mapping['scenarios']if s['id']=='tactical-idle')==next(s for s in old['scenarios']if s['id']=='tactical-idle')
        assert [r for r in walk['frame_mapping']if r['source_index']>=2]==[r for r in original['frame_mapping']if r['source_index']>=2]
        pair=[Image.open(OUT/side/f'frame-{i:03}.png').convert('RGBA')for i in[0,1]]
        oldrec=next(r for r in original['frame_mapping']if r['source_index']==1);oldimage=Image.open((ROOT/f'professions/class-2-{side}/maps'/oldrec['path']).resolve()).convert('RGBA');assert pair[1].tobytes()==oldimage.tobytes()
        for y in range(96):
            for x in range(128):
                if not(LEG_BOX[0]<=x<LEG_BOX[2]and LEG_BOX[1]<=y<LEG_BOX[3]):assert pair[0].getpixel((x,y))==pair[1].getpixel((x,y))
        boots=[leg_boxes(im)for im in pair];assert boots[0][1][3]-boots[0][0][3]>=6 and boots[1][0][3]-boots[1][1][3]>=6
        assert all(im.size==(128,96)and set(im.getchannel('A').getdata())<={0,255}for im in pair)
        a=next(a for a in targets if profiles[a['profile']]['side']==side and a['key']=='walk-up');p=profiles[a['profile']]
        assert len(a['frames'])==96 and [r['frame']for r in a['frames']]==[i for _ in range(3)for i in[0,1]for _ in range(16)]and all(r['offset']==[0,0]for r in a['frames'])
        panel0=render_panel(d,p,a,a['frames'][0],True,4,False,False).convert('RGB');panel1=render_panel(d,p,a,a['frames'][16],True,4,False,False).convert('RGB');box=ImageChops.difference(panel0,panel1).getbbox();assert box and 118<=box[0]<box[2]<=140 and 118<=box[1]<box[3]<=144,box
        for tick in[0,16]:render_frame(d,p,a,tick,4,False,False).save(OUT/f'{side}-phase-{tick//16}-playback.png',optimize=True)
        checked.append({'side':side,'phase_order':['left raised, right support','right raised, left support'],'boot_center_bounds':boots,'upper_body_and_equipment_pixel_identical':True,'actual_render_difference_bounds':list(box),'only_difference_is_legs':True})
    for a in targets:
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
        if a['key']=='walk-up':exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
    for r in exports:
        if not r.get('video'):continue
        q=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/r['video'])],capture_output=True,text=True,check=True);s=json.loads(q.stdout)['streams'][0];assert int(s['nb_read_frames'])==96 and abs(float(s['duration'])-96/r['fps'])<1/r['fps'];videos.append({'path':r['video'],'decoded':s})
    for a in targets:
        for field,kind,extension in[('video','videos','mp4'),('still','stills','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}.{extension}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':4,'native_phase_ticks':16,'walk_frames':96,'two_faction_leg_checks':checked,'unrelated_action_digests_unchanged':len(now)-4,'other_directions_idle_and_battle_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'dark/light enlarged phase pair plus offline real playback; no browser workaround or visible Godot window'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':4,'videos':videos,'exports':exports},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':4,'unrelated_actions_unchanged':len(now)-4,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
