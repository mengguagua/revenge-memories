#!/usr/bin/env python3
"""Small, targeted checks and playback export for the left-facing head fix."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageChops
from build_gallery import ROOT,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from revise_swordsman_left_profile import OUT,OLD,BOX,COLORS,ENEMY

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text())
    changed=[a for a in d['actions']if a['contentDigest']!=b['actions'][a['id']]['contentDigest']]
    wanted={f'professions-class-9-{side}-maps-tactical-walk--{key}'for side in['ally','enemy']for key in['walk-left','idle-left']}
    assert {a['id']for a in changed}==wanted
    assert len(d['actions'])==len(b['actions'])==647 and not d['validation']['structuralIssues']
    profiles={p['id']:p for p in d['profiles']};checks=[]
    for side,palette in[('ally',COLORS),('enemy',ENEMY)]:
        frames=[]
        for i in[6,7]:
            path=OUT/side/f'walk-{i:02}.png';im=Image.open(path).convert('RGBA');old=Image.open(OLD/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')
            assert im.size==old.size==(128,96)
            assert {p[:3]for p in im.getdata()if p[3]}==set(palette)
            assert set(im.getchannel('A').getdata())=={0,255}
            assert path.stat().st_size<50000
            before=old.copy();after=im.copy();before.paste((0,0,0,0),BOX);after.paste((0,0,0,0),BOX)
            assert before.tobytes()==after.tobytes()
            frames.append(im);checks.append({'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'outside_head_box_identical':True,'existing_four_colors':True})
        assert frames[0].crop((48,32,64,53)).tobytes()==frames[1].crop((48,32,64,53)).tobytes()
    exports=[];captures=[]
    for a in changed:
        old=b['actions'][a['id']]
        for key in['frames','fps','origin','duration','contactTick']:assert a[key]==old[key]
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']=='walk-left':
            for tick in[0,16]:
                p=OUT/f'{profiles[a["profile"]]["side"]}-left-tick-{tick:02}.png';render_frame(d,profiles[a['profile']],a,tick,8,True).save(p,optimize=True);captures.append(relative(p))
        print('Exported '+a['id'],flush=True)
    videos=[]
    for e in exports:
        result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        row=json.loads(result.stdout)['streams'][0];assert int(row['nb_read_frames'])==e['frames'];assert abs(float(row['duration'])-e['frames']/e['fps'])<1/e['fps'];videos.append({'path':e['video'],'decoded':row})
    for a in changed:
        for field,kind,ext in[('video','videos','mp4'),('still','stills','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';assert matched_export(p,a['contentDigest']);a[field]=relative(p)
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    for f in['revise_swordsman_left_profile.py','verify_swordsman_left_profile.py']:ast.parse((ROOT/'tools'/f).read_text())
    result={'status':'passed','changed_actions':sorted(wanted),'unchanged_actions':643,'native_timing_unchanged':True,'body_sword_shield_legs_unchanged_outside_head':True,'same_head_across_phases':True,'assets':checks,'exports':exports,'decoded_videos':videos,'phase_captures':captures,'visual_head_direction':'Left-facing profile; single eye, nose points image-left, ear at rear/right. Checked light and dark pose boards plus offline original/new capture.','runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','changed_actions':4,'unchanged_actions':643,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
