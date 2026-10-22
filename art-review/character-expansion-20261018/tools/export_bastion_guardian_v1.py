#!/usr/bin/env python3
"""Targeted offline playback exports and native-schedule verification for class22."""
import json, subprocess
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,build,pack_frame
from export_knight_complete import export_one
from import_bastion_guardian_v1 import REV, OUT, ALLY, ENEMY

def main():
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    profiles=[p for p in data['profiles']if p.get('revision')==REV];actions=[a for a in data['actions']if a.get('revision')==REV]
    assert len(profiles)==6 and len(actions)==40,(len(profiles),len(actions))
    assert all(a['ready']for a in actions)
    native={side:json.loads((ROOT/f'source-input/{"original"if side=="ally"else"enemy"}-motion/full-{"original"if side=="ally"else"enemy"}-motion.json').read_text())for side in ['ally','enemy']}
    plook={p['id']:p for p in profiles};timing=[]
    for a in actions:
        p=plook[a['profile']]
        if a['kind']=='attack':
            v=native[p['side']]['variants'][a['key']]
            assert a['frames']==[pack_frame(r)for r in v['frames']]
            assert a['contactTick']==v['contact_tick'] and a['fps']==v['native_fps']
            timing.append({'action':a['id'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'source_rows_equal':True,'contact_count':v['contact_count']})
        elif a['key']=='idle-cycle':
            expected=[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
            assert [r['frame']for r in a['frames']]==expected
        elif a['kind']=='map_walk':
            assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames'])
            order=[{'up':0,'right':2,'down':4,'left':6}[a['key'][5:]]+i for i in [0,1]]
            assert [r['frame']for r in a['frames']]==[i for _ in range(3)for i in order for _ in range(16)]
        assert not a.get('revisedFrames') and not a.get('reviewTailFrames')
    baseline=json.loads((OUT/'baseline.json').read_text());new={a['id']:a['contentDigest']for a in data['actions']}
    unrelated=[key for key in baseline['digests']if not key.startswith('professions-class-22-')]
    assert all(new[key]==baseline['digests'][key]for key in unrelated)
    registration=json.loads((OUT/'asset-manifest.json').read_text())
    assert all(r['clipped_pixels']==0 for r in registration['registration'])
    assert all(max(abs(a-b)for a,b in zip(r['actual_landmark'],r['target_landmark']))<=.51 for r in registration['registration'])
    for p in profiles:
        colors={tuple(bytes.fromhex(v))for v in (ALLY if p['side']=='ally'else ENEMY)}
        for path in p['newFrames'].values():
            im=Image.open(ROOT/path).convert('RGBA')
            assert set(im.getchannel('A').getdata())<={0,255}
            assert {v[:3]for v in im.getdata()if v[3]}<=colors
    reports=[]
    for a in actions:
        reports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
    print('Saved all40 still previews; native rows and untouched-action digests passed',flush=True)
    for a in actions:
        if not(a['kind']=='map_walk' or a['key']in['idle-cycle','idle','original_class_22_normal','original_class_22_enemy_normal','class_22_ally_javelin','class_22_enemy_javelin']):continue
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False)
        reports.append(export_one(data,a,args));print('Exported '+a['id'],flush=True)
        if a['key']in['original_class_22_normal','original_class_22_enemy_normal','class_22_ally_javelin','class_22_enemy_javelin']:
            args.close=True;reports.append(export_one(data,a,args))
    videos=[]
    for r in reports:
        if not r.get('video'):continue
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/r['video'])],capture_output=True,text=True,check=True)
        s=json.loads(probe.stdout)['streams'][0];assert int(s['nb_read_frames'])==r['frames'];assert abs(float(s['duration'])-r['frames']/r['fps'])<1/r['fps']
        videos.append({'path':r['video'],'frames':int(s['nb_read_frames']),'duration':float(s['duration']),'size':[s['width'],s['height']]})
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':40,'videos':videos,'exports':reports},ensure_ascii=False,indent=2)+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','profiles':len(profiles),'actions':len(actions),'total_gallery_profiles':len(data['profiles']),'total_gallery_actions':len(data['actions']),'all_paths_ready':True,'native_attack_schedules':timing,'native_idle_cycle_ticks':[14,8,14,8],'walk_ticks_per_pose':16,'whole_pose_registration_no_clipping':True,'registration_rounding_error_max':max(max(abs(a-b)for a,b in zip(r['actual_landmark'],r['target_landmark']))for r in registration['registration']),'unrelated_action_digests_unchanged':len(unrelated),'matte_palette_colors_per_faction':14,'binary_clean_alpha':True,'runtime_integrated':False,'user_visual_acceptance':'pending','browser_check':'not performed; local file URL denied, no workaround used','visual_check':'offline gallery renderer, dark/light pose boards and key stages'},ensure_ascii=False,indent=2)+'\n')
    build();print(json.dumps({'status':'passed','stills':40,'videos':len(videos),'unrelated_actions_unchanged':len(unrelated)}),flush=True)

if __name__=='__main__':main()
