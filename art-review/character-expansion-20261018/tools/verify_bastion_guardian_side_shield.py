#!/usr/bin/env python3
"""Check attached shield rig, fixed center, exact mirrors and original side cycles."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,build,matched_export,relative
from export_knight_complete import export_one
from export_gallery import render_frame
from revise_bastion_guardian_side_shield import REV,OUT,PIVOT,ANGLES
from import_knight_redraw_v3 import parts

def connected(im):
    return len(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]))

def main():
    data=build();profiles={p['id']:p for p in data['profiles']}
    actions=[a for a in data['actions']if a['profile'].startswith('professions-class-22-')and a['context']=='tactical-walk'and a['key']in['walk-right','walk-left','idle-right','idle-left']]
    assert len(actions)==8 and all(a['ready']for a in actions)
    baseline=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());changed={a['id']for a in actions}
    new={a['id']:a['contentDigest']for a in data['actions']};assert all(new[k]==v for k,v in baseline['digests'].items()if k not in changed)
    rigs={}
    for side in ['ally','enemy']:
        mapping=json.loads((ROOT/f'professions/class-22-{side}/maps/frame_mapping.json').read_text());assert mapping['scenarios'][0]==baseline[side]['scenarios'][0]
        old=baseline[side]['scenarios'][1];walk=mapping['scenarios'][1]
        assert walk['timing']==old['timing'] and walk['directions']==old['directions']
        for i in [0,1,4,5]:assert walk['frame_mapping'][i]==old['frame_mapping'][i]
        core=Image.open(OUT/f'{side}/shared-upper-body.png').convert('RGBA');assembly=Image.open(OUT/f'{side}/shared-arm-shield.png').convert('RGBA')
        assert connected(assembly)==1
        for i,angle in enumerate(ANGLES):
            layer=Image.open(OUT/f'{side}/arm-shield-{i}.png').convert('RGBA');assert layer.tobytes()==assembly.rotate(angle,resample=Image.Resampling.NEAREST,center=tuple(PIVOT),expand=False).tobytes();assert connected(layer)==1
            frame=Image.open(OUT/f'{side}/frame-{i+2:03}.png').convert('RGBA');mirror=Image.open(OUT/f'{side}/frame-{i+6:03}.png').convert('RGBA')
            assert frame.size==(128,96) and set(frame.getchannel('A').getdata())<={0,255}
            assert frame.crop((40,24,94,46)).tobytes()==core.crop((40,24,94,46)).tobytes()
            assert mirror.tobytes()==frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes();assert connected(frame)==1
            box=layer.getbbox();assert box[0]>0 and box[1]>0 and box[2]<128 and box[3]<96
        rigs[side]={'shoulder_pivot':PIVOT,'arm_shield_use_identical_shared_transform':True,'angles':ANGLES,'connected_layer_each_phase':True,'fixed_head_region_rgba_identical':True,'left_right_exact_mirrors':True,'full_character_connected_no_detached_shield':True}
    exports=[];videos=[]
    for a in actions:
        direction='right'if a['key'].endswith('right')else'left';order=[2,3]if direction=='right'else[6,7]
        expected=[i for _ in range(3)for i in order for _ in range(16)]if a['kind']=='map_walk'else[order[0]]*32
        assert [r['frame']for r in a['frames']]==expected
        assert all(r['offset']==[0,0]and not r['flip']for r in a['frames'])
        result=export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=a['kind']!='map_walk'));exports.append(result)
        if a['kind']=='map_walk':
            probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/result['video'])],capture_output=True,text=True,check=True)
            video=json.loads(probe.stdout)['streams'][0];assert int(video['nb_read_frames'])==96;assert abs(float(video['duration'])-96/a['fps'])<1/a['fps'];videos.append({'action':a['id'],'path':result['video'],'decoded':video})
            p=profiles[a['profile']]
            for phase,tick in enumerate([0,16]):render_frame(data,p,a,tick,4,False,False).save(OUT/f'{p["side"]}-{direction}-phase-{phase}.png',optimize=True)
            print(a['id']+': same arm/shield rig, original16-tick phases and96-frame decode passed',flush=True)
        for field,directory,suffix,extension in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{directory}/{a["id"]}{suffix}.{extension}';a[field]=relative(path)if matched_export(path,a['contentDigest'])and a['ready']else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':8,'other_action_digests_unchanged':len(baseline['digests'])-8,'rig_checks':rigs,'walk_frames':96,'ticks_per_phase':16,'accepted_idle_and_up_down_unchanged':True,'battle_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'dark/light pose boards and offline playback frames, no browser or Godot window'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':8,'videos':videos,'exports':exports},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':8,'unrelated_actions_unchanged':len(baseline['digests'])-8,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
