#!/usr/bin/env python3
"""Check weapon-only scope and export the affected battle previews."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageChops
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame
from export_knight_complete import export_one
from patch_sage_ruby_staff import REV,OUT,write
from import_knight_redraw_v3 import parts

def verify(export=False):
    baseline=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text())
    before={a['id']:a for a in baseline['gallery']['actions']};now={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};p=pp['professions-class-19-ally-battle'];actions=[a for a in now.values() if a['profile']==p['id']]
    assert len(actions)==88 and len(now)==len(before)==872 and len(pp)==100
    changed={k for k,a in now.items() if a['contentDigest']!=before[k]['contentDigest']}
    assert changed=={a['id'] for a in actions} and all(a['ready'] for a in actions) and not d['validation']['structuralIssues']
    for k,a in now.items():
        for field in ['frames','fps','origin','contactTick','duration']:assert a.get(field)==before[k].get(field),(k,field)
    assert d['effects']==baseline['gallery']['effects']
    assert file_hash(ROOT/'professions/class-19-ally/maps/frame_mapping.json')==baseline['map_mapping_sha256']
    reg=json.loads((OUT/'registration.json').read_text());mask=Image.open(OUT/'old-staff-mask.png').convert('L');layer=Image.open(OUT/'staff-layer.png').convert('RGBA');allowed=ImageChops.lighter(mask,layer.getchannel('A'));outside=ImageChops.invert(allowed);checks=[];first=None
    assert reg['placement']['clipped_pixels']==0 and len(p['newFrames'])==22
    for key,path in p['newFrames'].items():
        im=Image.open(ROOT/path).convert('RGBA');old=Image.open((ROOT/'professions/class-19-ally/battle'/baseline['battle']['frame_mapping'][key]).resolve()).convert('RGBA')
        assert im.size==(320,256) and set(im.getchannel('A').getdata())=={0,255}
        diff=ImageChops.difference(im,old)
        for channel in diff.split():assert not ImageChops.multiply(channel,outside).getbbox(),(key,'non-weapon pixels changed')
        for x,y in reg['original_hand_pixels'][key]:assert im.getpixel((x,y))==old.getpixel((x,y)),(key,'hand occlusion')
        fixed=im.crop((209,79,267,256)).tobytes()
        if first is None:first=fixed
        else:assert first==fixed,(key,'staff moves relative to hand')
        components=parts((x,y) for y in range(256) for x in range(320) if im.getpixel((x,y))[3]);assert len(components)==1,(key,'detached parts',list(map(len,components)))
        checks.append({'path':path,'size':list(im.size),'bytes':(ROOT/path).stat().st_size,'connected_components':1,'nonweapon_pixels_exact':True,'hand_pixels_preserved':len(reg['original_hand_pixels'][key])})
    for a in json.loads((OUT/'asset-manifest.json').read_text())['assets']:assert file_hash(ROOT/a['path'])==a['sha256'] and (ROOT/a['path']).stat().st_size==a['bytes']
    for name in ['patch_sage_ruby_staff.py','verify_sage_ruby_staff.py']:ast.parse((ROOT/'tools'/name).read_text())
    report={'status':'assets_passed','revision':REV,'changed_actions':len(changed),'unrelated_actions_unchanged':len(now)-len(changed),'battle_pose_sprites':22,'native_frames_fps_origins_contacts_exact':True,'all_spell_effects_unchanged':True,'map_mapping_and_art_unchanged':True,'nonweapon_pixels_exact':True,'original_grip_occlusion_preserved':True,'staff_fixed_all_22_poses':True,'asset_checks':checks,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','changed':88,'unchanged':784}),flush=True)
    if not export:return
    exports=[];captures=[]
    for a in actions:
        canonical=a['kind']!='attack' or not any(w in a['key'] for w in ['vs_heavy','far_'])
        if not canonical:continue
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key'] in ['class_19_ally_item_23','class_19_ally_item_40','class_19_ally_item_42']:
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
            for tick in [0,min(86,len(a['frames'])-1),a['contactTick']]:
                for light in [False,True]:
                    path=OUT/f'{a["key"]}-{tick:03}-{"light" if light else "dark"}.png';render_frame(d,p,a,tick,5,light,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['key'],flush=True)
    decoded=[]
    for e in exports:
        info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(info['nb_read_frames'])==e['frames'] and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path) if matched_export(path,a['contentDigest']) else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','changed':88,'unchanged':784,'videos':len(decoded)}),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
