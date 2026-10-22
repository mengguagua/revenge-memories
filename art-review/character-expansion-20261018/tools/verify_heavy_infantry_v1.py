#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused native motion, pose registration and offline playback checks for class2."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,pack_frame,matched_export,relative
from export_knight_complete import export_one
from export_gallery import render_frame,font
from import_heavy_infantry_v1 import REV,OUT,ALLY,ENEMY
from import_knight_redraw_v3 import parts

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());profiles=[p for p in d['profiles']if p.get('revision')==REV];lookup={p['id']:p for p in profiles};actions=[a for a in d['actions']if a['profile']in lookup]
    assert len(profiles)==6 and len(actions)==40 and all(a['ready']for a in actions),(len(profiles),len(actions))
    assert not d['validation']['structuralIssues']
    native={s:json.loads((ROOT/f'source-input/{"original"if s=="ally"else"enemy"}-motion/full-{"original"if s=="ally"else"enemy"}-motion.json').read_text())for s in['ally','enemy']};timing=[];cards=[]
    for a in actions:
        p=lookup[a['profile']]
        if a['kind']=='attack':
            v=native[p['side']]['variants'][a['key']];assert a['frames']==[pack_frame(r)for r in v['frames']]and a['contactTick']==v['contact_tick']and a['fps']==v['native_fps']and v['contact_count']==1
            timing.append({'action':a['id'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'contact_frame_in_ui':a['contactTick']+1,'source_rows_equal':True,'contact_count':v['contact_count']})
            cards.append({'character_id':p['actor'],'class_id':2,'card_or_weapon':'普通攻击（现行枪系武器）'if'normal'in a['key']else'投枪／格拉迪乌斯的原远程武器程序','animation':a['key'],'effect_tick':a['contactTick'],'effect_count':1,'extra_damage_or_shield_added':False})
        elif a['key']=='idle-cycle':
            assert [r['frame']for r in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
        elif a['kind']=='map_walk':
            direction=a['key'][5:];start={'up':0,'right':2,'down':4,'left':6}[direction]
            assert len(a['frames'])==96 and [r['frame']for r in a['frames']]==[f for _ in range(3)for f in[start,start+1]for _ in range(16)]and all(r['offset']==[0,0]for r in a['frames'])
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
    base=json.loads((OUT/'baseline.json').read_text());current={a['id']:a['contentDigest']for a in d['actions']};unchanged=[k for k in base['digests']if not k.startswith('professions-class-2-')];assert all(current[k]==base['digests'][k]for k in unchanged)
    manifest=json.loads((OUT/'asset-manifest.json').read_text());assert len(manifest['registration'])==21 and all(r['clipped_pixels']==0 for r in manifest['registration'])
    center_error=max(max(abs(a-b)for a,b in zip(r['actual_landmark'],r['target_landmark']))for r in manifest['registration']);assert center_error<=.51
    alpha_checks=[]
    for p in profiles:
        palette={tuple(bytes.fromhex(x))for x in(ALLY if p['side']=='ally'else ENEMY)}
        for f,path in p['newFrames'].items():
            im=Image.open(ROOT/path).convert('RGBA');assert set(im.getchannel('A').getdata())<={0,255};assert {c[:3]for c in im.getdata()if c[3]}<=palette
            components=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len([c for c in components if len(c)>12])==1,(p['id'],f,'detached substantial part',[len(c)for c in components])
            alpha_checks.append({'profile':p['id'],'frame':f,'binary_alpha':True,'substantial_connected_components':1})
    for side in['ally','enemy']:
        for i in[2,3]:
            right=Image.open(OUT/f'{side}/tactical-walk/frame-{i:03}.png').convert('RGBA');left=Image.open(OUT/f'{side}/tactical-walk/frame-{i+4:03}.png').convert('RGBA');assert left.tobytes()==right.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
        for f in[16,29,30,32]:
            a=Image.open(ROOT/'source-input/original-motion/class-2.png').convert('RGBA');e=Image.open(ROOT/'source-input/enemy-motion/class-2-enemy.png').convert('RGBA');w,h=80,64
            ac=a.crop((f%16*w,f//16*h,f%16*w+w,f//16*h+h)).getchannel('A');ec=e.crop((f%16*w,f//16*h,f%16*w+w,f//16*h+h)).getchannel('A');shifted=Image.new('L',(80,64));shifted.paste(ac,(-16,0))
            # Native throw/release has one faction-palette-dependent face pixel.
            # All other alpha pixels prove the exact background-slot translation.
            different={(x,y)for y in range(64)for x in range(80)if shifted.getpixel((x,y))!=ec.getpixel((x,y))}
            assert different==({(24,45)}if f in[30,32]else set()),(f,different)
    reports=[]
    for a in actions:reports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
    print('All40 stills, original programs, palette and anchor checks passed',flush=True)
    for a in actions:
        if not(a['kind']=='map_walk'or a['key']in['idle-cycle','idle','original_class_2_normal','original_class_2_enemy_normal','class_2_ally_javelin','class_2_enemy_javelin']):continue
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);reports.append(export_one(d,a,args));print('Exported '+a['id'],flush=True)
        if a['key']in['original_class_2_normal','original_class_2_enemy_normal','class_2_ally_javelin','class_2_enemy_javelin']:
            args.close=True;reports.append(export_one(d,a,args))
        if a['key']in['original_class_2_normal','original_class_2_enemy_normal']:
            for f in[0,5,7,11,12]:
                tick=next(n for n,r in enumerate(a['frames'])if r['frame']==f);render_frame(d,lookup[a['profile']],a,tick,4,False,True).save(OUT/f'{lookup[a["profile"]]["side"]}-normal-pose-{f:02}.png',optimize=True)
    videos=[]
    for rec in reports:
        if not rec.get('video'):continue
        q=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/rec['video'])],capture_output=True,text=True,check=True);s=json.loads(q.stdout)['streams'][0];assert int(s['nb_read_frames'])==rec['frames']and abs(float(s['duration'])-rec['frames']/rec['fps'])<1/rec['fps'];videos.append({'path':rec['video'],'decoded':s})
    for a in actions:
        for field,directory,suffix,extension in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{directory}/{a["id"]}{suffix}.{extension}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':40,'videos':videos,'exports':reports},ensure_ascii=False,indent=2)+'\n')
    (OUT/'card-action-map.json').write_text(json.dumps({'definitions_checked':['docs2/完整游戏设定.md:90','docs2/完整游戏设定.md:175','docs2/完整游戏设定.md:643','source-input/original-motion/full-original-motion.json','source-input/enemy-motion/full-enemy-motion.json'],'rows':cards,'guard_reactions':'Existing idle/miss/hit/exit reactions only; no new guard card or mitigation effect.','runtime_game_unchanged':True},ensure_ascii=False,indent=2)+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','profiles':6,'actions':40,'gallery_profiles':len(d['profiles']),'gallery_actions':len(d['actions']),'all_resource_paths_ready':True,'native_attack_schedules':timing,'native_idle_ticks':[14,8,14,8],'native_walk_ticks_per_pose':16,'registration_no_clipping':True,'fixed_face_or_helmet_landmark_error_max_pixels':center_error,'binary_alpha_and_connected_parts':alpha_checks,'native_enemy_background_shift_proven':True,'left_right_exact_mirrors':True,'unrelated_action_digests_unchanged':len(unchanged),'matte_palette_colors_per_faction':14,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'Whole-pose dark/light boards and representative offline playback captures. Browser local file access previously denied; no alternate server/browser or foreground Godot window.'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','actions':40,'videos':len(videos),'unrelated_actions_unchanged':len(unchanged)}),flush=True)

if __name__=='__main__':main()
