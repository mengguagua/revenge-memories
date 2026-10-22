#!/usr/bin/env python3
"""Focused verification of only the corrected class22 map idle."""
import json,subprocess
from types import SimpleNamespace
from pathlib import Path
from PIL import Image
from build_gallery import ROOT,build,matched_export,relative
from export_knight_complete import export_one
from export_gallery import render_frame
from revise_bastion_guardian_idle import REV,OUT

def main():
    data=build();profiles=[p for p in data['profiles']if p.get('revision')==REV];actions=[a for a in data['actions']if a.get('revision')==REV]
    assert len(profiles)==2 and len(actions)==2 and all(a['ready']for a in actions)
    baseline=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text())
    old=baseline['digests'];new={a['id']:a['contentDigest']for a in data['actions']};changed={a['id']for a in actions}
    assert all(new[k]==v for k,v in old.items()if k not in changed)
    expected=[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
    records=[]
    for p,a in zip(profiles,actions):
        assert p['id']==a['profile'] and [r['frame']for r in a['frames']]==expected and len(a['frames'])==88
        assert all(r['offset']==[0,0]and not r['flip']for r in a['frames'])
        side=p['side'];m=json.loads((ROOT/p['mapping']).read_text())
        assert m['scenarios'][1]==baseline[side]['scenarios'][1]
        weapon=Image.open(OUT/f'{side}/shared-spear.png').convert('RGBA');assert weapon.size==(8,76)
        for phase,pos in enumerate(meta['shared_spear_positions']):
            im=Image.open(OUT/f'{side}/frame-{phase:03}.png').convert('RGBA');hand=Image.open(OUT/f'{side}/glove-occlusion-{phase:03}.png').convert('RGBA')
            assert im.size==(96,96) and set(im.getchannel('A').getdata())<={0,255}
            for y in range(weapon.height):
                for x in range(weapon.width):
                    wp=weapon.getpixel((x,y));point=(x+pos[0],y+pos[1])
                    if wp[3]and not hand.getpixel(point)[3]:assert im.getpixel(point)==wp
            # Tip and butt must remain visible, not hidden by legs or clipped.
            for y in [0,weapon.height-1]:
                assert any(weapon.getpixel((x,y))[3]and im.getpixel((x+pos[0],y+pos[1]))==weapon.getpixel((x,y))for x in range(weapon.width))
        assert (OUT/f'{side}/frame-000.png').read_bytes()==(OUT/f'{side}/frame-004.png').read_bytes()
        assert (OUT/f'{side}/frame-001.png').read_bytes()==(OUT/f'{side}/frame-003.png').read_bytes()==(OUT/f'{side}/frame-005.png').read_bytes()
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);result=export_one(data,a,args)
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/result['video'])],capture_output=True,text=True,check=True)
        video=json.loads(probe.stdout)['streams'][0];assert int(video['nb_read_frames'])==88;assert abs(float(video['duration'])-88/a['fps'])<1/a['fps']
        records.append({'side':side,'export':result,'decoded_video':video})
        for phase,tick in enumerate([0,14,22,36]):render_frame(data,p,a,tick,4,False,False).save(OUT/f'{side}-phase-{phase}.png',optimize=True)
        print(side+' idle: shared spear geometry, four stages, video decode passed',flush=True)
    # Refresh export links through exactly the builder's normal snapshot predicate.
    for a in actions:
        for field,directory,suffix,extension in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{directory}/{a["id"]}{suffix}.{extension}';a[field]=relative(path)if matched_export(path,a['contentDigest'])and a['ready']else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    maximum_error=max(max(abs(x-y)for x,y in zip(r['actual_landmark'],r['target_landmark']))for r in meta['registration'])
    assert maximum_error<=.51 and all(r['clipped_pixels']==0 for r in meta['registration'])
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':2,'other_action_digests_unchanged':len(old)-2,'frames_per_action':88,'timing':[14,8,14,8],'cycle':[0,1,2,1],'shared_complete_spear_size':[8,76],'rigid_weapon_no_scaling':True,'all_unoccluded_spear_pixels_identical_after_translation':True,'tip_and_butt_visible_every_phase':True,'body_registration_rounding_error_max':maximum_error,'walking_and_battle_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'dark/light3x pose boards and offline original/redraw playback frames; no browser or Godot window'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','videos':2,'records':records},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':2,'other_actions_unchanged':len(old)-2,'videos':2}),flush=True)

if __name__=='__main__':main()
