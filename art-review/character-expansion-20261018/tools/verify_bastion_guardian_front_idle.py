#!/usr/bin/env python3
"""Focused fixed-body/frame timing verification and two playback exports."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,build,relative,matched_export
from export_knight_complete import export_one
from export_gallery import render_frame
from revise_bastion_guardian_front_idle import REV,OUT,ARM_BOX,SPEAR_POSITIONS

def main():
    data=build();profiles=[p for p in data['profiles']if p.get('revision')==REV];actions=[a for a in data['actions']if a.get('revision')==REV]
    assert len(profiles)==2 and len(actions)==2 and all(a['ready']for a in actions)
    baseline=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text())
    old=baseline['digests'];new={a['id']:a['contentDigest']for a in data['actions']};changed={a['id']for a in actions}
    assert all(new[k]==v for k,v in old.items()if k not in changed)
    expected=[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
    records=[];static_checks={};asset_checks=[]
    for p,a in zip(profiles,actions):
        assert p['id']==a['profile'] and [r['frame']for r in a['frames']]==expected and len(a['frames'])==88
        assert all(r['offset']==[0,0]and not r['flip']for r in a['frames'])
        side=p['side'];m=json.loads((ROOT/p['mapping']).read_text());assert m['scenarios'][1]==baseline[side]['scenarios'][1]
        weapon=Image.open(OUT/f'{side}/shared-spear.png').convert('RGBA');base=Image.open(OUT/f'{side}/shared-fixed-body.png').convert('RGBA')
        assert weapon.size==(8,76) and base.size==(96,96)
        protected=[(x,y)for y in range(96)for x in range(96)if base.getpixel((x,y))[3]and not(ARM_BOX[0]<=x<ARM_BOX[2]and ARM_BOX[1]<=y<ARM_BOX[3])]
        region_checks={name:list(box)for name,box in [('head_and_upper_body',(28,0,96,34)),('torso_and_full_shield',(40,34,96,58)),('legs_and_feet',(26,57,96,96))]}
        for phase,pos in enumerate(SPEAR_POSITIONS):
            path=OUT/f'{side}/frame-{phase:03}.png';im=Image.open(path).convert('RGBA');hand=Image.open(OUT/f'{side}/hand-occlusion-{phase:03}.png').convert('RGBA')
            assert set(im.getchannel('A').getdata())<={0,255}
            assert all(im.getpixel(point)==base.getpixel(point)for point in protected)
            for box in region_checks.values():assert im.crop(box).tobytes()==base.crop(box).tobytes()
            for y in range(weapon.height):
                for x in range(weapon.width):
                    wp=weapon.getpixel((x,y));point=(x+pos[0],y+pos[1])
                    if wp[3]and not hand.getpixel(point)[3]:assert im.getpixel(point)==wp
            for y in [0,weapon.height-1]:assert any(weapon.getpixel((x,y))[3]and im.getpixel((x+pos[0],y+pos[1]))==weapon.getpixel((x,y))for x in range(weapon.width))
            asset_checks.append({'path':path.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':path.stat().st_size,'colors':len({q[:3]for q in im.getdata()if q[3]})})
        static_checks[side]={'protected_pixels':len(protected),'all_protected_pixels_identical_to_shared_body':True,'fixed_regions':region_checks,'all_fixed_region_rgba_identical':True,'body_offsets':[[0,0],[0,0],[0,0]]}
        assert (OUT/f'{side}/frame-000.png').read_bytes()==(OUT/f'{side}/frame-004.png').read_bytes()
        assert (OUT/f'{side}/frame-001.png').read_bytes()==(OUT/f'{side}/frame-003.png').read_bytes()==(OUT/f'{side}/frame-005.png').read_bytes()
        result=export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False))
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/result['video'])],capture_output=True,text=True,check=True)
        video=json.loads(probe.stdout)['streams'][0];assert int(video['nb_read_frames'])==88;assert abs(float(video['duration'])-88/a['fps'])<1/a['fps']
        records.append({'side':side,'export':result,'decoded_video':video})
        for phase,tick in enumerate([0,14,22,36]):render_frame(data,p,a,tick,4,False,False).save(OUT/f'{side}-phase-{phase}.png',optimize=True)
        print(side+' idle: fixed head/torso/shield/legs pixel checks and88-frame decode passed',flush=True)
    for a in actions:
        for field,directory,suffix,extension in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{directory}/{a["id"]}{suffix}.{extension}';a[field]=relative(path)if matched_export(path,a['contentDigest'])and a['ready']else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':2,'other_action_digests_unchanged':len(old)-2,'static_body_pixel_checks':static_checks,'frames_per_action':88,'timing':[14,8,14,8],'cycle':[0,1,2,1],'shared_complete_spear_size':[8,76],'rigid_weapon_no_scaling':True,'all_unoccluded_weapon_pixels_identical':True,'tip_and_butt_visible_every_phase':True,'walking_and_battle_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','asset_checks':asset_checks,'visual_check':'dark/light3x pose boards and offline original/redraw playback frames; no browser or Godot window'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','videos':2,'records':records},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':2,'other_actions_unchanged':len(old)-2,'videos':2}),flush=True)

if __name__=='__main__':main()
