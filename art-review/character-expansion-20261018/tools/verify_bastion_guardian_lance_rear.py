#!/usr/bin/env python3
"""Targeted rear-shaft visibility, native timing and playback export checks."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,build,pack_frame,matched_export,relative
from export_knight_complete import export_one
from export_gallery import render_frame
from revise_cavalry_map import translate
from import_knight_redraw_v3 import parts
from revise_bastion_guardian_lance_rear import REV,OUT

def main():
    data=build();profiles={p['id']:p for p in data['profiles']};base=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text())
    actions=[a for a in data['actions']if a['profile'].startswith('professions-class-22-')and a['context']=='battle'and(a['kind']=='reaction'or a['key']in['original_class_22_normal','original_class_22_enemy_normal'])]
    assert len(actions)==10 and all(a['ready']for a in actions)
    ids={a['id']for a in actions};current={a['id']:a['contentDigest']for a in data['actions']};assert all(current[k]==v for k,v in base['digests'].items()if k not in ids)
    pose_checks={}
    for side in ['ally','enemy']:
        m=json.loads((ROOT/f'professions/class-22-{side}/battle/frame_mapping.json').read_text());oldmap=base[side]
        assert m['effect_overrides']==oldmap['effect_overrides'] and m['variant_keys']==oldmap['variant_keys']
        for f in ['25','27']:assert m['frame_mapping'][f]==oldmap['frame_mapping'][f]
        pose_checks[side]=[]
        for i in range(12):
            before=Image.open((ROOT/f'professions/class-22-{side}/battle'/oldmap['frame_mapping'][str(i)]).resolve()).convert('RGBA');after=Image.open(OUT/f'{side}/frame-{i:03}.png').convert('RGBA')
            assert after.size==(320,256)and set(after.getchannel('A').getdata())<={0,255}
            assert after.crop((190,128,225,162)).tobytes()==before.crop((190,128,225,162)).tobytes()
            assert all(after.getpixel((x,y))==before.getpixel((x,y))for y in range(200,256)for x in range(320)if before.getpixel((x,y))[3])
            connected=parts((x,y)for y in range(256)for x in range(320)if after.getpixel((x,y))[3]);assert len(connected)==1,(side,i,'detached weapon fragment')
            rec=meta['pose_repairs'][str(i)];assert rec['visible_butt_pixels']>=10 and rec['shared_asset_size']==[110,7]
            pose_checks[side].append({'source_pose':i,'visible_butt_pixels':rec['visible_butt_pixels'],'full_character_connected':True,'face_and_original_leg_pixels_unchanged':True})
        zero=Image.open(OUT/f'{side}/frame-000.png').convert('RGBA');expected=translate(zero,[-64,0])if side=='enemy'else zero
        for i in[13,24]:assert Image.open(OUT/f'{side}/frame-{i:03}.png').convert('RGBA').tobytes()==expected.tobytes()
    exports=[];videos=[];timing=[]
    for a in actions:
        p=profiles[a['profile']];side=p['side']
        if a['kind']=='attack':
            path=ROOT/f'source-input/{"original"if side=="ally"else"enemy"}-motion/full-{"original"if side=="ally"else"enemy"}-motion.json';v=json.loads(path.read_text())['variants'][a['key']]
            assert a['frames']==[pack_frame(r)for r in v['frames']]and len(a['frames'])==535 and a['contactTick']==245 and v['contact_count']==1
            timing.append({'side':side,'frames':535,'contact_tick':245,'contact_count':1,'native_rows_equal':True})
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);exports.append(export_one(data,a,args))
        if a['kind']=='attack':
            args.close=True;exports.append(export_one(data,a,args))
            for pose in[2,5,9,10,11]:
                tick=next(n for n,r in enumerate(a['frames'])if r['frame']==pose);render_frame(data,p,a,tick,4,False,True).save(OUT/f'{side}-pose-{pose:02}-playback.png',optimize=True)
        print(a['id']+': exported corrected rear shaft',flush=True)
    for r in exports:
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/r['video'])],capture_output=True,text=True,check=True)
        s=json.loads(probe.stdout)['streams'][0];assert int(s['nb_read_frames'])==r['frames'];assert abs(float(s['duration'])-r['frames']/r['fps'])<1/r['fps'];videos.append({'path':r['video'],'decoded':s})
    for a in actions:
        for field,directory,suffix,extension in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{directory}/{a["id"]}{suffix}.{extension}';a[field]=relative(path)if matched_export(path,a['contentDigest'])and a['ready']else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':10,'unrelated_action_digests_unchanged':len(base['digests'])-10,'ordinary_attack_timing':timing,'rear_shaft_pose_checks':pose_checks,'one_shared_rear_shaft_size':[110,7],'minimum_visible_butt_pixels':min(r['visible_butt_pixels']for r in meta['pose_repairs'].values()),'no_detached_old_handle_fragments':True,'javelin_unchanged':True,'map_actions_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'dark/light whole-pose boards and offline original/redraw normal attack playback; no browser or Godot window'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','videos':videos,'exports':exports},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':10,'unrelated_actions_unchanged':len(base['digests'])-10,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
