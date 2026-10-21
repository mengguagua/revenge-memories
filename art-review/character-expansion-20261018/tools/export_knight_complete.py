#!/usr/bin/env python3
"""Offline preview exports for the new class-4 profiles; never display in chat."""
import json
from types import SimpleNamespace
import subprocess
from build_gallery import ROOT
from export_gallery import export
from PIL import Image

OUT=ROOT/'knight-complete-v1-20261021'

def export_one(data,action,args):
    record=export(data,action,args)
    if record.get('skipped_unchanged'):
        suffix='--close' if args.close else ''
        stem=action['id']+suffix
        still='demos/stills/'+stem+'.png'
        record.update(still=still,video=None if args.stills_only else 'demos/videos/'+stem+'.mp4',
            frames=len(action['frames']),fps=action['fps'],expected_duration=action['duration'],
            still_bytes=(ROOT/still).stat().st_size,dimensions=list(Image.open(ROOT/still).size))
        if record['video']:record['video_bytes']=(ROOT/record['video']).stat().st_size
    return record

def main():
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    actions=[a for a in data['actions'] if a['profile'].startswith('professions-class-4-')]
    assert len(actions)==40 and all(a['ready'] for a in actions)
    reports=[]
    for action in actions:
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=True)
        reports.append(export_one(data,action,args))
    print('Saved still previews for all40 new actions',flush=True)
    for action in actions:
        video=action['kind'] in ['map_walk'] or action['key'] in ['idle-cycle','idle','original_class_4_normal','original_class_4_enemy_normal','class_4_ally_javelin','class_4_enemy_javelin']
        if not video:continue
        args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False)
        reports.append(export_one(data,action,args));print(action['id'],flush=True)
        if action['key'] in ['original_class_4_normal','original_class_4_enemy_normal']:
            args.close=True;reports.append(export_one(data,action,args));print(action['id']+' close',flush=True)
    checked=[]
    for r in reports:
        if not r.get('video'):continue
        path=ROOT/r['video']
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0',
            '-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],capture_output=True,text=True,check=True)
        s=json.loads(probe.stdout)['streams'][0]
        assert int(s['nb_read_frames'])==r['frames']
        assert abs(float(s['duration'])-r['frames']/r['fps'])<1/r['fps']
        checked.append({'path':r['video'],'decoded_frames':int(s['nb_read_frames']),'duration':float(s['duration']),'dimensions':[s['width'],s['height']]})
    # The stills are pixel-exact inspection exports; only lossless optimization.
    large=[ROOT/r['still'] for r in reports if r.get('still') and (ROOT/r['still']).stat().st_size>200000]
    if large:subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',*map(str,set(large))],check=True)
    for r in reports:
        if r.get('still'):r['still_bytes']=(ROOT/r['still']).stat().st_size
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':40,'videos':len(checked),
        'exports':reports,'decoded_video_checks':checked,'user_visual_acceptance':'pending',
        'presentation':'No chat images or tool previews. Saved locally for gallery acceptance.'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'stills':40,'videos':len(checked),'decoded_video_checks':'passed'}),flush=True)

if __name__=='__main__':main()
