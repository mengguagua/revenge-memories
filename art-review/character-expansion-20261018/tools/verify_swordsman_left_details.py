#!/usr/bin/env python3
"""Targeted acceptance checks for the three requested left-walk corrections."""
import ast,json,subprocess
from collections import deque
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from revise_swordsman_left_details import OUT,OLD,HEAD,SHIELDS,FOOT,COLORS,ENEMY
from import_knight_redraw_v3 import parts

def rim_closed(shield):
    # Flood the non-ivory area from all image edges. The entire blue face
    # must be enclosed by ivory, including the previously missing right edge.
    w,h=shield.size;ivory=COLORS[2];blue=COLORS[1]
    seeds=[(x,y)for y in range(h)for x in range(w)if x in[0,w-1]or y in[0,h-1]];q=deque(seeds);seen=set(seeds)
    while q:
        x,y=q.popleft()
        for nx,ny in[(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0<=nx<w and 0<=ny<h and(nx,ny)not in seen and shield.getpixel((nx,ny))[:3]!=ivory:
                seen.add((nx,ny));q.append((nx,ny))
    face={(x,y)for y in range(h)for x in range(w)if shield.getpixel((x,y))[:3]==blue}
    assert face and not face.intersection(seen),'Ivory rim has an open side'
    for xy in[(12,4),(12,32),(3,18),(20,18)]:assert shield.getpixel(xy)[:3]==ivory

def inside(x,y,b):return b[0]<=x<b[2]and b[1]<=y<b[3]

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text())
    changed=[a for a in d['actions']if a['contentDigest']!=b['actions'][a['id']]['contentDigest']]
    wanted={f'professions-class-9-{s}-maps-tactical-walk--{k}'for s in['ally','enemy']for k in['walk-left','idle-left']}
    assert {a['id']for a in changed}==wanted and len(d['actions'])==len(b['actions'])==647
    assert not d['validation']['structuralIssues'];rim_closed(Image.open(OUT/'source/complete-shield.png').convert('RGBA'))
    checks=[]
    for side,palette in[('ally',COLORS),('enemy',ENEMY)]:
        frames=[]
        for i in[6,7]:
            path=OUT/side/f'walk-{i:02}.png';im=Image.open(path).convert('RGBA');old=Image.open(OLD/side/f'walk-{i:02}.png').convert('RGBA');assert im.size==old.size==(128,96)
            assert {p[:3]for p in im.getdata()if p[3]}==set(palette);assert set(im.getchannel('A').getdata())=={0,255}
            boxes=[HEAD,SHIELDS[i]]+([FOOT]if i==7 else[])
            for y in range(96):
                for x in range(128):
                    if not any(inside(x,y,box)for box in boxes):assert im.getpixel((x,y))==old.getpixel((x,y)),(side,i,'unexpected edit',x,y)
            for y in range(31,54):
                for x in range(64,71):assert im.getpixel((x,y))[:3]!=palette[3],(side,i,'skin behind ear',x,y)
            # The foreground ivory blade stays exact, independent of hair fixes.
            for y in range(30,62):
                for x in range(32,49):
                    if old.getpixel((x,y))[:3]==palette[2]:assert im.getpixel((x,y))==old.getpixel((x,y))
            cc=parts((x,y)for y in range(96)for x in range(128)if im.getpixel((x,y))[3]);assert len(cc)==1
            if i==7:
                runs=[]
                for x in range(128):
                    if im.getpixel((x,87))[3]:
                        if not runs or x>runs[-1][-1]+1:runs.append([])
                        runs[-1].append(x)
                assert len(runs)==2 and max(runs[0])<66 and min(runs[1])>=68,('two visible feet',runs)
                assert any(im.getpixel((x,y))[3]and not old.getpixel((x,y))[3]for y in range(84,90)for x in range(68,76))
            frames.append(im);checks.append({'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'changes_limited_to_requested_layers':True,'opaque_components':1,'rear_head_skin_absent':True})
        assert frames[0].crop((48,32,64,53)).tobytes()==frames[1].crop((48,32,64,53)).tobytes()
    profiles={p['id']:p for p in d['profiles']};exports=[];captures=[]
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
        p=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        row=json.loads(p.stdout)['streams'][0];assert int(row['nb_read_frames'])==e['frames'];assert abs(float(row['duration'])-e['frames']/e['fps'])<1/e['fps'];videos.append({'path':e['video'],'decoded':row})
    for a in changed:
        for field,kind,ext in[('video','videos','mp4'),('still','stills','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';assert matched_export(p,a['contentDigest']);a[field]=relative(p)
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    for f in['revise_swordsman_left_details.py','verify_swordsman_left_details.py']:ast.parse((ROOT/'tools'/f).read_text())
    result={'status':'passed','changed_actions':sorted(wanted),'unchanged_actions':643,'native_timing_unchanged':True,'ivory_shield_rim_closed_all_four_sides':True,'crossed_phase_two_visible_feet':True,'rear_head_skin_absent':True,'fixed_head_across_phases':True,'assets':checks,'exports':exports,'decoded_videos':videos,'phase_captures':captures,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','changed_actions':4,'unchanged_actions':643,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
